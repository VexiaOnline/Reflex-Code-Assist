import reflex as rx
from app.states.settings_state import SettingsState


def settings_modal() -> rx.Component:
    return rx.el.div(
        rx.cond(
            SettingsState.show_settings,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.h3(
                                "LLM Settings", class_name="text-lg font-semibold"
                            ),
                            rx.el.button(
                                rx.icon("x", class_name="h-5 w-5"),
                                on_click=SettingsState.toggle_settings,
                                class_name="p-1 rounded-full hover:bg-gray-200",
                            ),
                            class_name="flex justify-between items-center pb-4 border-b",
                        ),
                        rx.el.div(
                            rx.el.label("Endpoint URL", class_name="font-medium"),
                            rx.el.input(
                                default_value=SettingsState.endpoint_url,
                                on_change=SettingsState.set_endpoint_url,
                                class_name="w-full p-2 border rounded-md mt-1",
                            ),
                            rx.el.label(
                                "Model Name (optional)", class_name="font-medium mt-4"
                            ),
                            rx.el.input(
                                default_value=SettingsState.model_name,
                                on_change=SettingsState.set_model_name,
                                class_name="w-full p-2 border rounded-md mt-1",
                            ),
                            rx.el.label(
                                f"Temperature: {SettingsState.temperature}",
                                class_name="font-medium mt-4",
                            ),
                            rx.el.input(
                                type="range",
                                min=0,
                                max=2,
                                step=0.1,
                                default_value=SettingsState.temperature.to(str),
                                on_change=SettingsState.set_temperature.throttle(50),
                                class_name="w-full mt-1",
                                key=f"temp-slider-{SettingsState.temperature}",
                            ),
                            rx.el.label(
                                f"Max Tokens: {SettingsState.max_tokens}",
                                class_name="font-medium mt-4",
                            ),
                            rx.el.input(
                                type="number",
                                default_value=SettingsState.max_tokens.to(str),
                                on_change=SettingsState.set_max_tokens,
                                class_name="w-full p-2 border rounded-md mt-1",
                            ),
                            class_name="py-4",
                        ),
                        rx.el.div(
                            rx.el.button(
                                "Close",
                                on_click=SettingsState.toggle_settings,
                                class_name="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300",
                            ),
                            class_name="flex justify-end pt-4 border-t",
                        ),
                        class_name="bg-white rounded-lg shadow-xl w-full max-w-md p-6",
                    ),
                    class_name="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50",
                )
            ),
        )
    )