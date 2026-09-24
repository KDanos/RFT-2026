from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QMenu
import numpy as np
import pandas as pd
import pyqtgraph as pg

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.canonical_names import CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from project.models import StraightLineAnnotation
from ui.depth_gradient_chart.depth_chart_menu import DepthChartMenu
from ui.depth_gradient_chart.straight_line import StraightLine
from units.units_normalisation import UREG, app_unit_to_pint, identify_si_storage_unit


class DepthGradientChart(pg.PlotWidget):
    def __init__(
            self,
            parent=None,
            x_axis: str = "",
            col_specs: list[ColumnSpec] | None = None,
            chart_id: str = "",
            view: AnalysisView | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.view = view
        self.project: ProjectDataManager | None = None

        # Set module variables
        self.x_axis = x_axis
        self.col_specs = col_specs
        self.chart_id = chart_id
        self.vb_menu = None
        self.df: pd.DataFrame | None = None
        self.all_lines: list[StraightLine] = []
        self.annotations_bar = None

        # Initialisation methods
        self._extract_quantity_and_units()
        self._create_line_drawing_variables()
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self._format_chart()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Keep pyqtgraph default menu for nesting; disable auto-popup on right-click
        self.vb_menu = self.getViewBox().menu
        self.getPlotItem().setMenuEnabled(False)

        self.all_lines.clear()
        assert self.view is not None, "DepthGradientChart requires a view"
        for a in self.view.annotations:
            if isinstance(a, StraightLineAnnotation) and a.chart_id == self.chart_id:
                new_line = StraightLine(
                    parent=self,
                    starting_point=a.start_si,
                    end_point=a.end_si,
                    color=a.color,
                    points_are_si=True,
                )
                new_line.id = a.line_id
                self.all_lines.append(new_line)
        self._paint_all_lines()

    def _built_plot_menu(self) -> QMenu:
        menu = DepthChartMenu(self)
        if self.vb_menu is not None:
            self.vb_menu.setTitle("Plot view")
            menu.addMenu(self.vb_menu)

        ctrl = self.getPlotItem().ctrlMenu
        if ctrl is not None:
            ctrl.setTitle("Plot Options")
            menu.addMenu(ctrl)
        return menu

    def _connect_signals(self) -> None:
        self.customContextMenuRequested.connect(self._show_menu)
        self.scene().sigMouseClicked.connect(self._on_plot_left_click)
        self.scene().sigMouseMoved.connect(self._on_plot_mouse_move)

    def _convert_array_to_user_units(
            self,
            data: np.ndarray,
            quantity_key: str,
            user_unit: str,
            ) -> np.ndarray:
        si_unit = app_unit_to_pint(identify_si_storage_unit(quantity_key))
        pint_user_unit = app_unit_to_pint(user_unit)
        return UREG.Quantity(data, si_unit).to(pint_user_unit).magnitude

    def _create_line_drawing_variables(self) -> None:
        self.draw_mode: bool = False
        self.line_start: QPoint | None = None
        self.preview_line = None

    def _end_draw_straigh_line(self) -> None:
        self.draw_mode = False
        self.removeItem(self.preview_line)
        self.preview_line = None

        new_line = StraightLine(
            self,
            starting_point=self.line_start,
            end_point=self.line_end,
        )
        self.addItem(new_line)
        self.all_lines.append(new_line)
        new_line.refresh_geometry()

        self.line_start = None

        to_save = StraightLineAnnotation(
            start_si=new_line.starting_point,
            end_si=new_line.end_point,
            color=new_line.color,
            chart_id=self.chart_id,
            line_id=new_line.id,
        )
        #Update the persistence variable
        self.view.annotations.append(to_save)
        self.project.mark_modified()

        #Reset the button on the annotations bar
        if self.annotations_bar is not None:
            self.annotations_bar.line_btn.setChecked(False)

    def _extract_quantity_and_units(self) -> None:
        specs_by_name = {s.name: s for s in self.col_specs}
        self.x_spec = specs_by_name.get(self.x_axis)
        if not self.x_spec:
            return

        self.x_quantity_key = self.x_spec.quantity_key
        self.x_unit = self.x_spec.unit

        self.y_spec = specs_by_name.get(CANONICAL_VERTICAL_DEPTH)
        self.y_quantity_key = self.y_spec.quantity_key
        self.y_unit = self.y_spec.unit

    def _format_chart(self) -> None:
        self.setBackground("white")
        self.invertY(True)

        y_label = f"{CANONICAL_VERTICAL_DEPTH} ({self.y_unit})"
        self.setLabel("left", y_label)
        x_label = f"{CANONICAL_FORMATION_PRESSURE} ({self.x_unit})"
        self.setLabel("bottom", x_label)

        self.getAxis("left").enableAutoSIPrefix(False)
        self.getAxis("bottom").enableAutoSIPrefix(False)

    def _get_line_starting_point(self, pos: QPoint) -> None:
        mouse_point = self.getViewBox().mapSceneToView(pos)
        x0, y0 = self.line_start
        x1, y1 = mouse_point.x(), mouse_point.y()
        self.line_end = x1, y1
        self.preview_line.setData([x0, x1], [y0, y1])
        self.preview_line.show()

    def _is_near_line(
            self,
            line: StraightLine,
            mouse_view: object,
            px_tol: float = 30,
            ) -> bool:

        # Get the line end points and convert to view cordinates
        p0, p1 = line.listPoints()
        p0 =line.mapToView(p0)
        p1 =line.mapToView(p1)

        x0, y0 = p0.x(),p0.y()
        x1, y1 = p1.x(), p1.y()
        
        mx, my = float(mouse_view.x()), float(mouse_view.y())

        dx, dy = x1 - x0, y1 - y0
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            t = 0.0
        else:
            t = ((mx - x0) * dx + (my - y0) * dy) / length_sq
            t = max(0.0, min(1.0, t))

        nearest_x = x0 + t * dx
        nearest_y = y0 + t * dy

        vb = self.getViewBox()
        p_mouse = vb.mapViewToScene(pg.Point(mx, my))
        p_near = vb.mapViewToScene(pg.Point(nearest_x, nearest_y))
        dist_px = ((p_mouse.x() - p_near.x()) ** 2 + (p_mouse.y() - p_near.y()) ** 2) ** 0.5
        return dist_px <= px_tol

    def _on_plot_left_click(self, event) -> None:
        if not self.draw_mode:
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        mouse_point = self.getViewBox().mapSceneToView(event.scenePos())
        x, y = mouse_point.x(), mouse_point.y()

        if self.line_start is None:
            self.line_start = (x, y)
            self.preview_line = pg.PlotDataItem(
                pen=pg.mkPen("black", width=1, style=Qt.PenStyle.DashLine)
            )
            self.addItem(self.preview_line)
            self.preview_line.hide()
        else:
            self._end_draw_straigh_line()

    def _on_plot_mouse_move(self, pos: QPoint) -> None:
        if self.draw_mode and self.line_start:
            self._get_line_starting_point(pos)

        # mouse = self.getViewBox().mapSceneToView(pos)
        # for line in self.all_lines:
        #     if self._is_near_line(line, mouse, px_tol=10):
        #         near = self._is_near_line(line, mouse)
        #         #Avoid entering the hovering state on every mouse move
        #         if near and not line.hovering:
        #             line.on_hover(pos)
        #         elif not near and line.hovering:
        #                 line.stop_hovering()

    def _paint_all_lines(self) -> None:
        for line in self.all_lines:
            self.removeItem(line)
            line.extract_units_and_quantities()
            line.refresh_geometry()
            self.addItem(line)

    def _point_tip(self, x: float, y: float, data) -> str:
        return (
            f"{CANONICAL_VERTICAL_DEPTH}: {y:.3g} ({self.y_unit})\n"
            f"{self.x_axis}:{x:.3g} ({self.x_unit})"
        )

    def _show_menu(self, pos: QPoint) -> None:
        scene_pos = self.mapToScene(pos)
        mouse = self.getViewBox().mapSceneToView(scene_pos)

        menu = None
        for line in self.all_lines:
            if self._is_near_line(line, mouse):
                menu = line.build_menu()
                break
        if menu is None:
                menu = self._built_plot_menu()
        menu.exec(self.mapToGlobal(pos))

    #--------Public API--------

    def set_data(self, df: pd.DataFrame) -> None:
        self.df = df
        self.clear()

        self.col_specs = self.view.column_specs
        self._extract_quantity_and_units()
        self._format_chart()

        if df is None or df.empty or CANONICAL_VERTICAL_DEPTH not in df.columns:
            return

        y = self._convert_array_to_user_units(
            df[CANONICAL_VERTICAL_DEPTH].to_numpy(dtype=float),
            self.y_quantity_key,
            self.y_unit,
        )

        if self.x_axis:
            x = self._convert_array_to_user_units(
                df[self.x_axis].to_numpy(dtype=float),
                self.x_quantity_key,
                self.x_unit,
            )

        scatter = pg.ScatterPlotItem(
            x=x,
            y=y,
            symbol="o",
            size=8,
            brush=pg.mkBrush("white"),
            pen=pg.mkPen("blue", width=2),
            hoverable=True,
            tip=self._point_tip,
        )
        self.addItem(scatter)

    def enter_add_text(self)->None:
        print (" I want to addd some text")
    
    def enter_draw_straight_line(self) -> None:
        self.draw_mode = True
        self.line_start = None
        if self.preview_line:
            self.preview_line.hide()

    def enter_draw_square(self)-> None: 
        print ("I want to draw a square")

    def enter_draw_circle(self)->None:
        print (" I want to draw a circle")

    def enter_draw_arrow(self)->None: 
        print ("I want to draw an arrow")


    
