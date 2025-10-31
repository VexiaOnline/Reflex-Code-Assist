import reflex as rx
import os
import json
import uuid
from datetime import datetime
import logging
from typing import TypedDict

USER_PROJECTS_ROOT = "projects"
APP_DATA_DIR = ".code_assist"
PROJECTS_FILE = os.path.join(APP_DATA_DIR, "projects.json")


class Project(TypedDict):
    id: str
    name: str
    path: str
    created_date: str
    last_accessed: str


class ProjectState(rx.State):
    projects: list[Project] = []
    current_project_id: str = ""
    show_project_manager: bool = False

    def _ensure_app_data_dir(self):
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        os.makedirs(USER_PROJECTS_ROOT, exist_ok=True)

    @rx.event
    def load_projects(self):
        self._ensure_app_data_dir()
        if os.path.exists(PROJECTS_FILE):
            try:
                with open(PROJECTS_FILE, "r") as f:
                    self.projects = json.load(f)
                if not self.current_project_id and self.projects:
                    latest_project = max(
                        self.projects, key=lambda p: p["last_accessed"]
                    )
                    self.current_project_id = latest_project["id"]
            except (json.JSONDecodeError, IndexError, ValueError) as e:
                logging.exception(f"Could not load or parse projects: {e}")
                self.projects = []
                self.current_project_id = ""

    def _save_projects(self):
        self._ensure_app_data_dir()
        with open(PROJECTS_FILE, "w") as f:
            json.dump(self.projects, f, indent=2)

    def _initialize_project_structure(self, project_path: str):
        """Creates the basic folder structure for a new Reflex project."""
        os.makedirs(os.path.join(project_path, "app"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "assets"), exist_ok=True)
        with open(os.path.join(project_path, "rxconfig.py"), "w") as f:
            f.write("""import reflex as rx

config = rx.Config(app_name='app')
""")
        with open(os.path.join(project_path, "app", "app.py"), "w") as f:
            f.write("""import reflex as rx

def index():
    return rx.text('Welcome to your new Reflex app!')

app = rx.App()
app.add_page(index)
""")

    @rx.event
    def create_project(self, form_data: dict):
        project_name = form_data.get("name")
        if not project_name:
            return rx.toast.error("Project name is required.")
        project_folder_name = "".join(
            (
                c
                for c in project_name.lower().replace(" ", "-")
                if c.isalnum() or c == "-"
            )
        )
        project_relative_path = project_folder_name
        full_project_path = os.path.join(USER_PROJECTS_ROOT, project_relative_path)
        if os.path.exists(full_project_path):
            return rx.toast.error(
                f"Project directory '{full_project_path}' already exists."
            )
        try:
            self._initialize_project_structure(full_project_path)
        except Exception as e:
            logging.exception(f"Failed to initialize project structure: {e}")
            return rx.toast.error("Failed to create project folders.")
        new_project = {
            "id": str(uuid.uuid4()),
            "name": project_name,
            "path": project_relative_path,
            "created_date": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
        }
        self.projects.append(new_project)
        self.current_project_id = new_project["id"]
        self._save_projects()
        yield ProjectState.switch_project(new_project["id"])
        return rx.toast.success(f"Project '{project_name}' created and selected.")

    @rx.event
    def switch_project(self, project_id: str):
        if project_id not in [p["id"] for p in self.projects]:
            return rx.toast.error("Project not found.")
        self.current_project_id = project_id
        project = self.get_project_by_id(project_id)
        if project:
            project["last_accessed"] = datetime.now().isoformat()
            self._save_projects()
        from app.states.editor_state import EditorState

        self.show_project_manager = False
        yield EditorState.on_load
        yield rx.toast.info(f"Switched to project '{self.current_project_name}'")

    @rx.event
    def delete_project(self, project_id: str):
        project_to_delete = self.get_project_by_id(project_id)
        if not project_to_delete:
            return rx.toast.error("Project not found.")
        self.projects = [p for p in self.projects if p["id"] != project_id]
        if self.current_project_id == project_id:
            self.current_project_id = self.projects[0]["id"] if self.projects else ""
        self._save_projects()
        from app.states.editor_state import EditorState

        yield EditorState.on_load
        return rx.toast.info(f"Project '{project_to_delete['name']}' removed.")
        from app.states.editor_state import EditorState

        yield EditorState.on_load
        return rx.toast.info(f"Project '{project_to_delete['name']}' removed.")

    @rx.var
    def current_project(self) -> Project | None:
        if not self.current_project_id:
            return None
        return self.get_project_by_id(self.current_project_id)

    @rx.event
    def get_project_by_id(self, project_id: str) -> Project | None:
        for p in self.projects:
            if p["id"] == project_id:
                return p
        return None

    @rx.var
    def current_project_name(self) -> str:
        if self.current_project:
            return self.current_project["name"]
        return "No Project Selected"

    @rx.var
    def current_project_path(self) -> str:
        if self.current_project:
            return os.path.join(USER_PROJECTS_ROOT, self.current_project["path"])
        return ""

    @rx.var
    def has_active_project(self) -> bool:
        return self.current_project_id != ""

    @rx.event
    def toggle_project_manager(self):
        self.show_project_manager = not self.show_project_manager