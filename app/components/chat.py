import reflex as rx
from reflex_monaco.monaco import MonacoEditor
from app.states.chat_state import ChatState
from app.states.generation_state import GenerationState, CodeBlock


def generation_view(generation: dict, index: int) -> rx.Component:
    content = generation["content"]
    return rx.el.div(
        rx.cond(
            generation["type"] == "explanation",
            rx.el.p(content, class_name="text-sm whitespace-pre-wrap"),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        generation["file_path"],
                        class_name="text-xs text-gray-500 font-mono",
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("check_check", class_name="h-4 w-4"),
                            "Apply",
                            on_click=lambda: GenerationState.apply_code(index),
                            class_name="flex items-center gap-1 px-2 py-1 text-xs bg-green-100 text-green-700 rounded-md hover:bg-green-200",
                        ),
                        rx.el.button(
                            rx.icon("circle_x", class_name="h-4 w-4"),
                            "Reject",
                            on_click=lambda: GenerationState.reject_code(index),
                            class_name="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    class_name="flex items-center justify-between p-2 bg-gray-50 border-b",
                ),
                MonacoEditor.create(
                    value=content.to(CodeBlock)["code"],
                    language=content.to(CodeBlock)["language"],
                    theme="vs-dark",
                    height="250px",
                    options={"readOnly": True, "minimap": {"enabled": False}},
                ),
                class_name="border rounded-md overflow-hidden bg-gray-800",
            ),
        ),
        class_name="my-2",
    )


def message_card(message: dict) -> rx.Component:
    role = message["role"]
    generations = message["content"]
    is_streaming_msg = (
        (message["role"] == "assistant")
        & (generations.length() == 0)
        & ChatState.is_streaming
    )
    return rx.el.div(
        rx.el.div(
            rx.el.p(role.capitalize(), class_name="font-semibold mb-1"),
            rx.cond(
                is_streaming_msg,
                rx.el.p(
                    ChatState.streaming_content + "▍",
                    class_name="text-sm whitespace-pre-wrap",
                ),
                rx.foreach(
                    generations,
                    lambda gen, i: rx.fragment(generation_view(gen, i), key=f"gen-{i}"),
                ),
            ),
            class_name="p-3 rounded-lg",
        ),
        class_name=rx.cond(
            role == "user", "bg-blue-100 self-end", "bg-gray-100 self-start"
        )
        + " rounded-xl w-4/5",
    )


def chat_interface() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2("Chat", class_name="text-lg font-bold"),
            rx.el.div(
                rx.el.button(
                    rx.icon("trash-2", class_name="h-4 w-4"),
                    on_click=ChatState.clear_conversation,
                    class_name="p-2 rounded-md hover:bg-gray-200",
                ),
                rx.el.button(
                    rx.icon("save", class_name="h-4 w-4"),
                    on_click=ChatState.save_conversation,
                    class_name="p-2 rounded-md hover:bg-gray-200",
                ),
                rx.upload.root(
                    rx.el.button(
                        rx.icon("folder-open", class_name="h-4 w-4"),
                        class_name="p-2 rounded-md hover:bg-gray-200",
                    ),
                    on_drop=ChatState.load_conversation,
                    accept={"application/json": [".json"]},
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="flex items-center justify-between p-4 border-b sticky top-0 bg-white z-10",
        ),
        rx.auto_scroll(
            rx.foreach(ChatState.messages, message_card),
            class_name="flex-1 p-4 space-y-4 overflow-y-auto",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    id="chat-input",
                    name="chat_input",
                    placeholder="Type your message... (Ctrl+K)",
                    class_name="flex-1 p-2 border rounded-lg",
                    default_value="",
                ),
                rx.el.button(
                    rx.icon("send", class_name="h-5 w-5"),
                    type="submit",
                    class_name="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50",
                    disabled=ChatState.is_loading,
                ),
                class_name="flex items-center gap-2",
            ),
            on_submit=ChatState.send_message,
            reset_on_submit=True,
            class_name="p-4 border-t",
        ),
        class_name="flex flex-col h-full",
    )