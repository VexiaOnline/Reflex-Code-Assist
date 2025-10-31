import reflex as rx
import httpx
import logging
import re
import os
import json
from datetime import datetime
from typing import TypedDict, Literal, Any
from app.states.settings_state import SettingsState
from app.states.context_state import ContextState
from app.states.editor_state import EditorState
from app.states.generation_state import Generation

SYSTEM_PROMPT = """You are CodeAssist, an expert Reflex developer. Your purpose is to help users build Reflex applications. 

**Response Guidelines**
1.  **Analyze User Requests**: Understand the user's goal. Ask for clarification if needed.
2.  **Provide Explanations First**: Always start with a clear, concise explanation of your plan. 
3.  **Generate Code**: After the explanation, provide the necessary code in markdown blocks with the correct language identifier (e.g., ).
4.  **Specify File Paths**: For each code block, specify the target file path using the format `File: app/path/to/file.py` on the line immediately preceding the code block. If it's a new file, use `File: app/path/to/new_file.py (new)`.
5.  **Follow Reflex Best Practices**: Ensure generated code adheres to the official Reflex documentation and style guides.
6.  **Be Helpful and Informative**: If you can't fulfill a request, explain why and offer alternatives.
"""


class Message(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: list[Generation]


class ChatState(rx.State):
    messages: list[Message] = []
    is_loading: bool = False
    quick_actions: list[dict[str, str]] = [
        {
            "name": "Explain this code",
            "prompt": "Explain the code in the current file.",
        },
        {
            "name": "Add docstrings",
            "prompt": "Add comprehensive docstrings to all functions and classes in the current file.",
        },
        {
            "name": "Refactor for clarity",
            "prompt": "Refactor the code in the current file to improve clarity and readability.",
        },
        {
            "name": "Find potential bugs",
            "prompt": "Analyze the current file for potential bugs or issues and suggest fixes.",
        },
    ]
    _all_docs: list[dict] = []
    _doc_embeddings = None
    _embedding_model = None

    def _load_rag_data(self):
        """Load RAG data and model if not already loaded."""
        if self._all_docs:
            return
        docs_path = "reflex_docs.json"
        if not os.path.exists(docs_path):
            logging.info("reflex_docs.json not found, RAG will be disabled.")
            return
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            logging.info("Loading RAG data from reflex_docs.json...")
            with open(docs_path, "r") as f:
                self._all_docs = json.load(f)
            embeddings = [doc["embedding"] for doc in self._all_docs]
            self._doc_embeddings = np.array(embeddings)
            model_name = "all-MiniLM-L6-v2"
            self._embedding_model = SentenceTransformer(model_name)
            logging.info(
                f"Loaded {len(self._all_docs)} doc chunks and '{model_name}' model for RAG."
            )
        except ImportError as e:
            logging.exception(f"Error importing RAG dependencies: {e}")
            logging.warning(
                "sentence-transformers or numpy not installed. RAG will be disabled. Run `pip install sentence-transformers numpy`"
            )
            self._all_docs = []
        except Exception as e:
            logging.exception(f"Failed to load RAG data: {e}")
            self._all_docs = []

    def _get_context_prompt(
        self, code_map, current_file, current_content, user_input
    ) -> str:
        """Constructs the context part of the prompt for the LLM."""
        prompt = """# Project Context

## Code Map
"""
        for file_summary in code_map:
            prompt += f"- {file_summary['path']}\n"
            for element in file_summary["elements"]:
                prompt += f"  - [{element['type']}] {element['name']} (line {element['line']})\n"
        prompt += """
"""
        if current_file:
            prompt += f"## Current Open File: {current_file}\n\n\n{current_content}\n\n"
        self._load_rag_data()
        if (
            self._all_docs
            and self._embedding_model is not None
            and (self._doc_embeddings is not None)
        ):
            try:
                import numpy as np

                query_embedding = self._embedding_model.encode(
                    user_input, convert_to_tensor=False
                )
                cos_sim = np.dot(self._doc_embeddings, query_embedding) / (
                    np.linalg.norm(self._doc_embeddings, axis=1)
                    * np.linalg.norm(query_embedding)
                )
                top_k_indices = np.argsort(cos_sim)[-5:][::-1]
                retrieved_chunks = [self._all_docs[i]["chunk"] for i in top_k_indices]
                if retrieved_chunks:
                    prompt += """## Retrieved Reflex Documentation (for context)

"""
                    for i, chunk in enumerate(retrieved_chunks):
                        prompt += f"--- Doc {i + 1} ---\n{chunk}\n\n"
                    prompt += """---

"""
            except Exception as e:
                logging.exception(f"RAG processing failed: {e}")
        prompt += """
Based on the context above, please respond to the following request.
"""
        return prompt

    def _parse_assistant_response(self, text: str) -> list[Generation]:
        """Parses the assistant's markdown response into a list of Generations."""
        generations = []
        pattern = "File:\\s*`?(.+?)(?:\\s*\\(new\\))?`?\\s*\\n(\\w+)?\\n([\\s\\S]*?)\\n"
        matches = list(re.finditer(pattern, text))
        last_index = 0
        for match in matches:
            explanation_text = text[last_index : match.start()].strip()
            if explanation_text:
                generations.append(
                    {
                        "type": "explanation",
                        "content": explanation_text,
                        "file_path": None,
                    }
                )
            file_path = match.group(1).strip()
            language = match.group(2) or ""
            code = match.group(3).strip()
            generations.append(
                {
                    "type": "code",
                    "content": {"language": language, "code": code},
                    "file_path": file_path,
                }
            )
            last_index = match.end()
        remaining_text = text[last_index:].strip()
        if remaining_text:
            generations.append(
                {"type": "explanation", "content": remaining_text, "file_path": None}
            )
        if not generations and text:
            return [{"type": "explanation", "content": text, "file_path": None}]
        return generations

    @rx.event
    async def send_message(self, form_data: dict):
        user_input = form_data.get("chat_input")
        if not user_input or not user_input.strip():
            return
        self.messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "explanation", "content": user_input, "file_path": None}
                ],
            }
        )
        self.is_loading = True
        yield
        try:
            settings = await self.get_state(SettingsState)
            context = await self.get_state(ContextState)
            editor = await self.get_state(EditorState)
            context_prompt = self._get_context_prompt(
                context.code_map,
                editor.current_file,
                editor.current_content,
                user_input,
            )
            full_prompt = (
                f"{SYSTEM_PROMPT}\n\n{context_prompt}\n\nUser Request: {user_input}"
            )
            api_url = f"{settings.endpoint_url}"
            if not api_url.endswith("/v1/completions"):
                if not api_url.endswith("/"):
                    api_url += "/"
                api_url += "v1/completions"
            payload = {
                "prompt": full_prompt,
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature,
                "stop": [
                    """
User Request:""",
                    "<|endoftext|>",
                ],
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                result = response.json()
                assistant_message = result["choices"][0]["text"]
                parsed_response = self._parse_assistant_response(assistant_message)
                self.messages.append({"role": "assistant", "content": parsed_response})
        except httpx.HTTPError as e:
            logging.exception(f"HTTP Error: {e}")
            error_content = f"Error connecting to LLM: {e}"
            self.messages.append(
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "explanation",
                            "content": error_content,
                            "file_path": None,
                        }
                    ],
                }
            )
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            self.messages.append(
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "explanation",
                            "content": "An unexpected error occurred.",
                            "file_path": None,
                        }
                    ],
                }
            )
        finally:
            self.is_loading = False
            yield

    @rx.event
    def execute_quick_action(self, index: int):
        action = self.quick_actions[index]
        yield ChatState.send_message({"chat_input": action["prompt"]})

    def _ensure_conversations_dir(self):
        dir_path = ".code_assist/conversations"
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @rx.event
    def save_conversation(self):
        dir_path = self._ensure_conversations_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"conversation_{timestamp}.json"
        file_path = os.path.join(dir_path, filename)
        try:
            with open(file_path, "w") as f:
                json.dump(self.messages, f, indent=2)
            return rx.toast.success(f"Conversation saved to {filename}")
        except Exception as e:
            logging.exception(f"Error saving conversation: {e}")
            return rx.toast.error("Failed to save conversation.")

    @rx.event
    async def load_conversation(self, files: list[rx.UploadFile]):
        try:
            if not files:
                return
            file = files[0]
            content = await file.read()
            self.messages = json.loads(content.decode("utf-8"))
            return rx.toast.success("Conversation loaded.")
        except Exception as e:
            logging.exception(f"Error loading conversation: {e}")
            return rx.toast.error("Failed to load conversation.")

    @rx.event
    def clear_conversation(self):
        self.messages = []
        return rx.toast.info("Conversation cleared.")