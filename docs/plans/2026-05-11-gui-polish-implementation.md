# GUI Polish Implementation Plan

**Goal:** Apply the approved professional desktop-tool visual treatment to the PyQt GUI.

**Architecture:** Add a small `puzzle_stitcher.ui_theme` module for colors and QSS snippets. Refactor `gui_stitch.py` to use named UI sections and theme helpers while keeping its current thread and solver flow.

**Tasks:**
1. Add tests for theme exports and required style snippets.
2. Implement `puzzle_stitcher/ui_theme.py`.
3. Refactor `gui_stitch.py` layout into header, folder panel, settings panel, action row, and log panel.
4. Run root tests and Python compilation checks.
