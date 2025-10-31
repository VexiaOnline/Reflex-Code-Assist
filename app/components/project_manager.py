import reflex as rx
from app.states.project_state import ProjectState, Project


def project_item_view(project: Project) -> rx.Component:
    is_active = ProjectState.current_project_id == project["id"]
    return rx.el.div(
        rx.el.div(
            rx.el.p(project["name"], class_name="font-semibold"),
            rx.el.p(project["path"], class_name="text-sm text-gray-500 font-mono"),
            class_name="flex-1",
        ),
        rx.el.div(
            rx.el.button(
                "Switch to",
                on_click=lambda: ProjectState.switch_project(project["id"]),
                class_name="px-3 py-1 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600",
                disabled=is_active,
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-4 w-4"),
                on_click=lambda: ProjectState.delete_project(project["id"]),
                class_name="p-2 text-sm text-red-500 rounded-md hover:bg-red-100",
                disabled=is_active,
            ),
            class_name="flex items-center gap-2",
        ),
        class_name=rx.cond(
            is_active,
            "flex items-center justify-between p-3 rounded-lg bg-blue-50 border border-blue-200",
            "flex items-center justify-between p-3 rounded-lg hover:bg-gray-50",
        ),
    )


def new_project_form() -> rx.Component:
    return rx.el.form(
        rx.el.h3("Create New Project", class_name="text-lg font-semibold mb-4"),
        rx.el.div(
            rx.el.label("Project Name", class_name="font-medium text-sm"),
            rx.el.input(
                name="name",
                placeholder="My Reflex App",
                class_name="w-full p-2 border rounded-md mt-1",
            ),
            class_name="mb-4",
        ),
        rx.el.button(
            "Create Project",
            type="submit",
            class_name="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700",
        ),
        on_submit=ProjectState.create_project,
        reset_on_submit=True,
        class_name="p-4 border rounded-lg bg-gray-50 mt-6",
    )


def project_manager_modal() -> rx.Component:
    return rx.el.div(
        rx.cond(
            ProjectState.show_project_manager,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h3("Project Manager", class_name="text-xl font-bold"),
                        rx.el.button(
                            rx.icon("x", class_name="h-5 w-5"),
                            on_click=ProjectState.toggle_project_manager,
                            class_name="p-1 rounded-full hover:bg-gray-200",
                        ),
                        class_name="flex justify-between items-center pb-4 border-b mb-4",
                    ),
                    rx.el.div(
                        rx.el.h4("Projects", class_name="font-semibold mb-2"),
                        rx.el.div(
                            rx.foreach(ProjectState.projects, project_item_view),
                            class_name="space-y-2",
                        ),
                        class_name="max-h-[30vh] overflow-y-auto pr-2",
                    ),
                    new_project_form(),
                    rx.el.div(
                        rx.el.button(
                            "Close",
                            on_click=ProjectState.toggle_project_manager,
                            class_name="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300 mt-6",
                        ),
                        class_name="flex justify-end pt-4 border-t",
                    ),
                    class_name="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6",
                    on_click=rx.stop_propagation,
                ),
                class_name="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50",
                on_click=ProjectState.toggle_project_manager,
            ),
        )
    )