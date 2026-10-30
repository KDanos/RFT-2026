from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import pyqtgraph as pg

from model.fluid_model import Fluid
from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.depth_gradient_chart.fluid_line_pressure import FluidLinePressure
from ui.main_window.project_signals import ProjectSignals

if TYPE_CHECKING:
    from ui.analysis_view import AnalysisViewWidget
    from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart
    from ui.depth_gradient_chart.excess_pressure_chart import ExcessPressureChart


class FluidLineXsPressure(FluidLinePressure):
    # Inherited variables (declared here for readability / typing; set by bases)

    # Project
    # LineAnnot
    parent_chart: pg.PlotWidget | DepthGradientChart | ExcessPressureChart
    project: ProjectDataManager
    view: AnalysisView
    analysis: AnalysisObject
    signals: ProjectSignals

    # Module
    # LineAnnot
    color: QColor | str
    style: Qt.PenStyle
    pen: object
    starting_point: tuple[float, float] | None
    end_point: tuple[float, float] | None
    is_visible: bool
    id: str
    syncing_peer: bool
    view_widget: AnalysisViewWidget | None
    x_quantity_key: str
    y_quantity_key: str
    x_unit: str
    y_unit: str

    # FluidLinePressure
    fluid: Fluid

    # Initialisation Methods
    # FluidLinePressure
    """
    (toggle_editable)
    """

    def __init__(
        self,
        parent: pg.PlotWidget,
        fluid: Fluid,
        signals: ProjectSignals,
        ) -> None:
        super().__init__(
            parent=parent,
            fluid=fluid,
            signals=signals,
            )

        # Set project variables

        # Set module variables

        # Initialisation methods
        self._convert_start_end_points_to_xs_domain()

    #--------Private UI--------

    def _convert_start_end_points_to_xs_domain(self) -> None:
        p, z = self.starting_point
        xs = self.parent_chart.convert_pressure_to_xs_pressure(p, z)
        if xs is not None:
            self.starting_point = (xs, z)

        p, z = self.end_point
        xs = self.parent_chart.convert_pressure_to_xs_pressure(p, z)
        if xs is not None:
            self.end_point = (xs, z)

    def _on_region_changing(self, _roi: object) -> None:
        # Guard to exit if this is initiated from the peer line
        if self.syncing_peer:
            return

        p0, p1 = self.listPoints()
        # Exit if the view has not been created yet to map the new coordinates
        if self.mapToView(p0) is None or self.mapToView(p1) is None:
            return

        # Keep self.starting_point / self.end_point in XS domain SI
        self._on_position_changed()

        xs, z_start = self.starting_point
        p_start = self.parent_chart.convert_xs_pressure_to_pressure(xs, z_start)
        if p_start is None:
            return

        xs, z_end = self.end_point
        p_end = self.parent_chart.convert_xs_pressure_to_pressure(xs, z_end)
        if p_end is None:
            return

        # Update the Fluid object (SSOT) in formation-pressure SI
        self.fluid.update_gradient_and_zpd_from_2_pressure_depth_points(
            (p_start, z_start),
            (p_end, z_end),
            )
        self.fluid.plotting_depth_min_si = min(z_start, z_end)
        self.fluid.plotting_depth_max_si = max(z_start, z_end)
        self.fluid.refresh_contacts_for_self()

        self.view_widget.graphical_sidebar.update_active_fluid_widgets()
        self._sync_peer_fluid_line()

    #--------Public API--------

    def apply_endpoints_from_fluid(self) -> None:
        f = self.fluid
        z0 = f.plotting_depth_min_si
        z1 = f.plotting_depth_max_si
        p0 = f.plotting_pressure_min_si
        p1 = f.plotting_pressure_max_si
        xs0 = self.parent_chart.convert_pressure_to_xs_pressure(p0, z0)
        xs1 = self.parent_chart.convert_pressure_to_xs_pressure(p1, z1)
        if xs0 is None or xs1 is None:
            return

        self._apply_si_endpoints_and_refresh((xs0, z0), (xs1, z1))
