import reflex as rx
from reflex_monaco.monaco import MonacoEditor
from app.states.editor_state import EditorState
from app.states.chat_state import ChatState


def file_tab(path: str, index: int) -> rx.Component:
    is_active = EditorState.active_tab_index == index
    has_unsaved = EditorState.unsaved_files.contains(path)
    return rx.el.div(
        rx.el.span(path.split("/")[-1]),
        rx.el.span(" ", rx.cond(has_unsaved, "●", ""), class_name="text-blue-500 ml-1"),
        rx.el.button(
            rx.icon("x", class_name="h-3 w-3"),
            on_click=lambda: EditorState.close_tab(index),
            class_name="ml-2 p-0.5 rounded hover:bg-gray-300",
        ),
        on_click=lambda: EditorState.switch_tab(index),
        class_name=rx.cond(
            is_active,
            "flex items-center px-3 py-2 text-sm bg-white border-t-2 border-blue-500 cursor-pointer",
            "flex items-center px-3 py-2 text-sm text-gray-600 bg-gray-100 border-b cursor-pointer hover:bg-gray-200",
        ),
    )


def quick_action_dropdown() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.el.option("Quick Actions...", value="", disabled=True),
            rx.foreach(
                ChatState.quick_actions,
                lambda action, i: rx.el.option(action["name"], value=i.to(str)),
            ),
            on_change=lambda index: ChatState.execute_quick_action(index.to(int)),
            value="",
            class_name="text-sm rounded-md border-gray-300",
        ),
        class_name="ml-auto",
    )


def editor_with_tabs() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.foreach(EditorState.open_tabs, file_tab),
            class_name="flex border-b bg-gray-50",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    "Save (Ctrl+S)",
                    on_click=EditorState.save_file,
                    class_name="px-3 py-1 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 disabled:opacity-50",
                    disabled=~EditorState.is_file_open,
                ),
                quick_action_dropdown(),
                class_name="flex items-center p-2 border-b",
            ),
            rx.cond(
                EditorState.is_file_open,
                MonacoEditor.create(
                    value=EditorState.current_content,
                    language="python",
                    theme="vs",
                    options={"lineNumbers": "on", "minimap": {"enabled": True}},
                    on_change=EditorState.on_change.debounce(250),
                    height="calc(100vh - 8.5rem)",
                ),
                rx.el.div(
                    "Select a file or open a tab to start editing.",
                    class_name="flex items-center justify-center h-full text-gray-500",
                ),
            ),
        ),
        class_name="flex-1 bg-white h-full flex flex-col",
    )