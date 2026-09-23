import uuid

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QCursor
from PyQt6.QtWidgets import QMenu
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ROI import Handle

from units import convert_from_normalised_to_user_units, normalise_from_user_units


class StraightLine(pg.LineSegmentROI):
    def __init__(
            self,
            parent: pg.PlotWidget | None = None,
            color: QColor | str = "black",
            style: Qt.PenStyle = Qt.PenStyle.DashLine,
            starting_point: tuple[float, float] | None = None,
            end_point: tuple[float, float] | None = None,
            points_are_si: bool = False,
            ) -> None:
        # Set project variables
        self.parent_chart = parent

        # Set module variables
        self.color = color
        self.style = style
        self.starting_point = starting_point
        self.end_point = end_point
        self.is_visible: bool = True
        self.pen = pg.mkPen(color=self.color, width=2, style=self.style)
        self.id = str(uuid.uuid4())

        super().__init__(
            positions=((0.0, 0.0), (0.0, 0.0)),
            pen=self.pen,
        )

        # Initialisation methods
        self._build_ui()
        self._define_menu_actions()
        self._connect_signals()
        self.extract_units_and_quantities()
        if not points_are_si:
            self._convert_viewbox_cordinates_to_SI()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.hoverPen = pg.mkPen(color=self.color, width=4, style=self.style)

        handle_pen = pg.mkPen(color=self.color, width=2)
        self.handlePen = handle_pen
        self.handleHoverPen = handle_pen
        for handle in self.getHandles():
            handle.pen = handle_pen
            handle.hoverPen = handle_pen
            handle.currentPen = handle_pen
            handle.sides = 12
            handle.startAng = 0.0
            handle.buildPath()
            handle._shape = None
            handle.update()
            self._install_handle_hover_guard(handle)

        self._set_handles_visible(False)

    def _connect_signals(self) -> None:
        self.sigRegionChangeStarted.connect(self._on_region_change_started)
        self.sigRegionChangeFinished.connect(self._on_region_change_finished)
        self.actionConvertLineToFluid.triggered.connect(self._convert_line_to_fluid)
        self.actionDuplicateLine.triggered.connect(self._duplicate_self)
        self.actionDeleteLine.triggered.connect(self._delete_self)

    def _convert_line_to_fluid(self) -> None:
        pass

    def _convert_viewbox_cordinates_to_SI(self) -> None:
        x_SI = normalise_from_user_units(
            self.x_unit,
            self.x_quantity_key,
            self.starting_point[0],
        )
        y_SI = normalise_from_user_units(
            self.y_unit,
            self.y_quantity_key,
            self.starting_point[1],
        )
        self.starting_point = (x_SI, y_SI)

        x_SI = normalise_from_user_units(
            self.x_unit,
            self.x_quantity_key,
            self.end_point[0],
        )
        y_SI = normalise_from_user_units(
            self.y_unit,
            self.y_quantity_key,
            self.end_point[1],
        )
        self.end_point = (x_SI, y_SI)

    def _cursor_over_any_handle(self) -> bool:
        scene = self.scene()
        view_widget = self.parent_chart
        if scene is None or view_widget is None:
            return False
        scene_pos = view_widget.mapToScene(view_widget.mapFromGlobal(QCursor.pos()))
        handles = set(self.getHandles())
        return any(item in handles for item in scene.items(scene_pos))

    def _define_menu_actions(self) -> None:
        self.actionConvertLineToFluid = QAction("Convert to Fluid", self)
        self.actionDuplicateLine = QAction("Duplicate", self)
        self.actionDeleteLine = QAction("Delete", self)

    def _delete_self(self) -> None:
        for line in self.parent_chart.all_lines:
            if line.id == self.id:
                self.parent_chart.all_lines.remove(line)
                break

        for line in self.parent_chart.view.annotations:
            if line.line_id == self.id:
                self.parent_chart.view.annotations.remove(line)
                break

        self.parent_chart.removeItem(self)
        self.deleteLater()
        self.parent_chart.project.mark_modified()

    def _duplicate_self(self) -> None:
        pass

    def _handles_drag_active(self) -> bool:
        return any(handle.isMoving for handle in self.getHandles())

    def _hide_handles_if_idle(self) -> None:
        if self._handles_drag_active() or self.mouseHovering:
            return
        if self._cursor_over_any_handle():
            return
        self._set_handles_visible(False)

    def _install_handle_hover_guard(self, handle: Handle) -> None:
        def hoverEvent(ev) -> None:
            Handle.hoverEvent(handle, ev)
            if ev.isExit():
                QTimer.singleShot(0, self._hide_handles_if_idle)
            else:
                self._set_handles_visible(True)

        handle.hoverEvent = hoverEvent

    def _on_position_changed(self) -> None:
        p0, p1 = self.listPoints()
        p0 = self.mapToView(p0)
        p1 = self.mapToView(p1)
        self.starting_point = float(p0.x()), float(p0.y())
        self.end_point = float(p1.x()), float(p1.y())

        self._convert_viewbox_cordinates_to_SI()
        for line in self.parent_chart.view.annotations:
            if self.id == line.line_id:
                line.start_si = self.starting_point
                line.end_si = self.end_point
                break

        self.parent_chart.project.mark_modified()

    def _on_region_change_finished(self, _roi: object) -> None:
        self._on_position_changed()
        QTimer.singleShot(0, self._hide_handles_if_idle)

    def _on_region_change_started(self, _roi: object) -> None:
        self._set_handles_visible(True)

    def _set_handles_visible(self, visible: bool) -> None:
        for handle in self.getHandles():
            handle.setVisible(visible)

    #--------Public API--------

    def build_menu(self) -> QMenu:
        menu = QMenu(self.parent_chart)
        menu.addAction(self.actionConvertLineToFluid)
        menu.addAction(self.actionDuplicateLine)
        menu.addAction(self.actionDeleteLine)
        return menu

    def extract_units_and_quantities(self) -> None:
        parent = self.parent_chart
        self.x_quantity_key = parent.x_quantity_key
        self.y_quantity_key = parent.y_quantity_key
        self.x_unit = parent.x_unit
        self.y_unit = parent.y_unit

    def refresh_geometry(self) -> None:
        x0 = convert_from_normalised_to_user_units(
            self.x_unit, self.x_quantity_key, self.starting_point[0]
        )
        y0 = convert_from_normalised_to_user_units(
            self.y_unit, self.y_quantity_key, self.starting_point[1]
        )
        x1 = convert_from_normalised_to_user_units(
            self.x_unit, self.x_quantity_key, self.end_point[0]
        )
        y1 = convert_from_normalised_to_user_units(
            self.y_unit, self.y_quantity_key, self.end_point[1]
        )

        handles = self.getHandles()
        self.movePoint(handles[0], (x0, y0), finish=False)
        self.movePoint(handles[1], (x1, y1), finish=False)

    def setMouseHover(self, hover: bool) -> None:
        super().setMouseHover(hover)
        if hover:
            self._set_handles_visible(True)
        else:
            QTimer.singleShot(0, self._hide_handles_if_idle)
