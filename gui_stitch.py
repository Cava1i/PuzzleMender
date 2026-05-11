"""PyQt GUI for the project-specific stitching workflow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtCore import QThread, Qt, pyqtSignal
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QProgressBar,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    print("请先安装 PyQt5: pip install PyQt5")
    sys.exit(1)

from puzzle_stitcher.paths import default_output_dir, runtime_base_dir
from puzzle_stitcher.gui_launch import show_main_window
from puzzle_stitcher.stitcher import (
    StitchConfig,
    StitchError,
    find_tile_images,
    infer_grid_from_tile_count,
    stitch_folder,
)
from puzzle_stitcher.ui_theme import metrics, style_sheet


class StitchThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)

    def __init__(self, folder: Path, output_dir: Path, config: StitchConfig):
        super().__init__()
        self.folder = folder
        self.output_dir = output_dir
        self.config = config

    def run(self) -> None:
        try:
            result = stitch_folder(
                self.folder,
                self.output_dir,
                self.config,
                log_callback=self.log_signal.emit,
                progress_callback=self.progress_signal.emit,
            )
            self.log_signal.emit(f"拼接成功，大图保存在:\n{result.output_image}")
            self.finished_signal.emit(str(result.output_image))
        except StitchError as exc:
            self.log_signal.emit(f"错误: {exc}")
            self.finished_signal.emit("")
        except Exception as exc:  # pragma: no cover - keeps GUI thread alive.
            self.log_signal.emit(f"发生异常: {exc}")
            self.finished_signal.emit("")


class DropLabel(QLabel):
    folder_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__("拖入切片文件夹\n支持 png / bmp，自动识别正方形或长方形")
        self.setObjectName("folderDrop")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(118)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return

        path = urls[0].toLocalFile()
        if Path(path).is_dir():
            self.folder_dropped.emit(path)
            self.setText(f"已选择文件夹\n{path}")
        else:
            self.setText("请拖入文件夹，而不是单个文件")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gaps RDP Cache 拼接工具")
        self.resize(760, 640)
        self.setMinimumSize(700, 560)
        self.setStyleSheet(style_sheet())

        self.selected_folder: Optional[Path] = None
        self.output_dir = default_output_dir(runtime_base_dir(__file__))
        self.thread: Optional[StitchThread] = None

        root = QWidget()
        root_layout = QVBoxLayout(root)
        theme_metrics = metrics()
        root_layout.setContentsMargins(
            theme_metrics["outer_margin"],
            theme_metrics["outer_margin"],
            theme_metrics["outer_margin"],
            theme_metrics["outer_margin"],
        )
        root_layout.setSpacing(theme_metrics["section_gap"])

        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_folder_panel())
        root_layout.addWidget(self._build_output_panel())
        root_layout.addWidget(self._build_settings_panel())
        root_layout.addWidget(self._build_action_panel())
        root_layout.addWidget(self._build_log_panel(), 1)

        self.setCentralWidget(root)
        self._sync_auto_grid_controls()
        self.refresh_summary()

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        title = QLabel("Gaps RDP Cache 拼接工具")
        title.setObjectName("titleLabel")
        subtitle = QLabel("整理切片、生成乱序输入图，并自动适配长方形切片")
        subtitle.setObjectName("subtitleLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return frame

    def _build_folder_panel(self) -> QFrame:
        frame = self._panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(self._section_title("输入切片"))
        header.addStretch()
        self.btn_choose = QPushButton("浏览文件夹")
        self.btn_choose.clicked.connect(self.choose_folder)
        header.addWidget(self.btn_choose)
        layout.addLayout(header)

        self.drop_label = DropLabel()
        self.drop_label.folder_dropped.connect(self.on_folder_selected)
        layout.addWidget(self.drop_label)

        self.folder_status = QLabel("尚未选择切片目录")
        self.folder_status.setObjectName("helperLabel")
        layout.addWidget(self.folder_status)
        return frame

    def _build_output_panel(self) -> QFrame:
        frame = self._panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(self._section_title("输出目录"))
        header.addStretch()
        self.btn_choose_output = QPushButton("选择输出目录")
        self.btn_choose_output.clicked.connect(self.choose_output_dir)
        header.addWidget(self.btn_choose_output)
        layout.addLayout(header)

        self.output_status = QLabel(f"默认输出: {self.output_dir}")
        self.output_status.setObjectName("helperLabel")
        layout.addWidget(self.output_status)
        return frame

    def _build_settings_panel(self) -> QFrame:
        frame = self._panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self._section_title("求解参数"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        self.input_cols = self._line_edit("28")
        self.input_rows = self._line_edit("16")
        self.input_size = self._line_edit("64")
        self.input_gens = self._line_edit("5")
        self.input_pop = self._line_edit("50")

        self.auto_grid_checkbox = QCheckBox("根据切片数量自动识别列数 / 行数")
        self.auto_grid_checkbox.setChecked(True)
        self.auto_grid_checkbox.stateChanged.connect(self.on_auto_grid_changed)
        grid.addWidget(self.auto_grid_checkbox, 0, 0, 1, 4)

        self._add_field(grid, 1, 0, "列数", self.input_cols)
        self._add_field(grid, 1, 2, "行数", self.input_rows)
        self._add_field(grid, 2, 0, "尺寸兜底 px", self.input_size)
        self._add_field(grid, 2, 2, "繁衍代数", self.input_gens)
        self._add_field(grid, 3, 0, "种群数量", self.input_pop)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)

        for field in [
            self.input_cols,
            self.input_rows,
            self.input_size,
            self.input_gens,
            self.input_pop,
        ]:
            field.textChanged.connect(self.refresh_summary)

        return frame

    def _build_action_panel(self) -> QFrame:
        frame = self._panel_frame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        summary_box = QVBoxLayout()
        summary_title = QLabel("运行摘要")
        summary_title.setObjectName("sectionTitle")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("helperLabel")
        summary_box.addWidget(summary_title)
        summary_box.addWidget(self.summary_label)

        self.btn_run = QPushButton("开始自动拼接")
        self.btn_run.setObjectName("runButton")
        self.btn_run.setMinimumWidth(180)
        self.btn_run.clicked.connect(self.run_stitch)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumWidth(220)

        layout.addLayout(summary_box, 1)
        action_box = QVBoxLayout()
        action_box.setSpacing(8)
        action_box.addWidget(self.progress_bar)
        action_box.addWidget(self.btn_run)
        layout.addLayout(action_box)
        return frame

    def _build_log_panel(self) -> QFrame:
        frame = self._panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self._section_title("运行日志"))

        self.log_output = QTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("运行后会在这里显示处理进度和错误信息")
        layout.addWidget(self.log_output, 1)
        return frame

    def _panel_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panelFrame")
        return frame

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _line_edit(self, value: str) -> QLineEdit:
        field = QLineEdit(value)
        field.setAlignment(Qt.AlignCenter)
        return field

    def _add_field(
        self,
        grid: QGridLayout,
        row: int,
        column: int,
        label_text: str,
        field: QLineEdit,
    ) -> None:
        label = QLabel(label_text)
        label.setObjectName("helperLabel")
        grid.addWidget(label, row, column)
        grid.addWidget(field, row, column + 1)

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择切片文件夹")
        if folder:
            self.on_folder_selected(folder)
            self.drop_label.setText(f"已选择文件夹\n{folder}")

    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            str(self.output_dir),
        )
        if folder:
            self.output_dir = Path(folder)
            self.output_status.setText(f"当前输出: {self.output_dir}")
            self.append_log(f"已设置输出目录: {self.output_dir}")

    def on_progress_update(self, value: int, message: str) -> None:
        if value < 0:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat(message)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(value)
            self.progress_bar.setFormat(f"{message}  %p%")

    def on_auto_grid_changed(self) -> None:
        self._sync_auto_grid_controls()
        if self.auto_grid_checkbox.isChecked() and self.selected_folder:
            self.apply_auto_grid_from_folder()
        self.refresh_summary()

    def _sync_auto_grid_controls(self) -> None:
        is_auto = self.auto_grid_checkbox.isChecked()
        self.input_cols.setEnabled(not is_auto)
        self.input_rows.setEnabled(not is_auto)

    def apply_auto_grid_from_folder(self) -> bool:
        if not self.selected_folder:
            return False

        try:
            images = find_tile_images(self.selected_folder)
            columns, rows = infer_grid_from_tile_count(len(images))
        except StitchError as exc:
            self.append_log(f"自动识别行列失败: {exc}")
            return False

        self.input_cols.setText(str(columns))
        self.input_rows.setText(str(rows))
        self.append_log(f"自动识别行列: {columns} x {rows}（{len(images)} 张切片）")
        return True

    def on_folder_selected(self, folder_path: str) -> None:
        self.selected_folder = Path(folder_path)
        self.folder_status.setText(f"当前目录: {self.selected_folder}")
        self.append_log(f"已加载工作目录: {self.selected_folder}")
        if self.auto_grid_checkbox.isChecked():
            self.apply_auto_grid_from_folder()

    def append_log(self, text: str) -> None:
        self.log_output.append(text)
        scroll_bar = self.log_output.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def refresh_summary(self) -> None:
        try:
            columns = int(self.input_cols.text())
            rows = int(self.input_rows.text())
            tile_size = int(self.input_size.text())
            generations = int(self.input_gens.text())
            population = int(self.input_pop.text())
            total = columns * rows
            mode = "自动行列" if self.auto_grid_checkbox.isChecked() else "手动行列"
            summary = (
                f"{mode}：{columns} x {rows} 网格，需 {total} 张切片；"
                f"自动识别尺寸，兜底 {tile_size}px；"
                f"{generations} 代 / {population} 种群"
            )
        except ValueError:
            summary = "参数暂未完整，请输入有效整数"
        self.summary_label.setText(summary)

    def run_stitch(self) -> None:
        if not self.selected_folder:
            self.append_log("请先选择包含切片的文件夹")
            return

        if self.auto_grid_checkbox.isChecked() and not self.apply_auto_grid_from_folder():
            return

        try:
            config = StitchConfig(
                columns=int(self.input_cols.text()),
                rows=int(self.input_rows.text()),
                tile_size=int(self.input_size.text()),
                generations=int(self.input_gens.text()),
                population=int(self.input_pop.text()),
            )
            config.validate()
        except ValueError:
            self.append_log("参数格式错误，请输入有效整数")
            return
        except StitchError as exc:
            self.append_log(f"参数错误: {exc}")
            return

        self.btn_run.setEnabled(False)
        self.btn_run.setText("正在拼接...")
        self.log_output.clear()
        self.on_progress_update(0, "准备开始")
        self.append_log(f"输出目录: {self.output_dir}")
        self.append_log("开始处理切片目录")

        self.thread = StitchThread(self.selected_folder, self.output_dir, config)
        self.thread.log_signal.connect(self.append_log)
        self.thread.progress_signal.connect(self.on_progress_update)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, path: str) -> None:
        if path:
            self.append_log("任务完成")
        self.reset_button()

    def reset_button(self) -> None:
        self.btn_run.setEnabled(True)
        self.btn_run.setText("开始自动拼接")
        self.on_progress_update(0, "就绪")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    show_main_window(window)
    sys.exit(app.exec_())
