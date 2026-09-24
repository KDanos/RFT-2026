from PyQt6.QtCore import QEvent, QPoint, QSize, Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QToolButton, QWidget

from ui import app_icon


class AnnotationsBar(QDialog):
    ICON_SIZE = QSize(28, 28)
    BTN_SIZE = QSize(32, 32)
    _FLAT_STYLE = """
        QToolButton {
            border: none;
            background: transparent;
        }
        QToolButton:hover {
            background: rgba(0, 0, 0, 10);
        }
        QToolButton:checked {
            background: transparent;
            border: 2px solid #1f77b4;
            border-radius: 4px;
        }
        QToolButton:checked:hover {
            background: rgba(0, 0, 0, 10);
        }
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint,
        )

        # Set project variables
        # (none)

        # Set module variables
        self.all_buttons: list[QToolButton] = []
        self.drag_offset: QPoint | None = None

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)

        self._define_buttons()
        self._position_self()

    def _connect_signals(self) -> None:
        self.line_btn.toggled.connect(self._on_line_btn_toggled)
        self.arrow_btn.toggled.connect(self._on_arrow_btn_toggled)
        self.text_btn.toggled.connect(self._on_text_btn_toggled)
        self.square_btn.toggled.connect(self._on_square_btn_toggled)
        self.circle_btn.toggled.connect(self._on_circle_btn_toggled)
        self.close_btn.clicked.connect(self._on_close)

    def _define_buttons(self) -> None:
        self.grip_box = QToolButton(self)
        self.grip_box.setIcon(app_icon("mdi.drag-vertical"))
        self.grip_box.setIconSize(self.ICON_SIZE)
        self.grip_box.setFixedSize(self.BTN_SIZE)
        self.grip_box.setStyleSheet(self._FLAT_STYLE)
        self.grip_box.setCursor(Qt.CursorShape.SizeAllCursor)
        self.grip_box.installEventFilter(self)
        self.main_layout.addWidget(self.grip_box)
        self.main_layout.addWidget(self._v_sep())

        self.line_btn = QToolButton(self)
        self.line_btn.setIcon(app_icon("ph.line-segment-thin"))
        self.all_buttons.append(self.line_btn)

        self.arrow_btn = QToolButton(self)
        self.arrow_btn.setIcon(app_icon("mdi6.arrow-bottom-left-thin"))
        self.all_buttons.append(self.arrow_btn)

        self.text_btn = QToolButton(self)
        self.text_btn.setIcon(app_icon("mdi6.text-box-outline"))
        self.all_buttons.append(self.text_btn)

        self.square_btn = QToolButton(self)
        self.square_btn.setIcon(app_icon("ph.square-thin"))
        self.all_buttons.append(self.square_btn)

        self.circle_btn = QToolButton(self)
        self.circle_btn.setIcon(app_icon("ph.circle-thin"))
        self.all_buttons.append(self.circle_btn)

        for btn in self.all_buttons:
            btn.setIconSize(self.ICON_SIZE)
            btn.setFixedSize(self.BTN_SIZE)
            btn.setAutoRaise(True)
            btn.setCheckable(True)
            btn.setStyleSheet(self._FLAT_STYLE)
            self.main_layout.addWidget(btn)

        self.main_layout.addWidget(self._v_sep())

        self.close_btn = QToolButton(self)
        self.close_btn.setIcon(app_icon("mdi.window-close"))
        self.close_btn.setIconSize(self.ICON_SIZE)
        self.close_btn.setFixedSize(self.BTN_SIZE)
        self.close_btn.setStyleSheet(self._FLAT_STYLE)
        self.main_layout.addWidget(self.close_btn)

    def _on_arrow_btn_toggled(self, checked: bool) -> None:
        if checked:
            self._uncheck_other_tools(self.arrow_btn)
            self.parent().enter_draw_arrow()

    def _on_circle_btn_toggled(self, checked: bool) -> None:
        if checked:
            self._uncheck_other_tools(self.circle_btn)
            self.parent().enter_draw_circle()

    def _on_close(self) -> None:
        chart = self.parent()
        if chart is not None:
            chart.annotations_bar = None
        self.close()

    def _on_line_btn_toggled(self, checked: bool) -> None:
        if checked:
            self._uncheck_other_tools(self.line_btn)
            self.parent().enter_draw_straight_line()

    def _on_square_btn_toggled(self, checked: bool) -> None:
        if checked:
            self._uncheck_other_tools(self.square_btn)
            self.parent().enter_draw_square()

    def _on_text_btn_toggled(self, checked: bool) -> None:
        if checked:
            self._uncheck_other_tools(self.text_btn)
            self.parent().enter_add_text()

    def _position_self(self) -> None:
        anchor = self.parent()
        assert anchor is not None
        self.adjustSize()
        gap = 8
        top_left = anchor.mapToGlobal(anchor.rect().topLeft())
        x = top_left.x() + (anchor.width() - self.width()) // 2
        y = top_left.y() - self.height() - gap
        self.move(x, y)

    def _uncheck_other_tools(self, active: QToolButton) -> None:
        for btn in self.all_buttons:
            if btn is not active and btn.isChecked():
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)

    def _v_sep(self) -> QFrame:
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    #--------Public API--------

    def clear_tool_selection(self) -> None:
        for btn in self.all_buttons:
            btn.setChecked(False)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.grip_box:
            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self.drag_offset = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                return True

            if (
                event.type() == QEvent.Type.MouseMove
                and self.drag_offset is not None
                and event.buttons() & Qt.MouseButton.LeftButton
            ):
                self.move(event.globalPosition().toPoint() - self.drag_offset)
                return True

            if event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_offset = None
                return True

        return super().eventFilter(obj, event)
