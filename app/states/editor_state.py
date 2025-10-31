import reflex as rx
import os
import logging
from typing import Any, cast, Union

FileTreeItem = tuple[str, Union["FileTree", None]]
FileTree = list[FileTreeItem]


class EditorState(rx.State):
    """State for the file system and code editor."""

    files: dict[str, str] = {}
    current_content: str = ""
    unsaved_files: set[str] = set()
    open_tabs: list[str] = []
    active_tab_index: int = -1

    def _get_file_tree(self, path: str = ".") -> FileTree:
        """Recursively get the file tree for a given path."""
        tree: FileTree = []
        try:
            for item in sorted(os.listdir(path)):
                if item.startswith((".", "__")) or item == "node_modules":
                    continue
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    tree.append((item, self._get_file_tree(full_path)))
                else:
                    tree.append((item, None))
        except FileNotFoundError as e:
            logging.exception(f"File not found while building file tree: {e}")
            return []
        except Exception as e:
            logging.exception(f"Error getting file tree for {path}: {e}")
            return []
        return tree

    @rx.var
    def current_file(self) -> str:
        if 0 <= self.active_tab_index < len(self.open_tabs):
            return self.open_tabs[self.active_tab_index]
        return ""

    @rx.var
    def is_file_open(self) -> bool:
        return self.active_tab_index != -1

    @rx.event
    async def on_load(self):
        """Load the file tree and analyze the project on app load."""
        from app.states.file_browser_state import FileBrowserState
        from app.states.context_state import ContextState
        from app.states.project_state import ProjectState

        project_state = await self.get_state(ProjectState)
        file_browser_state = await self.get_state(FileBrowserState)
        if project_state.has_active_project:
            file_tree_data = self._get_file_tree(
                path=project_state.current_project_path
            )
            file_browser_state.file_tree = file_tree_data
            yield ContextState.analyze_project
        else:
            file_browser_state.file_tree = []
        file_browser_state._build_flat_list()

    def _read_file_content(self, path: str):
        if path not in self.files:
            try:
                with open(path, "r") as f:
                    self.files[path] = f.read()
            except Exception as e:
                logging.exception(f"Error reading file {path}: {e}")
                self.files[path] = f"Error reading file: {e}"

    @rx.event
    def open_file_in_tab(self, path: str):
        if path not in self.open_tabs:
            self.open_tabs.append(path)
        self.active_tab_index = self.open_tabs.index(path)
        self._read_file_content(path)
        self.current_content = self.files.get(path, "")

    @rx.event
    def switch_tab(self, index: int):
        if 0 <= index < len(self.open_tabs):
            self.active_tab_index = index
            path = self.open_tabs[index]
            self.current_content = self.files.get(path, "")

    @rx.event
    def close_tab(self, index: int):
        if not 0 <= index < len(self.open_tabs):
            return
        path_to_close = self.open_tabs.pop(index)
        if path_to_close in self.unsaved_files:
            self.unsaved_files.remove(path_to_close)
        if not self.open_tabs:
            self.active_tab_index = -1
            self.current_content = ""
        elif self.active_tab_index >= index:
            self.active_tab_index = max(0, self.active_tab_index - 1)
            new_path = self.open_tabs[self.active_tab_index]
            self.current_content = self.files.get(new_path, "")

    @rx.event
    def on_change(self, content: str):
        """Handle content change in the editor."""
        if self.is_file_open:
            self.current_content = content
            if self.files.get(self.current_file, "") != content:
                self.unsaved_files.add(self.current_file)
            elif self.current_file in self.unsaved_files:
                self.unsaved_files.remove(self.current_file)

    @rx.event
    def save_file(self):
        """Save the current file."""
        if not self.is_file_open:
            return rx.toast.warning("No file is open to save.")
        try:
            self.files[self.current_file] = self.current_content
            with open(self.current_file, "w") as f:
                f.write(self.current_content)
            if self.current_file in self.unsaved_files:
                self.unsaved_files.remove(self.current_file)
            return rx.toast.success(f"Saved {self.current_file}")
        except Exception as e:
            logging.exception(f"Error saving file {self.current_file}: {e}")
            return rx.toast.error(f"Failed to save {self.current_file}")