from puzzle_stitcher.gui_launch import show_main_window


class FakeWindow:
    def __init__(self) -> None:
        self.maximized = False

    def showMaximized(self) -> None:
        self.maximized = True


def test_show_main_window_uses_maximized_display() -> None:
    window = FakeWindow()

    show_main_window(window)

    assert window.maximized is True
