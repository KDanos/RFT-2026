from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget

from project import AnalysisView, ColumnSpec, ProjectDataManager
from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart
from ui.depth_gradient_chart.fluid_line_xs_pressure import FluidLineXsPressure
from ui.main_window.project_signals import ProjectSignals

if TYPE_CHECKING:
    import pandas as pd

    from ui.annotations.annotations_bar import AnnotationsBar
    from ui.depth_gradient_chart.fluid_line_pressure import FluidLinePressure
    from ui.depth_gradient_chart.line_annot import LineAnnot
    from ui.depth_gradient_chart.rectangle_annotation import RectangleAnnotation


class ExcessPressureChart(DepthGradientChart):
    # Inherited variables (declared here for readability / typing; set by bases)

    # Project
    # DepthGradientChart
    view: AnalysisView
    project: ProjectDataManager
    signals: ProjectSignals

    # Module
    # DepthGradientChart
    x_axis: str
    col_specs: list[ColumnSpec] | None
    chart_id: str
    vb_menu: object | None
    df: pd.DataFrame | None
    all_scatter_plot_items: list
    all_lines: list[LineAnnot]
    all_visible_fluids: list[FluidLinePressure]
    all_rectangles: list[RectangleAnnotation]
    annotations_bar: AnnotationsBar | None
    fluid_tip_active: bool
    x_spec: object
    x_quantity_key: str
    x_unit: str
    y_spec: object
    y_quantity_key: str
    y_unit: str
    draw_tool: object
    first_click: object
    preview_drawing_item: object

    # Initialisation Methods
    # DepthGradientChart
    """
    (_build_ui)
    (_connect_signals)
    """

    def __init__(
        self,
        parent: QWidget,
        view: AnalysisView,
        project: ProjectDataManager,
        signals: ProjectSignals,
        x_axis: str = "",
        col_specs: list[ColumnSpec] | None = None,
        chart_id: str = "",
        ) -> None:
        super().__init__(
            parent=parent,
            view=view,
            project=project,
            signals=signals,
            x_axis=x_axis,
            col_specs=col_specs,
            chart_id=chart_id,
            )

        # Set project variables

        # Set module variables

        # Initialisation methods

    #--------Private UI--------

    def _paint_all_fluids(self) -> None:
        self.all_visible_fluids.clear()
        for fluid in self.view.sidebar.visible_fluids:
            if fluid is not self.view.sidebar.ref_fluid:
                new_line = FluidLineXsPressure(
                    parent=self,
                    fluid=fluid,
                    signals=self.signals,
                    )
                self.all_visible_fluids.append(new_line)

        for line in self.all_visible_fluids:
            self.removeItem(line)
            line.extract_units_and_quantities()
            line.refresh_geometry()
            self.addItem(line)

    #--------Public API--------

    def convert_pressure_to_xs_pressure(
        self,
        pressure: float,
        depth: float,
        ) -> float | None:
        ref_fluid = self.view.sidebar.ref_fluid
        if ref_fluid is None:
            return None

        gradient = ref_fluid.gradient_si
        zpd = ref_fluid.zero_pressure_depth_si
        expected_p = (depth - zpd) * gradient
        return pressure - expected_p

    def convert_xs_pressure_to_pressure(
        self,
        xs_pressure: float,
        depth: float,
        ) -> float | None:
        ref_fluid = self.view.sidebar.ref_fluid
        if ref_fluid is None:
            return None

        gradient = ref_fluid.gradient_si
        zpd = ref_fluid.zero_pressure_depth_si
        expected_p = (depth - zpd) * gradient
        return expected_p + xs_pressure
