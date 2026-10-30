from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QMenu, QMessageBox
import pyqtgraph as pg

from project import AnalysisObject, AnalysisView, ProjectDataManager, StraightLineAnnotation
from ui.main_window.project_signals import ProjectSignals
from units import convert_from_normalised_to_user_units, normalise_from_user_units

if TYPE_CHECKING:
    from ui.analysis_view import AnalysisViewWidget
    from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart
    from ui.depth_gradient_chart.excess_pressure_chart import ExcessPressureChart


class LineAnnot(pg.LineSegmentROI):
    # Inherited variables

    # Project
    # None

    # Module
    # None

    # Initialisation Methods
    # None

    def __init__(
        self,
        parent: pg.PlotWidget,
        signals: ProjectSignals,
        starting_point: tuple[float, float] | None = None,
        end_point: tuple[float, float] | None = None,
        points_are_si: bool = False,
        color: QColor | str = "black",
        style: Qt.PenStyle = Qt.PenStyle.DashLine,
        ) -> None:
        # Locals only until LineSegmentROI is constructed (no self.* before super)
        pen = pg.mkPen(color=color, width=2, style=style)

        super().__init__(
            positions=((0.0, 0.0), (0.0, 0.0)),
            pen=pen,
            )

        # Set project variables
        self.parent_chart: DepthGradientChart | ExcessPressureChart = parent
        self.project: ProjectDataManager = self.parent_chart.project
        self.view: AnalysisView = self.parent_chart.view
        self.analysis: AnalysisObject = self.view.analysis_object
        self.signals: ProjectSignals = signals

        # Set module variables
        self.color: QColor | str = color
        self.style: Qt.PenStyle = style
        self.pen: object = pen
        self.starting_point: tuple[float, float] | None = starting_point
        self.end_point: tuple[float, float] | None = end_point
        self.is_visible: bool = True
        self.id: str = str(uuid.uuid4())
        self.syncing_peer: bool = False
        self.is_mirrored: bool = False
        self.parent_id: str = self.parent_chart.chart_id

        from ui.analysis_view import AnalysisViewWidget
        w = self.parent_chart
        while w is not None and not isinstance(w, AnalysisViewWidget):
            w = w.parent()
        self.view_widget: AnalysisViewWidget | None = w

        # Initialisation methods
        self._build_ui()
        self._set_handle_pen_options()
        self._define_menu_actions()
        self._connect_signals()
        self.extract_units_and_quantities()
        if not points_are_si:
            self._convert_viewbox_cordinates_to_SI()

    #--------Private UI--------

    def _apply_si_endpoints_and_refresh(
        self,
        starting_point: tuple[float, float],
        end_point: tuple[float, float],
        ) -> None:
        self.starting_point = starting_point
        self.end_point = end_point
        self.extract_units_and_quantities()
        self.refresh_geometry()

    def _build_ui(self) -> None:
        self.hoverPen = pg.mkPen(self.pen)
        self.hoverPen.setWidth(4)

    def _connect_signals(self) -> None:
        # Line Movement
        self.sigRegionChangeStarted.connect(self._on_region_change_started)
        self.sigRegionChanged.connect(self._on_region_changing)
        self.sigRegionChangeFinished.connect(self._on_region_change_finished)

        # Menu Actions
        self.actionConvertLineToFluid.triggered.connect(self._convert_line_to_fluid)
        self.actionMirrorLine.triggered.connect(self._mirror_line_annotation)
        self.actionDuplicateLine.triggered.connect(self._duplicate_self)
        self.actionDeleteLine.triggered.connect(self.delete_self)

    def _convert_line_to_fluid(self) -> None:
        from ui.analysis_view.new_fluid_dialog import NewFluidDialog

        if self.view_widget is not None and self.view_widget.new_fluid_dialog:
            QMessageBox.critical(
                self.parent_chart,
                "New Fluid Dialog Already Open",
                """An instacne of a New Fluid Dialog Window is already open for this view. 
                \nPLease close that one to proceed.""",
                )
            return

        gradient = self.calculate_fluid_gradient_si()
        y_intercept = self.calculate_y_intercept_si()

        dlg = NewFluidDialog(
            self.parent_chart,
            self.project,
            self.view,
            signals=self.signals,
            pressure_gradient_si=gradient,
            zero_pressure_depth_si=y_intercept,
            base_line=self,
            )
        if self.view_widget is not None:
            self.view_widget.new_fluid_dialog = dlg
            dlg.finished.connect(
                lambda: setattr(self.view_widget, "new_fluid_dialog", None)
                )
        dlg.show()

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

    def _define_menu_actions(self) -> None:
        self.actionConvertLineToFluid = QAction("Convert to Fluid", self)
        self.actionDuplicateLine = QAction("Duplicate", self)
        if self.parent_id == "pressure_plot":
            text = "Mirror on Excess Pressure Plot"
        else:
            text = "Mirror on Pressure Plot"
        self.actionMirrorLine = QAction(text, self)
        self.actionDeleteLine = QAction("Delete", self)

    def _duplicate_self(self) -> None:
        vb = self.parent_chart.getViewBox()

        z_min, z_max = vb.viewRange()[1]
        dz = z_max - z_min
        shift = 0.05 * dz
        shift_si = normalise_from_user_units(self.y_unit, "length", shift)

        x_start, y_start = self.starting_point
        x_end, y_end = self.end_point
        starting_point = (x_start, y_start + shift_si)
        end_point = (x_end, y_end + shift_si)

        self.parent_chart.add_straight_line_annotation(
            starting_point,
            end_point,
            points_are_si=True,
            )

    def _find_peer_line_by_id(self) -> LineAnnot | None:
        """For mirrored line annotations that share self.id."""
        other = self._other_depth_chart()
        if other is None:
            return None
        return next((ln for ln in other.all_lines if ln.id == self.id), None)

    def _mirror_line_annotation(self) -> None:
        # Exit if the line is already mirrored — menu does not offer Mirror then
        if self.is_mirrored:
            return

        other = self._other_depth_chart()
        if other is None:
            return

        if self.parent_id not in ["pressure_plot", "xs_pressure_plot"]:
            return
        if self.parent_id == "pressure_plot":
            p_start, z_start = self.starting_point
            p_end, z_end = self.end_point
            xs_start = other.convert_pressure_to_xs_pressure(p_start, z_start)
            xs_end = other.convert_pressure_to_xs_pressure(p_end, z_end)
            starting_point = (xs_start, z_start)
            end_point = (xs_end, z_end)
        elif self.parent_id == "xs_pressure_plot":
            xs_start, z_start = self.starting_point
            xs_end, z_end = self.end_point
            p_start = self.parent_chart.convert_xs_pressure_to_pressure(
                xs_start, z_start,
                )
            p_end = self.parent_chart.convert_xs_pressure_to_pressure(
                xs_end, z_end,
                )
            starting_point = (p_start, z_start)
            end_point = (p_end, z_end)
        other.add_straight_line_annotation(
            starting_point,
            end_point,
            points_are_si=True,
            is_mirrored=True,
            uuid=self.id,
            )

        # Ensure the line is not mirrorable again and linked to its peer
        self.is_mirrored = True

    def _on_position_changed(self) -> None:
        """Convert the new position from ROI coordinates to view coordinates."""
        p0, p1 = self.listPoints()
        p0 = self.mapToView(p0)
        p1 = self.mapToView(p1)
        self.starting_point = float(p0.x()), float(p0.y())
        self.end_point = float(p1.x()), float(p1.y())

        self._convert_viewbox_cordinates_to_SI()
        for line in self.parent_chart.view.annotations:
            if (
                isinstance(line, StraightLineAnnotation)
                and self.id == line.line_id
                and line.chart_id == self.parent_id
                ):
                line.start_si = self.starting_point
                line.end_si = self.end_point
                break

        self.parent_chart.project.mark_modified()

    def _on_region_change_finished(self, _roi: object) -> None:
        self._on_position_changed()
        self._set_handle_pen_options()
        # Fallback if mid-drag sync did not run
        self._sync_peer_line()

    def _on_region_change_started(self, _roi: object) -> None:
        self._set_handle_pen_options()

    def _on_region_changing(self, _roi: object) -> None:
        if not self.is_mirrored or self.syncing_peer:
            return

        p0, p1 = self.listPoints()
        if self.mapToView(p0) is None or self.mapToView(p1) is None:
            return
        self._on_position_changed()

        self._sync_peer_line()

    def _other_depth_chart(self) -> DepthGradientChart | ExcessPressureChart | None:
        if self.view_widget is None:
            return None

        frame = self.view_widget.graphical_frame
        if self.parent_chart is frame.pressure_chart:
            other = frame.xs_pressure_chart
        elif self.parent_chart is frame.xs_pressure_chart:
            other = frame.pressure_chart
        else:
            return None

        if not other.isVisible():
            return None
        return other

    def _set_handle_pen_options(self) -> None:
        self.handlePen = pg.mkPen(color=(0, 0, 0, 0), width=2)
        self.handleHoverPen = pg.mkPen(self.pen)
        self.handleHoverPen.setStyle(Qt.PenStyle.SolidLine)
        self.handleHoverPen.sides = 12
        self.handleHoverPen.radius = 10

        for handle in self.getHandles():
            handle.sides = 12
            handle.radius = 10
            handle.buildPath()

            handle.pen = self.handlePen
            handle.currentPen = self.handlePen
            handle.hoverPen = self.handleHoverPen

            handle.update()

    def _sync_peer_line(self) -> None:
        if not self.is_mirrored or self.syncing_peer:
            return

        other = self._other_depth_chart()
        peer = self._find_peer_line_by_id()
        if peer is None or other is None:
            return

        if self.parent_id == "pressure_plot":
            p0, z0 = self.starting_point
            p1, z1 = self.end_point
            xs0 = other.convert_pressure_to_xs_pressure(p0, z0)
            xs1 = other.convert_pressure_to_xs_pressure(p1, z1)
            if xs0 is None or xs1 is None:
                return
            starting_point = (xs0, z0)
            end_point = (xs1, z1)
        elif self.parent_id == "xs_pressure_plot":
            xs0, z0 = self.starting_point
            xs1, z1 = self.end_point
            p0 = self.parent_chart.convert_xs_pressure_to_pressure(xs0, z0)
            p1 = self.parent_chart.convert_xs_pressure_to_pressure(xs1, z1)
            if p0 is None or p1 is None:
                return
            starting_point = (p0, z0)
            end_point = (p1, z1)
        else:
            return

        peer.syncing_peer = True
        try:
            peer._apply_si_endpoints_and_refresh(starting_point, end_point)
            for line in self.view.annotations:
                if (
                    isinstance(line, StraightLineAnnotation)
                    and line.line_id == peer.id
                    and line.chart_id == peer.parent_id
                    ):
                    line.start_si = peer.starting_point
                    line.end_si = peer.end_point
                    break
        finally:
            peer.syncing_peer = False

    #--------Public API--------

    def build_menu(self) -> QMenu:
        menu = QMenu(self.parent_chart)
        menu.addAction(self.actionConvertLineToFluid)
        if not self.is_mirrored and self.view.sidebar.ref_fluid:
            menu.addAction(self.actionMirrorLine)
        menu.addAction(self.actionDuplicateLine)
        menu.addAction(self.actionDeleteLine)
        return menu

    def calculate_fluid_gradient_si(self) -> float:
        slope = self.calculate_line_slope_si()
        if slope == 0:
            raise ValueError(
                "Cannot compute fluid gradient: line has has zero pressure span"
                )
        return 1 / slope

    def calculate_line_slope_si(self) -> float:
        p0, p1 = self.listPoints()
        p0 = self.mapToView(p0)
        p1 = self.mapToView(p1)

        dx = p0.x() - p1.x()
        dy = p0.y() - p1.y()
        if dy == 0:
            raise ValueError(
                "Cannot compute fluid gradient: line has zero depth span"
                )

        dx = normalise_from_user_units(self.x_unit, self.x_quantity_key, dx)
        dy = normalise_from_user_units(self.y_unit, self.y_quantity_key, dy)
        return dy / dx

    def calculate_y_intercept_si(self) -> float | None:
        m = self.calculate_line_slope_si()
        if m is not None:
            return self.starting_point[1] - m * self.starting_point[0]
        return None

    def delete_self(self) -> None:
        if self.is_mirrored:
            other = self._other_depth_chart()
            peer = self._find_peer_line_by_id()

        for line in self.parent_chart.all_lines:
            if line.id == self.id:
                self.parent_chart.all_lines.remove(line)
                if self.is_mirrored and other is not None and peer is not None:
                    other.all_lines.remove(peer)
                break

        for line in list(self.parent_chart.view.annotations):
            if (
                isinstance(line, StraightLineAnnotation)
                and line.line_id == self.id
                ):
                self.parent_chart.view.annotations.remove(line)

        self.parent_chart.removeItem(self)
        self.deleteLater()
        if self.is_mirrored and other is not None and peer is not None:
            other.removeItem(peer)
            peer.deleteLater()
        self.parent_chart.project.mark_modified()

    def extract_units_and_quantities(self) -> None:
        parent = self.parent_chart
        self.x_quantity_key: str = parent.x_quantity_key
        self.y_quantity_key: str = parent.y_quantity_key
        self.x_unit: str = parent.x_unit
        self.y_unit: str = parent.y_unit

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
        self._set_handle_pen_options()
