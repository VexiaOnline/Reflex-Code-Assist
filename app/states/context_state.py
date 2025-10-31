import reflex as rx
import os
import ast
import logging
from typing import TypedDict, cast


class CodeElement(TypedDict):
    type: str
    name: str
    line: int


class FileSummary(TypedDict):
    path: str
    elements: list[CodeElement]


class ContextState(rx.State):
    """Manages the code analysis and context for the LLM."""

    code_map: list[FileSummary] = []
    show_context_panel: bool = True

    def _analyze_file(self, file_path: str) -> list[CodeElement]:
        """Analyzes a Python file to extract key code elements."""
        elements = []
        try:
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        elements.append(
                            {"type": "import", "name": alias.name, "line": node.lineno}
                        )
                elif isinstance(node, ast.ImportFrom):
                    elements.append(
                        {
                            "type": "import_from",
                            "name": node.module or "",
                            "line": node.lineno,
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    elements.append(
                        {"type": "class", "name": node.name, "line": node.lineno}
                    )
                elif isinstance(node, ast.FunctionDef):
                    decorator_list = [
                        d.id for d in node.decorator_list if isinstance(d, ast.Name)
                    ]
                    element_type = "function"
                    if "rx.event" in decorator_list:
                        element_type = "event"
                    elif "rx.var" in decorator_list:
                        element_type = "var"
                    elements.append(
                        {"type": element_type, "name": node.name, "line": node.lineno}
                    )
        except Exception as e:
            logging.exception(f"Error analyzing file {file_path}: {e}")
        return elements

    def _build_code_map(self, path: str = ".") -> list[FileSummary]:
        """Builds a map of the entire codebase."""
        project_map = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [
                d
                for d in dirs
                if d not in ["node_modules", ".venv", "__pycache__"]
                and (not d.startswith("."))
            ]
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    elements = self._analyze_file(file_path)
                    if elements:
                        project_map.append({"path": file_path, "elements": elements})
        return project_map

    @rx.event
    async def analyze_project(self):
        """Event handler to trigger project analysis."""
        from app.states.project_state import ProjectState

        project_state = await self.get_state(ProjectState)
        if not project_state.has_active_project:
            self.code_map = []
            return
        self.code_map = self._build_code_map(path=project_state.current_project_path)
        return rx.toast.info(
            f"Analysis of {project_state.current_project_name} complete."
        )

    @rx.event
    def toggle_context_panel(self):
        self.show_context_panel = not self.show_context_panel