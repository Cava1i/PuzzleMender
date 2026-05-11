"""Project-specific helpers for building and solving tile puzzles."""

from puzzle_stitcher.stitcher import (
    StitchConfig,
    StitchError,
    StitchResult,
    TileGeometry,
    create_shuffled_input,
    find_tile_images,
    infer_grid_from_tile_count,
    solve_with_gaps,
    stitch_folder,
)
from puzzle_stitcher.paths import default_output_dir, runtime_base_dir

__all__ = [
    "StitchConfig",
    "StitchError",
    "StitchResult",
    "TileGeometry",
    "create_shuffled_input",
    "default_output_dir",
    "runtime_base_dir",
    "find_tile_images",
    "infer_grid_from_tile_count",
    "solve_with_gaps",
    "stitch_folder",
]
