# Rectangular Adaptive Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically support rectangular tile images by normalizing them to square solver pieces and restoring the final image to the original tile ratio.

**Architecture:** Keep the bundled `gaps` solver unchanged. Add a geometry detection layer in `puzzle_stitcher.stitcher`: selected tiles are inspected, rectangular tiles are resized to square temporary pieces for the solver, and the solver output is resized back to `columns * original_width` by `rows * original_height`.

**Tech Stack:** Python, Pillow, pytest, existing `gaps` solver.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/test_stitcher.py`

**Steps:**
1. Add a test proving `create_shuffled_input` converts `10x6` tiles into a `20x20` square solver input for a `2x2` puzzle.
2. Add a test proving `stitch_folder` writes a square intermediate result and restores the final output to `20x12`.
3. Run `python -m pytest tests/test_stitcher.py -v` and confirm failure.

### Task 2: Geometry Layer

**Files:**
- Modify: `puzzle_stitcher/stitcher.py`

**Steps:**
1. Add `TileGeometry`.
2. Detect selected tile dimensions.
3. Use `max(width, height)` as the temporary square solver size.
4. Resize each rectangular tile to the square solver size before pasting.
5. Pass a solver config whose `tile_size` matches the square solver size.

### Task 3: Restore Final Ratio

**Files:**
- Modify: `puzzle_stitcher/stitcher.py`

**Steps:**
1. Add a square solver output path, `gaps_solved_square.png`.
2. Save solver output there when adaptive mode is active.
3. Resize the square solver output back to original final dimensions.
4. Keep square tile behavior unchanged.

### Task 4: UI Messaging and Verification

**Files:**
- Modify: `gui_stitch.py`
- Modify: `tests/test_stitcher.py`

**Steps:**
1. Make the GUI summary explain that the size field is only a fallback/solver hint.
2. Run root tests and Python compilation.
