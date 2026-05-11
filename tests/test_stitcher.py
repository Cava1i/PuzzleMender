from pathlib import Path

import pytest
from PIL import Image

from puzzle_stitcher.stitcher import (
    StitchConfig,
    StitchError,
    create_shuffled_input,
    find_tile_images,
    infer_grid_from_tile_count,
    stitch_folder,
)


def _make_tile(path: Path, color: tuple[int, int, int], size: int = 8) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (size, size), color).save(path)


def _make_rect_tile(
    path: Path,
    color: tuple[int, int, int],
    size: tuple[int, int] = (10, 6),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def test_find_tile_images_supports_png_and_bmp(tmp_path: Path) -> None:
    tiles_dir = tmp_path / "tiles"
    _make_tile(tiles_dir / "b.png", (255, 0, 0))
    _make_tile(tiles_dir / "a.bmp", (0, 255, 0))
    (tiles_dir / "ignored.txt").write_text("not an image", encoding="utf-8")

    images = find_tile_images(tiles_dir)

    assert [image.name for image in images] == ["a.bmp", "b.png"]


def test_find_tile_images_rejects_missing_folder(tmp_path: Path) -> None:
    with pytest.raises(StitchError, match="does not exist"):
        find_tile_images(tmp_path / "missing")


def test_stitch_config_defaults_to_quick_solver_settings() -> None:
    config = StitchConfig()

    assert config.generations == 5
    assert config.population == 50


def test_stitch_config_rejects_single_generation_runs() -> None:
    config = StitchConfig(generations=1)

    with pytest.raises(StitchError, match="generations must be at least 2"):
        config.validate()


@pytest.mark.parametrize(
    ("tile_count", "expected"),
    [
        (500, (25, 20)),
        (448, (28, 16)),
        (4, (2, 2)),
        (7, (7, 1)),
    ],
)
def test_infer_grid_from_tile_count_prefers_landscape_near_square(
    tile_count: int,
    expected: tuple[int, int],
) -> None:
    assert infer_grid_from_tile_count(tile_count) == expected


def test_infer_grid_from_tile_count_rejects_empty_counts() -> None:
    with pytest.raises(StitchError, match="positive"):
        infer_grid_from_tile_count(0)


def test_create_shuffled_input_requires_enough_tiles(tmp_path: Path) -> None:
    tiles = []
    for index in range(3):
        path = tmp_path / f"tile_{index}.png"
        _make_tile(path, (index, index, index))
        tiles.append(path)

    config = StitchConfig(columns=2, rows=2, tile_size=8)

    with pytest.raises(StitchError, match="Need 4 tiles"):
        create_shuffled_input(tiles, tmp_path / "input.png", config)


def test_create_shuffled_input_rejects_mixed_tile_dimensions(tmp_path: Path) -> None:
    tiles = []
    for index in range(4):
        path = tmp_path / f"tile_{index}.png"
        _make_tile(path, (index, index, index), size=10 if index == 2 else 8)
        tiles.append(path)

    config = StitchConfig(columns=2, rows=2, tile_size=8)

    with pytest.raises(StitchError, match="same dimensions"):
        create_shuffled_input(tiles, tmp_path / "input.png", config)


def test_create_shuffled_input_resizes_rectangular_tiles_to_square(
    tmp_path: Path,
) -> None:
    tiles = []
    for index in range(4):
        path = tmp_path / f"tile_{index}.png"
        _make_rect_tile(path, (index, index, index), size=(10, 6))
        tiles.append(path)

    config = StitchConfig(columns=2, rows=2, tile_size=8, seed=123)
    create_shuffled_input(tiles, tmp_path / "input.png", config)

    with Image.open(tmp_path / "input.png") as image:
        assert image.size == (20, 20)


def test_stitch_folder_creates_default_outputs_and_calls_solver(tmp_path: Path) -> None:
    tiles_dir = tmp_path / "tiles"
    for index, color in enumerate(
        [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    ):
        _make_tile(tiles_dir / f"tile_{index}.png", color)

    output_dir = tmp_path / "out"
    config = StitchConfig(columns=2, rows=2, tile_size=8, seed=123)
    calls = {}
    logs = []

    def fake_solver(
        puzzle_path: Path,
        solution_path: Path,
        solver_config: StitchConfig,
        log_callback=None,
    ) -> Path:
        calls["puzzle_path"] = puzzle_path
        calls["solution_path"] = solution_path
        calls["config"] = solver_config
        if log_callback:
            log_callback("fake solver called")
        Image.open(puzzle_path).save(solution_path)
        return solution_path

    result = stitch_folder(
        tiles_dir,
        output_dir,
        config,
        solver=fake_solver,
        log_callback=logs.append,
    )

    assert result.input_image == output_dir / "gaps_input_shuffled.png"
    assert result.output_image == output_dir / "gaps_solved_final.png"
    assert result.input_image.exists()
    assert result.output_image.exists()
    assert result.total_tiles == 4
    assert len(result.selected_images) == 4
    assert calls["puzzle_path"] == result.input_image
    assert calls["solution_path"] == result.output_image
    assert calls["config"] == config
    assert "fake solver called" in logs


def test_stitch_folder_reports_staged_progress(tmp_path: Path) -> None:
    tiles_dir = tmp_path / "tiles"
    for index, color in enumerate(
        [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    ):
        _make_tile(tiles_dir / f"tile_{index}.png", color)

    output_dir = tmp_path / "out"
    config = StitchConfig(columns=2, rows=2, tile_size=8, seed=123)
    progress_events = []

    def fake_solver(
        puzzle_path: Path,
        solution_path: Path,
        solver_config: StitchConfig,
        log_callback=None,
    ) -> Path:
        Image.open(puzzle_path).save(solution_path)
        return solution_path

    stitch_folder(
        tiles_dir,
        output_dir,
        config,
        solver=fake_solver,
        progress_callback=lambda value, message: progress_events.append(
            (value, message)
        ),
    )

    values = [value for value, _message in progress_events]
    assert values == [0, 10, 25, -1, 90, 100]
    assert progress_events[-1][1] == "完成"


def test_stitch_folder_restores_rectangular_solution_to_original_ratio(
    tmp_path: Path,
) -> None:
    tiles_dir = tmp_path / "tiles"
    for index, color in enumerate(
        [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    ):
        _make_rect_tile(tiles_dir / f"tile_{index}.png", color, size=(10, 6))

    output_dir = tmp_path / "out"
    config = StitchConfig(columns=2, rows=2, tile_size=8, seed=123)
    calls = {}

    def fake_solver(
        puzzle_path: Path,
        solution_path: Path,
        solver_config: StitchConfig,
        log_callback=None,
    ) -> Path:
        calls["puzzle_path"] = puzzle_path
        calls["solution_path"] = solution_path
        calls["config"] = solver_config
        with Image.open(puzzle_path) as puzzle:
            assert puzzle.size == (20, 20)
            puzzle.save(solution_path)
        return solution_path

    result = stitch_folder(tiles_dir, output_dir, config, solver=fake_solver)

    assert result.square_output_image == output_dir / "gaps_solved_square.png"
    assert calls["solution_path"] == result.square_output_image
    assert calls["config"].tile_size == 10
    with Image.open(result.output_image) as final_image:
        assert final_image.size == (20, 12)
