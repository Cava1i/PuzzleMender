"""Command-line wrapper for the project-specific stitching workflow."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from puzzle_stitcher.paths import default_output_dir, runtime_base_dir
from puzzle_stitcher.stitcher import (
    StitchConfig,
    StitchError,
    find_tile_images,
    infer_grid_from_tile_count,
    stitch_folder,
)


ENV_INPUT_DIR = "GAPS_STITCH_INPUT_DIR"
ENV_OUTPUT_DIR = "GAPS_STITCH_OUTPUT_DIR"
ENV_AUTO_GRID = "GAPS_STITCH_AUTO_GRID"
ENV_COLUMNS = "GAPS_STITCH_COLUMNS"
ENV_ROWS = "GAPS_STITCH_ROWS"
ENV_SIZE = "GAPS_STITCH_SIZE"
ENV_GENERATIONS = "GAPS_STITCH_GENERATIONS"
ENV_POPULATION = "GAPS_STITCH_POPULATION"
ENV_SEED = "GAPS_STITCH_SEED"
PROGRESS_BAR_WIDTH = 28


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    return int(value)


def _env_optional_int(name: str) -> Optional[int]:
    value = os.environ.get(name)
    if not value:
        return None
    return int(value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def build_parser(
    default_folder: Path,
    default_output_path: Path,
    default_auto_grid: bool,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a shuffled puzzle from tile images and solve it with gaps. "
            "Tile size, rectangular tiles, and final ratio restoration are detected "
            "automatically."
        ),
        epilog=(
            "Rectangular adaptive mode is automatic: rectangular tiles are stretched "
            "to square solver pieces, solved, then restored to their original ratio "
            "in gaps_solved_final.png."
        ),
    )
    parser.add_argument(
        "--folder",
        default=str(default_folder),
        help=f"Folder containing png/bmp tile images. Env: {ENV_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_output_path),
        help=f"Folder for generated images. Env: {ENV_OUTPUT_DIR}",
    )
    grid_group = parser.add_mutually_exclusive_group()
    grid_group.add_argument(
        "--auto-grid",
        dest="auto_grid",
        action="store_true",
        help="Infer columns/rows from the number of tile images.",
    )
    grid_group.add_argument(
        "--manual-grid",
        dest="auto_grid",
        action="store_false",
        help="Use --columns and --rows instead of inferring the grid.",
    )
    parser.set_defaults(auto_grid=default_auto_grid)
    parser.add_argument(
        "--columns",
        type=int,
        default=_env_int(ENV_COLUMNS, 28),
        help=f"Puzzle columns when --manual-grid is used. Env: {ENV_COLUMNS}",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=_env_int(ENV_ROWS, 16),
        help=f"Puzzle rows when --manual-grid is used. Env: {ENV_ROWS}",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=_env_int(ENV_SIZE, 64),
        help=f"Fallback tile size; actual tile dimensions are detected. Env: {ENV_SIZE}",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=_env_int(ENV_GENERATIONS, 5),
        help=f"Number of genetic algorithm generations. Env: {ENV_GENERATIONS}",
    )
    parser.add_argument(
        "--population",
        type=int,
        default=_env_int(ENV_POPULATION, 50),
        help=f"Genetic algorithm population size. Env: {ENV_POPULATION}",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=_env_optional_int(ENV_SEED),
        help=f"Optional shuffle seed for reproducible input generation. Env: {ENV_SEED}",
    )
    return parser


def format_progress(
    value: int,
    message: str,
    width: int = PROGRESS_BAR_WIDTH,
) -> str:
    """Format CLI progress as a stable text progress bar."""

    if value < 0:
        return f"[处理中] {message}"

    percent = max(0, min(100, value))
    filled = int(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent:3d}% {message}"


def print_progress(value: int, message: str) -> None:
    print(format_progress(value, message), flush=True)


def main(argv: Optional[Sequence[str]] = None) -> int:
    base_dir = runtime_base_dir(__file__)
    default_folder = Path(os.environ.get(ENV_INPUT_DIR, str(base_dir.parent / "png_output")))
    default_output_path = Path(
        os.environ.get(ENV_OUTPUT_DIR, str(default_output_dir(base_dir)))
    )
    parser = build_parser(
        default_folder=default_folder,
        default_output_path=default_output_path,
        default_auto_grid=_env_bool(ENV_AUTO_GRID, True),
    )
    args = parser.parse_args(argv)

    print("=== 拼图脚本（基于本地 gaps 源码）===")
    print(f"切片目录: {Path(args.folder)}")
    print(f"输出目录: {Path(args.output_dir)}")
    print("长方形自适应: 自动识别")
    print(f"求解参数: {args.generations} 代 / {args.population} 种群")

    try:
        columns, rows = args.columns, args.rows
        if args.auto_grid:
            images = find_tile_images(Path(args.folder))
            columns, rows = infer_grid_from_tile_count(len(images))
            print(f"自动识别行列: {columns} x {rows}（{len(images)} 张切片）")
        else:
            print(f"手动行列: {columns} x {rows}")

        config = StitchConfig(
            columns=columns,
            rows=rows,
            tile_size=args.size,
            generations=args.generations,
            population=args.population,
            seed=args.seed,
        )
        result = stitch_folder(
            Path(args.folder),
            Path(args.output_dir),
            config,
            log_callback=print,
            progress_callback=print_progress,
        )
    except StitchError as exc:
        print(f"错误: {exc}")
        return 1

    print(f"拼接成功，临时输入图: {result.input_image}")
    if result.square_output_image:
        print(f"长方形中间图: {result.square_output_image}")
    print(f"最终还原图: {result.output_image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
