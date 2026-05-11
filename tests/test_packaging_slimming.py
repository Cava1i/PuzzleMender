from pathlib import Path

import importlib
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_genetic_algorithm_does_not_import_plot_until_verbose_mode() -> None:
    sys.modules.pop("gaps.genetic_algorithm", None)
    sys.modules.pop("gaps.plot", None)

    importlib.import_module("gaps.genetic_algorithm")

    assert "gaps.plot" not in sys.modules


def test_build_script_uses_separate_cli_and_gui_pyinstaller_args() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_exes.ps1").read_text(
        encoding="utf-8"
    )

    assert "$cliArgs" in script
    assert "$guiArgs" in script
    assert '-PyInstallerArgs $cliArgs' in script
    assert '-PyInstallerArgs $guiArgs' in script


def test_build_script_fails_when_pyinstaller_fails() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_exes.ps1").read_text(
        encoding="utf-8"
    )

    assert "Invoke-PyInstaller" in script
    assert "$PyInstallerArgs" in script
    assert "[string[]]$Args" not in script
    assert "$LASTEXITCODE" in script
    assert "throw \"PyInstaller failed" in script


def test_build_script_allows_explicit_python_executable() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_exes.ps1").read_text(
        encoding="utf-8"
    )

    assert '[string]$Python = "python"' in script
    assert "& $Python -m pip show pathlib" in script
    assert "& $Python -m PyInstaller" in script


def test_cli_build_excludes_gui_and_plotting_dependencies() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_exes.ps1").read_text(
        encoding="utf-8"
    )

    assert '"--exclude-module", "PyQt5"' in script
    assert '"--exclude-module", "matplotlib"' in script
    assert '"--exclude-module", "tkinter"' in script


def test_build_script_does_not_collect_all_gaps_submodules() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_exes.ps1").read_text(
        encoding="utf-8"
    )

    assert '"--collect-submodules", "gaps"' not in script


def test_project_base_dependency_uses_headless_opencv() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "opencv-python-headless" in pyproject
    assert '"opencv-python>=' not in pyproject
