from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QWidget

from ui.widgets.annotations_bar import AnnotationsBar


class DepthChartMenu(QMenu):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Set project variables
        # (none)

        # Set module variables
        self.parent_chart = parent

        # Initialisation methods
        self._define_main_menu_actions()
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.addAction(self.actionShowAnnotations)
        self.addAction(self.actionDrawStraightLine)

    def _connect_signals(self) -> None:
        self.actionDrawStraightLine.triggered.connect(self._draw_straight_line)
        self.actionShowAnnotations.triggered.connect(self._show_annotations_toolbar)

    def _define_main_menu_actions(self) -> None:
        self.actionShowAnnotations = QAction("Make Annotations", self)
        self.actionDrawStraightLine = QAction("Draw straight line", self)

    def _draw_straight_line(self) -> None:
        chart = self.parent()
        chart.enter_draw_straight_line()

    def _show_annotations_toolbar(self) -> None:
        chart = self.parent_chart
        existing = getattr(chart, "annotations_bar", None)
        if existing is not None and existing.isVisible():
            existing.raise_()
            existing.activateWindow()
            return

        chart.annotations_bar = AnnotationsBar(chart)
        chart.annotations_bar.show()

    #--------Public API--------
    # No public methods yet.
