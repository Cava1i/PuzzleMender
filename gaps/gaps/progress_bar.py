import sys
import os


def print_progress(
    iteration: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 50,
    fill: str = "#",
    print_end: str = "\r",
) -> None:
    """Call in a loop to create terminal progress bar."""

    percent = f"{100 * (iteration / float(total)):.{decimals}f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)
