"""Filesystem path helpers shared by project entry points."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union


def default_output_dir(project_dir: Union[Path, str]) -> Path:
    """Return the default output folder for generated stitching artifacts."""

    return Path(project_dir) / "output"


def runtime_base_dir(
    module_file: Union[Path, str],
    frozen: Optional[bool] = None,
    executable_path: Optional[Union[Path, str]] = None,
) -> Path:
    """Return the directory where runtime outputs should live."""

    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if is_frozen:
        executable = Path(executable_path or sys.executable)
        return executable.resolve().parent
    return Path(module_file).resolve().parent
