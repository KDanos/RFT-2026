import uuid

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QCursor
from PyQt6.QtWidgets import QMenu
import pyqtgraph as pg
from pyqtgraph.graphicsItems.ROI import Handle

from units import convert_from_normalised_to_user_units, normalise_from_user_units


class RectangleAnnotation(pg.RectROI):
    def __init__(
            self,
            parent: pg.PlotWidget | None = None,
            color: QColor | str = "black",
            style: Qt.PenStyle = Qt.PenStyle.DashLine,
            position: tuple[float, float] = (0.0, 0.0),
            size: tuple[float, float] = (1.0, 1.0),
            points_are_si: bool = False,
            ) -> None:
        # Set project variables
        self.parent_chart = parent

        # Set module variables
        self.color = color
        self.style = style
        self.position = position
        self.size_si = size
        self.is_visible: bool = True
        self.pen = pg.mkPen(color=self.color, width=2, style=self.style)
        self.id = str(uuid.uuid4())

        super().__init__(
            pos=(0.0, 0.0),
            size=(1e-9, 1e-9),
            pen=self.pen,
            invertible=True,
        )

        # Initialisation methods
        self._build_ui()
        self._define_menu_actions()
        self._connect_signals()
        self.extract_units_and_quantities()
        if not points_are_si:
            self._convert_viewbox_coordinates_to_SI()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.hoverPen = pg.mkPen(color=self.color, width=3, style=self.style)

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

        self._set_handles_visibility(False)

    def _connect_signals(self) -> None:
        self.sigRegionChangeStarted.connect(self._on_region_change_started)
        self.sigRegionChangeFinished.connect(self._on_region_change_finished)
        self.actionDelete.triggered.connect(self._delete_self)
        self.actionDuplicate.triggered.connect(self._duplicate_self)

    def _convert_viewbox_coordinates_to_SI(self) -> None:
        x_si = normalise_from_user_units(
            self.x_unit, self.x_quantity_key, self.position[0],
        )
        y_si = normalise_from_user_units(
            self.y_unit, self.y_quantity_key, self.position[1],
        )
        self.position = (x_si, y_si)

        w_si = normalise_from_user_units(
            self.x_unit, self.x_quantity_key, self.size_si[0],
        )
        h_si = normalise_from_user_units(
            self.y_unit, self.y_quantity_key, self.size_si[1],
        )
        self.size_si = (w_si, h_si)

    def _cursor_over_any_handle(self) -> bool:
        scene = self.scene()
        view_widget = self.parent_chart
        if scene is None or view_widget is None:
            return False
        scene_pos = view_widget.mapToScene(view_widget.mapFromGlobal(QCursor.pos()))
        handles = set(self.getHandles())
        return any(item in handles for item in scene.items(scene_pos))

    def _define_menu_actions(self) -> None:
        self.actionDelete = QAction("Delete", self.parent_chart)
        self.actionDuplicate = QAction("Duplicate", self.parent_chart)

    def _delete_self(self) -> None:
        for rect in self.parent_chart.all_rectangles:
            if rect.id == self.id:
                self.parent_chart.all_rectangles.remove(rect)
                break

        for ann in self.parent_chart.view.annotations:
            if getattr(ann, "rect_id", None) == self.id:
                self.parent_chart.view.annotations.remove(ann)
                break

        self.parent_chart.removeItem(self)
        self.deleteLater()
        if self.parent_chart.project is not None:
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
        self._set_handles_visibility(False)

    def _install_handle_hover_guard(self, handle: Handle) -> None:
        def hoverEvent(ev) -> None:
            Handle.hoverEvent(handle, ev)
            if ev.isExit():
                QTimer.singleShot(0, self._hide_handles_if_idle)
            else:
                self._set_handles_visibility(True)

        handle.hoverEvent = hoverEvent

    def _on_position_changed(self) -> None:
        pos = self.pos()
        size = self.size()
        self.position = (float(pos.x()), float(pos.y()))
        self.size_si = (float(size.x()), float(size.y()))
        self._convert_viewbox_coordinates_to_SI()

        for ann in self.parent_chart.view.annotations:
            if getattr(ann, "rect_id", None) == self.id:
                ann.pos_si = self.position
                ann.size_si = self.size_si
                break

        if self.parent_chart.project is not None:
            self.parent_chart.project.mark_modified()

    def _on_region_change_finished(self, _roi: object) -> None:
        self._on_position_changed()
        QTimer.singleShot(0, self._hide_handles_if_idle)

    def _on_region_change_started(self, _roi: object) -> None:
        self._set_handles_visibility(True)

    def _set_handles_visibility(self, visible: bool) -> None:
        for handle in self.getHandles():
            handle.setVisible(visible)

    #--------Public API--------

    def build_menu(self) -> QMenu:
        menu = QMenu(self.parent_chart)
        menu.addAction(self.actionDuplicate)
        menu.addAction(self.actionDelete)
        return menu

    def extract_units_and_quantities(self) -> None:
        parent = self.parent_chart
        self.x_quantity_key = parent.x_quantity_key
        self.y_quantity_key = parent.y_quantity_key
        self.x_unit = parent.x_unit
        self.y_unit = parent.y_unit

    def refresh_geometry(self) -> None:
        x = convert_from_normalised_to_user_units(
            self.x_unit, self.x_quantity_key, self.position[0],
        )
        y = convert_from_normalised_to_user_units(
            self.y_unit, self.y_quantity_key, self.position[1],
        )
        w = convert_from_normalised_to_user_units(
            self.x_unit, self.x_quantity_key, self.size_si[0],
        )
        h = convert_from_normalised_to_user_units(
            self.y_unit, self.y_quantity_key, self.size_si[1],
        )
        # Avoid sigRegionChangeFinished during programmatic layout (project may be unset).
        self.blockSignals(True)
        try:
            self.setPos((x, y))
            self.setSize((w, h))
        finally:
            self.blockSignals(False)

    def setMouseHover(self, hover: bool) -> None:
        super().setMouseHover(hover)
        if hover:
            self._set_handles_visibility(True)
        else:
            QTimer.singleShot(0, self._hide_handles_if_idle)
