from pathlib import Path

import run_gaps_stitch
from puzzle_stitcher.stitcher import StitchConfig, StitchResult


def _fake_result(output_dir_arg) -> StitchResult:
    return StitchResult(
        input_image=Path(output_dir_arg) / "gaps_input_shuffled.png",
        output_image=Path(output_dir_arg) / "gaps_solved_final.png",
        selected_images=(),
        total_tiles=0,
    )


def test_main_passes_cli_arguments_to_stitch_service(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tiles_dir = tmp_path / "tiles"
    output_dir = tmp_path / "out"
    calls = {}

    def fake_stitch_folder(
        folder,
        output_dir_arg,
        config,
        log_callback=None,
        progress_callback=None,
    ):
        calls["folder"] = Path(folder)
        calls["output_dir"] = Path(output_dir_arg)
        calls["config"] = config
        if log_callback:
            log_callback("called")
        if progress_callback:
            progress_callback(100, "done")
        return _fake_result(output_dir_arg)

    monkeypatch.setattr(run_gaps_stitch, "stitch_folder", fake_stitch_folder)

    exit_code = run_gaps_stitch.main(
        [
            "--folder",
            str(tiles_dir),
            "--output-dir",
            str(output_dir),
            "--manual-grid",
            "--columns",
            "3",
            "--rows",
            "2",
            "--size",
            "8",
            "--generations",
            "5",
            "--population",
            "9",
            "--seed",
            "123",
        ]
    )

    assert exit_code == 0
    assert calls["folder"] == tiles_dir
    assert calls["output_dir"] == output_dir
    assert calls["config"] == StitchConfig(
        columns=3,
        rows=2,
        tile_size=8,
        generations=5,
        population=9,
        seed=123,
    )


def test_main_auto_grid_uses_all_tile_images(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tiles_dir = tmp_path / "tiles"
    tiles_dir.mkdir()
    for index in range(6):
        (tiles_dir / f"tile_{index}.png").write_text("x", encoding="utf-8")

    output_dir = tmp_path / "out"
    calls = {}

    def fake_stitch_folder(
        folder,
        output_dir_arg,
        config,
        log_callback=None,
        progress_callback=None,
    ):
        calls["folder"] = Path(folder)
        calls["output_dir"] = Path(output_dir_arg)
        calls["config"] = config
        return _fake_result(output_dir_arg)

    monkeypatch.setattr(run_gaps_stitch, "stitch_folder", fake_stitch_folder)

    exit_code = run_gaps_stitch.main(
        [
            "--folder",
            str(tiles_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert calls["config"].columns == 3
    assert calls["config"].rows == 2


def test_main_uses_environment_defaults(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tiles_dir = tmp_path / "env_tiles"
    output_dir = tmp_path / "env_out"
    calls = {}

    monkeypatch.setenv("GAPS_STITCH_INPUT_DIR", str(tiles_dir))
    monkeypatch.setenv("GAPS_STITCH_OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("GAPS_STITCH_AUTO_GRID", "0")
    monkeypatch.setenv("GAPS_STITCH_COLUMNS", "4")
    monkeypatch.setenv("GAPS_STITCH_ROWS", "3")
    monkeypatch.setenv("GAPS_STITCH_SIZE", "12")
    monkeypatch.setenv("GAPS_STITCH_GENERATIONS", "7")
    monkeypatch.setenv("GAPS_STITCH_POPULATION", "11")
    monkeypatch.setenv("GAPS_STITCH_SEED", "99")

    def fake_stitch_folder(
        folder,
        output_dir_arg,
        config,
        log_callback=None,
        progress_callback=None,
    ):
        calls["folder"] = Path(folder)
        calls["output_dir"] = Path(output_dir_arg)
        calls["config"] = config
        return _fake_result(output_dir_arg)

    monkeypatch.setattr(run_gaps_stitch, "stitch_folder", fake_stitch_folder)

    exit_code = run_gaps_stitch.main([])

    assert exit_code == 0
    assert calls["folder"] == tiles_dir
    assert calls["output_dir"] == output_dir
    assert calls["config"] == StitchConfig(
        columns=4,
        rows=3,
        tile_size=12,
        generations=7,
        population=11,
        seed=99,
    )


def test_format_progress_draws_cli_progress_bar() -> None:
    assert (
        run_gaps_stitch.format_progress(25, "已生成乱序输入图", width=10)
        == "[##--------]  25% 已生成乱序输入图"
    )


def test_format_progress_reports_indeterminate_solver_stage() -> None:
    assert run_gaps_stitch.format_progress(-1, "算法求解中", width=10) == (
        "[处理中] 算法求解中"
    )


def test_parser_documents_automatic_rectangular_adaptive_mode() -> None:
    parser = run_gaps_stitch.build_parser(
        default_folder=Path("tiles"),
        default_output_path=Path("output"),
        default_auto_grid=True,
    )

    assert "Rectangular adaptive mode is automatic" in parser.format_help()
