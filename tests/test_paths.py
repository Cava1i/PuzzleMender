from pathlib import Path

from puzzle_stitcher.paths import default_output_dir, runtime_base_dir


def test_default_output_dir_is_project_output_folder(tmp_path: Path) -> None:
    assert default_output_dir(tmp_path) == tmp_path / "output"


def test_runtime_base_dir_uses_module_folder_for_source_runs(tmp_path: Path) -> None:
    assert runtime_base_dir(tmp_path / "gui_stitch.py", frozen=False) == tmp_path


def test_runtime_base_dir_uses_exe_folder_for_frozen_runs(tmp_path: Path) -> None:
    exe_path = tmp_path / "dist" / "gaps_stitch_gui.exe"

    assert (
        runtime_base_dir(tmp_path / "gui_stitch.py", frozen=True, executable_path=exe_path)
        == exe_path.parent
    )
