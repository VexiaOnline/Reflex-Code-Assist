import reflex as rx
from typing import TypedDict, Literal
import logging


class CodeBlock(TypedDict):
    language: str
    code: str


class Generation(TypedDict):
    type: Literal["explanation", "code"]
    content: str | CodeBlock
    file_path: str | None


class GenerationState(rx.State):
    """Manages the state for code generation, including previews and application."""

    generations: list[Generation] = []

    @rx.event
    async def apply_code(self, generation_index: int):
        """Applies a specific code generation to the corresponding file."""
        from app.states.chat_state import ChatState

        chat_state = await self.get_state(ChatState)
        assistant_messages = [
            m for m in chat_state.messages if m["role"] == "assistant"
        ]
        if not assistant_messages:
            yield rx.toast.error("No assistant message found to apply code from.")
            return
        last_message_generations = assistant_messages[-1]["content"]
        if generation_index >= len(last_message_generations):
            yield rx.toast.error("Invalid generation index.")
            return
        generation = last_message_generations[generation_index]
        file_path = generation.get("file_path")
        if not file_path or generation["type"] != "code":
            yield rx.toast.warning("No file path or code found for this generation.")
            return
        code_content = generation["content"]["code"]
        try:
            import os

            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(file_path, "w") as f:
                f.write(code_content)
            from app.states.editor_state import EditorState
            from app.states.context_state import ContextState

            yield EditorState.on_load
            yield ContextState.analyze_project
            yield rx.toast.success(f"Applied code to {file_path}")
            return
        except Exception as e:
            logging.exception(f"Error applying code to {file_path}: {e}")
            yield rx.toast.error(f"Failed to write to {file_path}")
            return

    @rx.event
    def reject_code(self, generation_index: int):
        """Rejects a specific code generation."""
        logging.info(f"Rejecting code for generation {generation_index}")
        return rx.toast.info("Code rejection logic not yet implemented.")