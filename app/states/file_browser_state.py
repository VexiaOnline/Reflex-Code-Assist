import reflex as rx
from typing import Any, Union, TypedDict
from app.states.editor_state import EditorState, FileTree, FileTreeItem


class FileListItem(TypedDict):
    path: str
    name: str
    is_folder: bool
    depth: int


class FileBrowserState(rx.State):
    """State to manage the file browser UI and interactions."""

    file_tree: FileTree = []
    file_list: list[FileListItem] = []
    expanded_dirs: set[str] = set()

    def _build_flat_list_recursive(self, tree: FileTree, path: str, depth: int):
        """Helper to recursively build the flat file list."""
        for name, children in tree:
            full_path = f"{path}/{name}" if path != "." else name
            if children is None:
                self.file_list.append(
                    {
                        "path": full_path,
                        "name": name,
                        "is_folder": False,
                        "depth": depth,
                    }
                )
            else:
                self.file_list.append(
                    {"path": full_path, "name": name, "is_folder": True, "depth": depth}
                )
                if full_path in self.expanded_dirs:
                    self._build_flat_list_recursive(children, full_path, depth + 1)

    def _build_flat_list(self):
        """Build the flat file list from the tree."""
        self.file_list = []
        self._build_flat_list_recursive(self.file_tree, ".", 0)

    @rx.event
    def toggle_expand(self, path: str):
        """Toggle the expanded state of a directory."""
        if path in self.expanded_dirs:
            self.expanded_dirs.remove(path)
        else:
            self.expanded_dirs.add(path)
        self._build_flat_list()

    @rx.event
    async def handle_file_click(self, path: str):
        """Handle when a file is clicked."""
        editor_state = await self.get_state(EditorState)
        yield editor_state.open_file_in_tab(path)


def file_item_view(item: FileListItem) -> rx.Component:
    return rx.el.div(
        rx.cond(
            item["is_folder"],
            rx.el.div(
                rx.icon("folder", class_name="h-4 w-4 mr-2"),
                rx.el.span(item["name"]),
                class_name="flex items-center cursor-pointer p-1 rounded hover:bg-gray-200",
                on_click=FileBrowserState.toggle_expand(item["path"]),
            ),
            rx.el.div(
                rx.icon("file", class_name="h-4 w-4 mr-2"),
                rx.el.span(item["name"]),
                class_name="flex items-center cursor-pointer p-1 rounded hover:bg-gray-200",
                on_click=FileBrowserState.handle_file_click(item["path"]),
            ),
        ),
        class_name=rx.cond(
            (EditorState.current_file == item["path"]) & ~item["is_folder"],
            "bg-blue-100 rounded-md",
            "",
        ),
        style={
            "padding_left": rx.cond(item["depth"] > 0, f"{item['depth']}rem", "0.25rem")
        },
    )