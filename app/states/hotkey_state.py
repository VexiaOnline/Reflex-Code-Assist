import reflex as rx
from app.states.editor_state import EditorState
from app.states.settings_state import SettingsState


class HotkeyState(rx.State):
    @rx.event
    def handle_hotkey(self, key: str, mods: dict[str, bool]):
        is_ctrl_or_meta = mods.get("ctrlKey") or mods.get("metaKey")
        if is_ctrl_or_meta and key.lower() == "s":
            yield rx.prevent_default
            yield EditorState.save_file
            return
        if is_ctrl_or_meta and key.lower() == "k":
            yield rx.prevent_default
            yield rx.set_focus("chat-input")
            return
        if key == "Escape":
            return SettingsState.toggle_settings
        return rx.console_log(f"Unhandled key press: {key}")