from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QWidget


class DepthMenuChart(QMenu):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Set project variables
        # (none)

        # Set module variables
        # (none)

        # Initialisation methods
        self._define_main_menu_actions()
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.addAction(self.actionDrawStraightLine)

    def _connect_signals(self) -> None:
        self.actionDrawStraightLine.triggered.connect(self._draw_straight_line)

    def _define_main_menu_actions(self) -> None:
        self.actionDrawStraightLine = QAction("Draw straight line", self)

    def _draw_straight_line(self) -> None:
        chart = self.parent()
        chart.start_draw_straight_line()

    #--------Public API--------
    # No public methods yet.
