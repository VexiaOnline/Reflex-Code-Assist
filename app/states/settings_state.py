import reflex as rx
import logging


class SettingsState(rx.State):
    show_settings: bool = False
    endpoint_url: str = "http://localhost:5000"
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000

    @rx.event
    def toggle_settings(self):
        self.show_settings = not self.show_settings

    @rx.event
    def set_endpoint_url(self, url: str):
        self.endpoint_url = url

    @rx.event
    def set_model_name(self, name: str):
        self.model_name = name

    @rx.event
    def set_temperature(self, temp: str):
        try:
            self.temperature = float(temp)
        except (ValueError, TypeError) as e:
            logging.exception(f"Error setting temperature: {e}")

    @rx.event
    def set_max_tokens(self, tokens: str):
        try:
            self.max_tokens = int(tokens)
        except (ValueError, TypeError) as e:
            logging.exception(f"Error setting max tokens: {e}")