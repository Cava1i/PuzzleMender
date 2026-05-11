# Structure Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate the project shell around a reusable puzzle stitching service while keeping the existing `gaps` solver intact.

**Architecture:** Add a small root-level `puzzle_stitcher` package that owns tile discovery, validation, shuffled input generation, and solver orchestration. Refactor the command-line script and PyQt GUI to call that service instead of duplicating workflow code or spawning `gaps/gaps/cli.py` directly.

**Tech Stack:** Python, Pillow, OpenCV/NumPy through the existing `gaps` package, PyQt5 for the optional GUI, pytest for coverage.

---

### Task 1: Outer Workflow Tests

**Files:**
- Create: `tests/test_stitcher.py`

**Steps:**
1. Write tests for scanning mixed `.png` and `.bmp` tiles.
2. Write tests for too few tiles and mismatched tile sizes.
3. Write a high-level `stitch_folder` test with an injected lightweight solver.
4. Run `python -m pytest tests/test_stitcher.py -v` and verify failure because `puzzle_stitcher` does not exist yet.

### Task 2: Reusable Service Layer

**Files:**
- Create: `puzzle_stitcher/__init__.py`
- Create: `puzzle_stitcher/stitcher.py`

**Steps:**
1. Add `StitchConfig`, `StitchResult`, and `StitchError`.
2. Implement `find_tile_images`, `create_shuffled_input`, `solve_with_gaps`, and `stitch_folder`.
3. Run `python -m pytest tests/test_stitcher.py -v` and verify it passes.

### Task 3: Entry Point Refactor

**Files:**
- Modify: `run_gaps_stitch.py`
- Modify: `gui_stitch.py`

**Steps:**
1. Replace duplicated stitching code in the CLI wrapper with `puzzle_stitcher.stitcher.stitch_folder`.
2. Replace duplicated stitching and subprocess code in the GUI worker thread with the same service.
3. Keep defaults compatible with the current project: 28 columns, 16 rows, 64 px, 20 generations, 200 population.

### Task 4: Project Hygiene

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`

**Steps:**
1. Ignore caches and generated outputs.
2. Add root project metadata and optional GUI dependency group.
3. Run root service tests and existing `gaps` tests.
