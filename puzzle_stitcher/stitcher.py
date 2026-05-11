"""Reusable workflow for preparing and solving square tile puzzles."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple, Union

from PIL import Image


DEFAULT_IMAGE_PATTERNS = ("*.png", "*.bmp")
DEFAULT_INPUT_NAME = "gaps_input_shuffled.png"
DEFAULT_SQUARE_OUTPUT_NAME = "gaps_solved_square.png"
DEFAULT_OUTPUT_NAME = "gaps_solved_final.png"


class StitchError(RuntimeError):
    """Raised when the stitching workflow cannot continue."""


@dataclass(frozen=True)
class StitchConfig:
    """Settings shared by the command-line and GUI entry points."""

    columns: int = 28
    rows: int = 16
    tile_size: int = 64
    generations: int = 5
    population: int = 50
    seed: Optional[int] = None
    input_name: str = DEFAULT_INPUT_NAME
    square_output_name: str = DEFAULT_SQUARE_OUTPUT_NAME
    output_name: str = DEFAULT_OUTPUT_NAME
    image_patterns: Tuple[str, ...] = DEFAULT_IMAGE_PATTERNS

    @property
    def required_tiles(self) -> int:
        return self.columns * self.rows

    def validate(self) -> None:
        numeric_values = {
            "columns": self.columns,
            "rows": self.rows,
            "tile_size": self.tile_size,
            "generations": self.generations,
            "population": self.population,
        }
        for name, value in numeric_values.items():
            if value <= 0:
                raise StitchError(f"{name} must be a positive integer")

        if self.generations < 2:
            raise StitchError("generations must be at least 2")


@dataclass(frozen=True)
class TileGeometry:
    """Detected dimensions used to adapt rectangular tiles for the solver."""

    width: int
    height: int

    @property
    def solver_size(self) -> int:
        return max(self.width, self.height)

    @property
    def is_rectangular(self) -> bool:
        return self.width != self.height

    def solver_canvas_size(self, columns: int, rows: int) -> Tuple[int, int]:
        return columns * self.solver_size, rows * self.solver_size

    def final_canvas_size(self, columns: int, rows: int) -> Tuple[int, int]:
        return columns * self.width, rows * self.height


@dataclass(frozen=True)
class StitchResult:
    """Paths and metadata produced by a stitching run."""

    input_image: Path
    output_image: Path
    selected_images: Tuple[Path, ...]
    total_tiles: int
    square_output_image: Optional[Path] = None
    tile_geometry: Optional[TileGeometry] = None


Solver = Callable[
    [Path, Path, StitchConfig, Optional[Callable[[str], None]]],
    Path,
]
ProgressCallback = Callable[[int, str], None]


def _log(log_callback: Optional[Callable[[str], None]], message: str) -> None:
    if log_callback:
        log_callback(message)


def _progress(
    progress_callback: Optional[ProgressCallback],
    value: int,
    message: str,
) -> None:
    if progress_callback:
        progress_callback(value, message)


def _resize_filter() -> int:
    if hasattr(Image, "Resampling"):
        return Image.Resampling.BICUBIC
    return Image.BICUBIC


def find_tile_images(
    folder: Union[Path, str],
    patterns: Sequence[str] = DEFAULT_IMAGE_PATTERNS,
) -> List[Path]:
    """Return sorted tile image paths from a folder."""

    folder_path = Path(folder)
    if not folder_path.exists():
        raise StitchError(f"Tile folder does not exist: {folder_path}")
    if not folder_path.is_dir():
        raise StitchError(f"Tile path is not a folder: {folder_path}")

    images = {
        path.resolve()
        for pattern in patterns
        for path in folder_path.glob(pattern)
        if path.is_file()
    }

    if not images:
        joined_patterns = ", ".join(patterns)
        raise StitchError(f"No tile images found in {folder_path} ({joined_patterns})")

    return sorted(images, key=lambda path: path.name.lower())


def infer_grid_from_tile_count(tile_count: int) -> Tuple[int, int]:
    """Infer a landscape-oriented grid that uses every tile."""

    if tile_count <= 0:
        raise StitchError("Tile count must be a positive integer")

    best_columns = tile_count
    best_rows = 1
    best_gap = tile_count - 1

    factor = 1
    while factor * factor <= tile_count:
        if tile_count % factor == 0:
            rows = factor
            columns = tile_count // factor
            gap = columns - rows
            if gap < best_gap:
                best_columns = columns
                best_rows = rows
                best_gap = gap
        factor += 1

    return best_columns, best_rows


def _select_images(images: Sequence[Union[Path, str]], config: StitchConfig) -> List[Path]:
    image_paths = [Path(image) for image in images]
    required_tiles = config.required_tiles
    if len(image_paths) < required_tiles:
        raise StitchError(
            f"Need {required_tiles} tiles for {config.columns}x{config.rows}, "
            f"but found {len(image_paths)}"
        )

    selected_images = image_paths[:]
    random.Random(config.seed).shuffle(selected_images)
    return selected_images[:required_tiles]


def _detect_tile_geometry(images: Sequence[Path]) -> TileGeometry:
    detected_size: Optional[Tuple[int, int]] = None
    detected_path: Optional[Path] = None

    for image_path in images:
        with Image.open(image_path) as tile:
            tile_size = tile.size

        if detected_size is None:
            detected_size = tile_size
            detected_path = image_path
            continue

        if tile_size != detected_size:
            raise StitchError(
                "All selected tiles must have the same dimensions; "
                f"{detected_path} is {detected_size[0]}x{detected_size[1]}, "
                f"but {image_path} is {tile_size[0]}x{tile_size[1]}"
            )

    if detected_size is None:
        raise StitchError("No tile images selected")

    return TileGeometry(width=detected_size[0], height=detected_size[1])


def _create_shuffled_input_with_geometry(
    images: Sequence[Union[Path, str]],
    output_path: Union[Path, str],
    config: StitchConfig,
) -> Tuple[Tuple[Path, ...], TileGeometry]:
    selected_images = _select_images(images, config)
    geometry = _detect_tile_geometry(selected_images)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", geometry.solver_canvas_size(config.columns, config.rows))

    square_size = (geometry.solver_size, geometry.solver_size)
    for index, image_path in enumerate(selected_images):
        with Image.open(image_path) as tile:
            if tile.size != (geometry.width, geometry.height):
                raise StitchError(
                    f"Tile {image_path} changed dimensions while processing"
                )

            tile_image = tile.convert("RGB")
            if tile_image.size != square_size:
                tile_image = tile_image.resize(square_size, _resize_filter())

            x = (index % config.columns) * geometry.solver_size
            y = (index // config.columns) * geometry.solver_size
            canvas.paste(tile_image, (x, y))

    canvas.save(output)
    return tuple(selected_images), geometry


def create_shuffled_input(
    images: Sequence[Union[Path, str]],
    output_path: Union[Path, str],
    config: StitchConfig,
) -> Tuple[Path, ...]:
    """Create the temporary shuffled puzzle image expected by `gaps`."""

    config.validate()
    selected_images, _geometry = _create_shuffled_input_with_geometry(
        images, output_path, config
    )
    return selected_images


def solve_with_gaps(
    puzzle_path: Path,
    solution_path: Path,
    config: StitchConfig,
    log_callback: Optional[Callable[[str], None]] = None,
    gaps_source_dir: Optional[Path] = None,
) -> Path:
    """Solve a prepared puzzle image with the bundled `gaps` package."""

    config.validate()
    candidate_dirs = []
    if gaps_source_dir:
        candidate_dirs.append(Path(gaps_source_dir))
    else:
        if hasattr(sys, "_MEIPASS"):
            candidate_dirs.append(Path(sys._MEIPASS) / "gaps")  # type: ignore[attr-defined]
        candidate_dirs.append(Path(__file__).resolve().parents[1] / "gaps")

    for gaps_dir in candidate_dirs:
        if gaps_dir.exists():
            gaps_dir_string = str(gaps_dir)
            if gaps_dir_string not in sys.path:
                sys.path.insert(0, gaps_dir_string)
            break

    try:
        import cv2 as cv  # pylint: disable=import-outside-toplevel
        import numpy as np  # pylint: disable=import-outside-toplevel
        from gaps.genetic_algorithm import (  # pylint: disable=import-outside-toplevel
            GeneticAlgorithm,
        )
    except ImportError as exc:
        raise StitchError(
            "Bundled gaps solver package is not importable. "
            "Run from the project root or rebuild the executable with --paths gaps."
        ) from exc

    puzzle = Path(puzzle_path)
    solution = Path(solution_path)
    solution.parent.mkdir(parents=True, exist_ok=True)

    input_puzzle = cv.imdecode(np.fromfile(str(puzzle), dtype=np.uint8), cv.IMREAD_COLOR)
    if input_puzzle is None:
        raise StitchError(f"Failed to read puzzle image: {puzzle}")

    _log(log_callback, f"Population: {config.population}")
    _log(log_callback, f"Generations: {config.generations}")
    _log(log_callback, f"Piece size: {config.tile_size}")

    ga = GeneticAlgorithm(
        image=input_puzzle,
        piece_size=config.tile_size,
        population_size=config.population,
        generations=config.generations,
    )
    result = ga.start_evolution(verbose=False)
    output_image = result.to_image()

    encoded, output_buffer = cv.imencode(".png", output_image)
    if not encoded:
        raise StitchError(f"Failed to encode solution image: {solution}")
    output_buffer.tofile(str(solution))

    _log(log_callback, "Puzzle solved")
    return solution


def _restore_rectangular_solution(
    square_solution_path: Path,
    final_solution_path: Path,
    config: StitchConfig,
    geometry: TileGeometry,
) -> None:
    final_solution_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(square_solution_path) as square_solution:
        restored = square_solution.resize(
            geometry.final_canvas_size(config.columns, config.rows),
            _resize_filter(),
        )
        restored.save(final_solution_path)


def stitch_folder(
    folder: Union[Path, str],
    output_dir: Union[Path, str],
    config: StitchConfig,
    solver: Solver = solve_with_gaps,
    log_callback: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> StitchResult:
    """Prepare a shuffled input image and solve it."""

    config.validate()
    _progress(progress_callback, 0, "准备开始")
    output_path = Path(output_dir)
    input_image = output_path / config.input_name
    output_image = output_path / config.output_name
    square_output_image = output_path / config.square_output_name

    images = find_tile_images(folder, config.image_patterns)
    _log(log_callback, f"Found {len(images)} tile images")
    _progress(progress_callback, 10, "已扫描切片")

    selected_images, geometry = _create_shuffled_input_with_geometry(
        images, input_image, config
    )
    _log(log_callback, f"Created shuffled puzzle: {input_image}")
    _progress(progress_callback, 25, "已生成乱序输入图")
    _log(
        log_callback,
        f"Detected tile size: {geometry.width}x{geometry.height}",
    )

    solver_config = replace(config, tile_size=geometry.solver_size)
    solver_output_image = square_output_image if geometry.is_rectangular else output_image

    if geometry.is_rectangular:
        _log(
            log_callback,
            f"Rectangular adaptive mode: solving as {geometry.solver_size}x"
            f"{geometry.solver_size} tiles",
        )

    _progress(progress_callback, -1, "算法求解中")
    solver(input_image, solver_output_image, solver_config, log_callback)
    _progress(progress_callback, 90, "算法求解完成")

    result_square_output = None
    if geometry.is_rectangular:
        _progress(progress_callback, 95, "正在恢复原始比例")
        _restore_rectangular_solution(
            square_output_image,
            output_image,
            config,
            geometry,
        )
        result_square_output = square_output_image
        _log(log_callback, f"Restored final ratio: {output_image}")

    _log(log_callback, f"Saved solution: {output_image}")
    _progress(progress_callback, 100, "完成")

    return StitchResult(
        input_image=input_image,
        output_image=output_image,
        selected_images=selected_images,
        total_tiles=len(selected_images),
        square_output_image=result_square_output,
        tile_geometry=geometry,
    )
