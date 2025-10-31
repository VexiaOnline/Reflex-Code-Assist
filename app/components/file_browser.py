import reflex as rx
from app.states.editor_state import EditorState
from app.states.file_browser_state import FileBrowserState, file_item_view
from app.components.context_panel import context_panel


def file_browser() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2("Files", class_name="text-xl font-bold p-4 border-b"),
                class_name="sticky top-0 bg-gray-50 z-10",
            ),
            rx.el.div(
                rx.cond(
                    FileBrowserState.file_list.length() > 0,
                    rx.foreach(FileBrowserState.file_list, file_item_view),
                    rx.el.div(
                        "No project selected. Create or select a project to begin.",
                        class_name="p-4 text-sm text-gray-500",
                    ),
                ),
                class_name="p-2 overflow-y-auto",
            ),
            class_name="h-1/2 flex-1 flex flex-col",
        ),
        context_panel(),
        class_name="w-64 bg-gray-50 border-r h-full flex flex-col",
    )