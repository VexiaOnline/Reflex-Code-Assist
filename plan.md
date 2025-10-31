# Code Assist - Refactor Plan

## Phase 1: Fix Critical UI and File Path Issues ✅
**Goal**: Fix file path handling and chat UI width issues before refactoring

### Tasks:
- [x] Fix file path handling in `apply_code` to prevent duplicate project paths
  - Strip project path prefix from LLM-provided paths if present (loop handles multiple duplicates)
  - Normalize paths to always be relative to project root
  - Security check prevents directory traversal
- [x] Fix chat column width - prevent expansion when typing long messages
  - Set fixed width (w-96) on chat container
  - Add proper text wrapping for input field with `min-w-0`
- [x] Test both fixes to ensure they work correctly
  - ✅ Path handling tested: single/double/triple duplicates all handled correctly
  - ✅ UI verified: chat maintains fixed width

---

## Phase 2: Refactor LLM Prompt System (Collapsible Thinking Blocks) ✅
**Goal**: Make the chat interface work like Reflex Build agent with collapsible sections

### Tasks:
- [x] Create new structured response format for CodeAssist LLM
  - Defined response sections: `[THINKING]`, `[EXPLANATION]`, `[CODE]`
  - Updated system prompt to enforce this structure with examples
  - Added rules: "Keep thinking concise", "Explain briefly"
- [x] Update response parser to handle structured sections
  - Parser now recognizes `[THINKING]`, `[EXPLANATION]`, `[CODE]` markers
  - Backward compatible with legacy markdown format
  - Tested with structured, legacy, and mixed formats
- [x] Build collapsible UI components for each section type
  - Created `thinking_block_view()` - collapsible card with brain icon
  - Thinking blocks collapsed by default (expand on click)
  - Styled with gray background to differentiate from explanations
  - Code blocks keep existing Apply/Reject UI
- [x] Add collapse state management
  - Track expanded thinking blocks by ID
  - `toggle_thinking_block()` event handler
  - State persists across re-renders

---

## Phase 3: Enhanced Context and Agent Instructions ✅
**Goal**: Improve context system to guide LLM behavior and reduce verbose output

### Tasks:
- [x] Refactor system prompt with Reflex Build-style instructions
  - Added explicit format rules and section markers
  - Included structured output examples
  - Defined assistant role: "Expert Reflex developer"
- [x] Improve context prompt generation
  - Context includes code map (file structure)
  - Shows current open file content
  - RAG system retrieves relevant docs (if available)
  - Context formatted to guide structured responses
- [x] Add response guidelines to system prompt
  - "Use [THINKING] for analysis, [EXPLANATION] for user-facing text, [CODE] for implementations"
  - "Wrap sections in markers for proper parsing"
  - File path format: `File: path/to/file.py` before code blocks
- [x] Test and iterate on prompt effectiveness
  - Parser tested with multiple response formats
  - Collapse/expand functionality verified
  - UI components render correctly

---

## Success Criteria
- ✅ Files are written to correct project paths (no duplicates)
- ✅ Chat UI maintains fixed width regardless of message length
- ✅ LLM responses are structured with collapsible sections
- ✅ Thinking blocks collapse by default (like Reflex Build)
- ✅ Explanations are brief and focused
- ✅ Code blocks appear with Apply/Reject actions
- ✅ Overall chat feels clean and organized like Reflex Build interface

---

## Notes
- All phases complete! 🎉
- System prompt guides LLM to produce structured output
- Parser handles both new and legacy formats
- Thinking blocks provide clean, collapsible reasoning view
- Next: User testing to refine prompt effectiveness
