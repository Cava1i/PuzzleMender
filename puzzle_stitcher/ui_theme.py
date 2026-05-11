"""Shared visual styling for the PyQt desktop interface."""

from __future__ import annotations

from typing import Dict


COLORS: Dict[str, str] = {
    "ink": "#17202A",
    "muted": "#68707D",
    "panel": "#FFFFFF",
    "surface": "#F4F6F8",
    "border": "#D7DEE6",
    "primary": "#116D6E",
    "primary_hover": "#0D5C5D",
    "primary_disabled": "#8EA7A8",
    "danger": "#B42318",
    "warning": "#B7791F",
    "success": "#168A4A",
    "log_bg": "#101820",
    "log_text": "#9FF0B5",
    "header_bg": "#17202A",
    "header_text": "#F8FAFC",
    "header_muted": "#B7C1CE",
}


TYPOGRAPHY: Dict[str, int] = {
    "body": 17,
    "helper": 16,
    "title": 28,
    "subtitle": 16,
    "section": 20,
    "drop": 18,
    "button": 17,
    "log": 16,
}


def metrics() -> Dict[str, int]:
    """Return stable UI sizing tokens used by the PyQt view."""

    return {
        "radius": 6,
        "control_height": 46,
        "section_gap": 14,
        "outer_margin": 18,
        "panel_padding": 16,
    }


def style_sheet() -> str:
    """Return the application-wide Qt style sheet."""

    values = metrics()
    return f"""
QMainWindow {{
    background: {COLORS["surface"]};
}}

QWidget {{
    color: {COLORS["ink"]};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: {TYPOGRAPHY["body"]}px;
}}

QFrame#headerFrame {{
    background: {COLORS["header_bg"]};
    border-radius: {values["radius"]}px;
}}

QLabel#titleLabel {{
    color: {COLORS["header_text"]};
    font-size: {TYPOGRAPHY["title"]}px;
    font-weight: 700;
}}

QLabel#subtitleLabel {{
    color: {COLORS["header_muted"]};
    font-size: {TYPOGRAPHY["subtitle"]}px;
}}

QFrame#panelFrame {{
    background: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: {values["radius"]}px;
}}

QLabel#sectionTitle {{
    color: {COLORS["ink"]};
    font-size: {TYPOGRAPHY["section"]}px;
    font-weight: 700;
}}

QLabel#helperLabel {{
    color: {COLORS["muted"]};
    font-size: {TYPOGRAPHY["helper"]}px;
}}

QLabel#folderDrop {{
    background: #F9FBFC;
    border: 1px dashed #9FB0C1;
    border-radius: {values["radius"]}px;
    color: {COLORS["muted"]};
    font-size: {TYPOGRAPHY["drop"]}px;
}}

QLineEdit {{
    min-height: {values["control_height"]}px;
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 0 10px;
    background: #FFFFFF;
    selection-background-color: {COLORS["primary"]};
}}

QLineEdit:focus {{
    border: 1px solid {COLORS["primary"]};
}}

QPushButton {{
    min-height: {values["control_height"]}px;
    border-radius: 4px;
    padding: 0 14px;
    border: 1px solid {COLORS["border"]};
    background: #FFFFFF;
    color: {COLORS["ink"]};
    font-size: {TYPOGRAPHY["button"]}px;
    font-weight: 600;
}}

QPushButton:hover {{
    background: #F5F8FA;
}}

QPushButton#runButton {{
    min-height: 54px;
    background: {COLORS["primary"]};
    border: 1px solid {COLORS["primary"]};
    color: #FFFFFF;
    font-size: {TYPOGRAPHY["button"]}px;
    font-weight: 700;
}}

QPushButton#runButton:hover {{
    background: {COLORS["primary_hover"]};
}}

QPushButton#runButton:disabled {{
    background: {COLORS["primary_disabled"]};
    border-color: {COLORS["primary_disabled"]};
}}

QTextEdit#logOutput {{
    background: {COLORS["log_bg"]};
    color: {COLORS["log_text"]};
    border: 1px solid #0B1117;
    border-radius: {values["radius"]}px;
    padding: 10px;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: {TYPOGRAPHY["log"]}px;
}}
"""
