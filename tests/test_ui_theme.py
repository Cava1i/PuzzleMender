from puzzle_stitcher.ui_theme import COLORS, TYPOGRAPHY, metrics, style_sheet


def test_theme_exposes_required_color_tokens() -> None:
    required_tokens = {
        "ink",
        "muted",
        "panel",
        "surface",
        "border",
        "primary",
        "primary_hover",
        "danger",
        "log_bg",
        "log_text",
    }

    assert required_tokens.issubset(COLORS)


def test_metrics_returns_stable_spacing_values() -> None:
    values = metrics()

    assert values["radius"] == 6
    assert values["control_height"] == 46
    assert values["section_gap"] == 14


def test_typography_uses_larger_readable_defaults() -> None:
    assert TYPOGRAPHY["body"] == 17
    assert TYPOGRAPHY["helper"] == 16
    assert TYPOGRAPHY["title"] == 28
    assert TYPOGRAPHY["log"] == 16


def test_style_sheet_contains_key_widget_rules() -> None:
    qss = style_sheet()

    assert "QMainWindow" in qss
    assert "QPushButton#runButton" in qss
    assert "QTextEdit#logOutput" in qss
    assert COLORS["primary"] in qss
    assert "font-size: 17px;" in qss
    assert "font-size: 16px;" in qss
