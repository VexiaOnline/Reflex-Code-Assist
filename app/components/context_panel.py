import reflex as rx
from app.states.context_state import ContextState


def code_element_view(element: dict) -> rx.Component:
    return rx.el.div(
        rx.el.span(f"[{element['type']}]", class_name="text-xs text-gray-500 mr-2"),
        rx.el.span(element["name"], class_name="text-sm font-mono"),
        rx.el.span(f":{element['line']}", class_name="text-xs text-gray-400 ml-1"),
        class_name="flex items-center",
    )


def file_summary_view(summary: dict) -> rx.Component:
    return rx.el.div(
        rx.el.p(summary["path"], class_name="font-semibold text-sm truncate"),
        rx.el.div(
            rx.foreach(summary["elements"], code_element_view),
            class_name="ml-4 mt-1 space-y-1",
        ),
        class_name="py-2",
    )


def context_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2("Project Context", class_name="text-lg font-bold"),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                on_click=ContextState.analyze_project,
                class_name="p-2 rounded-md hover:bg-gray-200",
            ),
            class_name="flex items-center justify-between p-4 border-b",
        ),
        rx.el.div(
            rx.cond(
                ContextState.code_map,
                rx.foreach(ContextState.code_map, file_summary_view),
                rx.el.div(
                    "Click refresh to analyze project.",
                    class_name="text-sm text-gray-500 p-4",
                ),
            ),
            class_name="flex-1 p-2 overflow-y-auto",
        ),
        class_name="h-1/2 flex-1 flex flex-col border-t",
    )