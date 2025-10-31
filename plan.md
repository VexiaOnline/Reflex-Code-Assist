# Reflex Build Clone - Local LLM Edition

## Project Overview

### Scope & Intent
Build a web-based development assistant for Reflex applications that mimics the core functionality of Reflex Build, but powered by a **locally-hosted LLM** (text-generation-webui) instead of Claude API. The application provides an interactive chat interface for code analysis, generation, and modification without requiring cloud API costs or external dependencies.

### Key Differences from Original Reflex Build
- ✅ **Local LLM Integration**: Uses text-generation-webui API endpoint (default: `http://localhost:5000`)
- ✅ **Code-Focused Workspace**: File browser + Monaco code editor + context window
- ✅ **Project Management**: Multi-project support with project switching and isolation
- ❌ **No Sandboxed Preview**: Removes the live preview pane and screenshot capabilities
- ❌ **No Remote Execution**: No `run_python` or isolated testing environment
- ✅ **Direct File Operations**: Read/write files directly in the local project directory

### Target Features
1. **Chat Interface**: Natural language interaction with local LLM for code assistance ✅
2. **Code Editor**: Monaco-based editor with syntax highlighting and file tree ✅
3. **Context Management**: Display and manage conversation context (code map, file contents) ✅
4. **Code Generation**: Generate Reflex components, state classes, and event handlers ✅
5. **Code Analysis**: Parse project structure, understand existing code, suggest improvements ✅
6. **File Operations**: Create, read, update, delete files in the project directory ✅
7. **Conversation History**: Persistent chat history with ability to reference previous messages ✅
8. **LLM Configuration**: Settings for endpoint URL, model selection, temperature, max tokens ✅
9. **Project Management**: Create, view, switch, and delete projects with isolated workspaces ✅

---

## Phase 10: Project Storage Restructuring ✅

### Objective
Separate Code Assist app files from user projects completely. Store all user projects in a top-level "projects" folder, never use the app directory as working directory.

### Tasks
- [x] Update project storage structure to use top-level "projects" folder
- [x] Modify ProjectState to create project subfolders within "projects/"
- [x] Update project creation to initialize project folder structure automatically
- [x] Change project metadata to use relative paths within "projects/"
- [x] Update file browser to show empty state when no project selected
- [x] Ensure editor shows placeholder when no project selected
- [x] Update conversation storage to use project subfolders
- [x] Add validation to prevent accessing app directory

**Expected Outcome**: Complete separation of app and user project files, with all projects stored in "projects/" folder.

---

## Progress Summary

### Completed ✅
- **Phase 1-8**: All previous functionality ✅
- **Phase 10**: Project storage restructuring ✅

### Current Task 🔄
- **Phase 10**: Implementing new project storage structure

---

## New Technical Implementation

### Updated Project Storage Structure
```
code-assist-app/               # This Reflex app
├── app/
├── assets/
├── projects/                  # USER PROJECTS FOLDER (top-level)
│   ├── my-reflex-app/        # Individual project folder
│   │   ├── app/              # User's Reflex app code
│   │   ├── assets/
│   │   ├── .code_assist/     # Project-specific metadata
│   │   │   ├── conversations/
│   │   │   └── metadata.json
│   │   └── rxconfig.py
│   └── another-project/
│       └── ...
├── .code_assist/             # Global app settings
│   └── projects.json         # List of all projects
└── requirements.txt
```

### Key Changes
1. **Top-Level Projects Folder**: All user projects live in `./projects/` at the root of the Code Assist app
2. **Project Folder Creation**: When creating a project, a new subfolder is created in `projects/`
3. **No Default Project**: No automatic project selection - user must create or select a project
4. **Empty State UI**: When no project is selected, file browser and editor show empty placeholder states
5. **Project Metadata**: Stored in `.code_assist/projects.json` with relative paths from `projects/` folder
6. **Conversation Storage**: Each project stores conversations in its own `.code_assist/conversations/` subfolder

### Implementation Steps
1. Update ProjectState to use `projects/` folder for all project operations
2. Modify project creation to create project subfolder with initial structure
3. Update EditorState and FileBrowserState to handle no-project-selected state
4. Change all path resolution to work relative to `projects/{project_folder_name}/`
5. Add validation to ensure app directory is never accessed as project directory