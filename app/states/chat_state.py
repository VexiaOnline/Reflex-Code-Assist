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
1.  **Structured Responses**: Structure your response into sections: `[THINKING]`, `[EXPLANATION]`, and `[CODE]`.
2.  **Thinking Block**: Use the `[THINKING]` block to outline your plan, analyze the request, and reason about the solution. This is for your internal monologue and should be concise. Wrap it in `[THINKING]...[/THINKING]`.
3.  **Explanation Block**: Use the `[EXPLANATION]` block for the user-facing explanation. This should be clear and directly address the user's request. Wrap it in `[EXPLANATION]...[/EXPLANATION]`.
4.  **Code Blocks**: Place all code snippets inside `[CODE]` blocks. Each code block must be preceded by a `File: path/to/file.py` line.
5.  **Example Response Structure**:

    [THINKING]
    The user wants to add a button. I need to define the button component and an event handler in the state.
    [/THINKING]

    [EXPLANATION]
    I will add a new button to your UI. When clicked, it will trigger an event to update the counter.
    [/EXPLANATION]

    [CODE]
    File: app/state.py

    class State(rx.State):
        count: int = 0

        def increment(self):
            self.count += 1

    [/CODE]

    [CODE]
    File: app/app.py

    def index():
        return rx.button(f"Click me: {State.count}", on_click=State.increment)

    [/CODE]

**Be Helpful and Informative**: If you can't fulfill a request, explain why and offer alternatives within an `[EXPLANATION]` block.
"""


class Message(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: list[Generation]


class ChatState(rx.State):
    messages: list[Message] = []
    is_loading: bool = False
    is_streaming: bool = False
    streaming_content: str = ""
    expanded_thinking_blocks: set[str] = set()
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
        docs_path = "rag/reflex_docs.json"
        if not os.path.exists(docs_path):
            logging.info("rag/reflex_docs.json not found, RAG will be disabled.")
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
        """Parses the assistant's structured response into a list of Generations."""
        generations = []
        section_pattern = "\\[(THINKING|EXPLANATION|CODE)\\]([\\s\\S]*?)(?=\\[(THINKING|EXPLANATION|CODE)\\]|$)"
        code_file_pattern = (
            "File:\\s*`?(.+?)(?:\\s*\\(new\\))?`?\\s*\\n(\\w+)?\\n([\\s\\S]*?)\\n"
        )
        sections = re.findall(section_pattern, text)
        if not sections:
            code_matches = list(re.finditer(code_file_pattern, text))
            last_index = 0
            for match in code_matches:
                explanation_text = text[last_index : match.start()].strip()
                if explanation_text:
                    generations.append(
                        {
                            "type": "explanation",
                            "content": explanation_text,
                            "file_path": None,
                        }
                    )
                file_path, language, code = match.groups()
                generations.append(
                    {
                        "type": "code",
                        "content": {"language": language or "", "code": code.strip()},
                        "file_path": file_path.strip(),
                    }
                )
                last_index = match.end()
            remaining_text = text[last_index:].strip()
            if remaining_text:
                generations.append(
                    {
                        "type": "explanation",
                        "content": remaining_text,
                        "file_path": None,
                    }
                )
            if not generations and text:
                return [{"type": "explanation", "content": text, "file_path": None}]
            return generations
        for section_type, section_content, _ in sections:
            section_content = section_content.strip()
            if section_type == "THINKING":
                generations.append(
                    {"type": "thinking", "content": section_content, "file_path": None}
                )
            elif section_type == "EXPLANATION":
                generations.append(
                    {
                        "type": "explanation",
                        "content": section_content,
                        "file_path": None,
                    }
                )
            elif section_type == "CODE":
                code_match = re.search(code_file_pattern, section_content)
                if code_match:
                    file_path, language, code = code_match.groups()
                    generations.append(
                        {
                            "type": "code",
                            "content": {
                                "language": language or "",
                                "code": code.strip(),
                            },
                            "file_path": file_path.strip(),
                        }
                    )
                else:
                    generations.append(
                        {
                            "type": "explanation",
                            "content": section_content,
                            "file_path": None,
                        }
                    )
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
        self.is_streaming = True
        self.messages.append({"role": "assistant", "content": []})
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
                "stream": True,
                "stop": [
                    """
User Request:""",
                    "<|endoftext|>",
                ],
            }
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", api_url, json=payload) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        if chunk.startswith("data: "):
                            data_str = chunk.replace("data: ", "").strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                self.streaming_content += data["choices"][0]["text"]
                                yield
                            except json.JSONDecodeError as e:
                                logging.exception(
                                    f"Could not decode streaming chunk: {data_str}: {e}"
                                )
                                continue
        except httpx.HTTPError as e:
            logging.exception(f"HTTP Error: {e}")
            self.streaming_content = f"Error connecting to LLM: {e}"
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            self.streaming_content = "An unexpected error occurred."
        finally:
            self.is_loading = False
            self.is_streaming = False
            if self.streaming_content:
                parsed_response = self._parse_assistant_response(self.streaming_content)
                self.messages[-1]["content"] = parsed_response
            self.streaming_content = ""
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
    def toggle_thinking_block(self, block_id: str):
        if block_id in self.expanded_thinking_blocks:
            self.expanded_thinking_blocks.remove(block_id)
        else:
            self.expanded_thinking_blocks.add(block_id)

    @rx.event
    def clear_conversation(self):
        self.messages = []
        self.expanded_thinking_blocks = set()
        return rx.toast.info("Conversation cleared.")