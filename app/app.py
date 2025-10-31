import reflex as rx
from app.states.settings_state import SettingsState
from app.states.editor_state import EditorState
from app.states.file_browser_state import FileBrowserState
from app.states.hotkey_state import HotkeyState
from app.states.project_state import ProjectState
from app.components.chat import chat_interface
from app.components.settings import settings_modal
from app.components.file_browser import file_browser
from app.components.editor import editor_with_tabs
from app.components.context_panel import context_panel
from app.components.project_manager import project_manager_modal


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.header(
                rx.el.div(
                    rx.el.h1("Code Assist", class_name="text-xl font-bold"),
                    rx.el.p(
                        ProjectState.current_project_name,
                        class_name="text-sm text-gray-500 ml-2",
                    ),
                    class_name="flex items-center",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("folder_git_2", class_name="h-5 w-5"),
                        "Projects",
                        on_click=ProjectState.toggle_project_manager,
                        class_name="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md hover:bg-gray-200",
                    ),
                    rx.el.button(
                        rx.icon("settings", class_name="h-5 w-5"),
                        on_click=SettingsState.toggle_settings,
                        class_name="p-2 rounded-md hover:bg-gray-200",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="flex items-center justify-between p-4 border-b",
            ),
            rx.el.div(
                file_browser(),
                editor_with_tabs(),
                rx.el.div(
                    chat_interface(),
                    class_name="w-1/3 flex flex-col h-full bg-white border-l shrink-0",
                ),
                class_name="flex flex-1 overflow-hidden",
            ),
            class_name="flex flex-col h-screen w-screen bg-gray-100",
        ),
        settings_modal(),
        project_manager_modal(),
        rx.window_event_listener(on_key_down=HotkeyState.handle_hotkey),
        class_name="font-['Inter'] bg-white",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, on_load=[EditorState.on_load, ProjectState.load_projects])