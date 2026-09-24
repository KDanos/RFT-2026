from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QMenu, QWidget
import numpy as np
import pandas as pd
import pyqtgraph as pg

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.canonical_names import CANONICAL_SURFACE_PRESSURE, CANONICAL_VERTICAL_DEPTH
from project.models import RectAnnotation, StraightLineAnnotation
from ui.depth_gradient_chart.depth_chart_menu import DepthChartMenu
from ui.depth_gradient_chart.rectangle_annotation import RectangleAnnotation
from ui.depth_gradient_chart.straight_line import StraightLine
from units.units_normalisation import UREG, app_unit_to_pint, identify_si_storage_unit


class DepthGradientChart(pg.PlotWidget):
    TOOL_LINE = "straight_line"
    TOOL_SQUARE = "square"
    TOOL_CIRCLE = "circle"
    TOOL_ARROW = "arrow"
    TOOL_TEXT = "text_box"

    def __init__(
            self,
            parent: QWidget | None = None,
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
        self.all_rectangles: list[RectangleAnnotation] = []
        self.annotations_bar = None

        # Initialisation methods
        self._extract_quantity_and_units()
        self._create_line_drawing_variables()
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _begin_draw_preview(self) -> None:
        pen = pg.mkPen("black", width=1, style=Qt.PenStyle.DashLine)
        if self.draw_tool == self.TOOL_LINE:
            self.preview_drawing_item = pg.PlotDataItem(pen=pen)
        elif self.draw_tool == self.TOOL_SQUARE:
            self.preview_drawing_item = pg.RectROI(
                pos=self.first_click,
                size=(1e-9, 1e-9),
                pen=pen,
                invertible=True,
            )

        self.addItem(self.preview_drawing_item)
        self.preview_drawing_item.hide()

    def _build_plot_menu(self) -> QMenu:
        menu = DepthChartMenu(self)
        if self.vb_menu is not None:
            self.vb_menu.setTitle("Plot view")
            menu.addMenu(self.vb_menu)

        ctrl = self.getPlotItem().ctrlMenu
        if ctrl is not None:
            ctrl.setTitle("Plot Options")
            menu.addMenu(ctrl)
        return menu

    def _build_ui(self) -> None:
        self._format_chart()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Keep pyqtgraph default menu for nesting; disable auto-popup on right-click
        self.vb_menu = self.getViewBox().menu
        self.getPlotItem().setMenuEnabled(False)

        self.all_lines.clear()
        self.all_rectangles.clear()
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
            elif isinstance(a, RectAnnotation) and a.chart_id == self.chart_id:
                new_rect = RectangleAnnotation(
                    parent=self,
                    position=a.pos_si,
                    size=a.size_si,
                    color=a.color,
                    points_are_si=True,
                )
                new_rect.id = a.rect_id
                self.all_rectangles.append(new_rect)
        self._paint_all_lines()
        self._paint_all_rectangles()

    def _clear_draw_preview_item(self) -> None:
        if self.preview_drawing_item is not None:
            self.removeItem(self.preview_drawing_item)
            self.preview_drawing_item = None
        self.first_click = None

    def _connect_signals(self) -> None:
        self.customContextMenuRequested.connect(self._show_menu)
        self.scene().sigMouseClicked.connect(self._on_plot_left_click_rebuild)
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
        self.draw_tool: str | None = None
        self.first_click: QPoint | None = None
        self.preview_drawing_item = None

    def _end_draw_square(self) -> None:
        pos = self.preview_drawing_item.pos()
        size = self.preview_drawing_item.size()
        position = (float(pos.x()), float(pos.y()))
        rect_size = (float(size.x()), float(size.y()))

        new_rect = RectangleAnnotation(
            self,
            position=position,
            size=rect_size,
        )
        self.addItem(new_rect)
        self.all_rectangles.append(new_rect)
        new_rect.refresh_geometry()

        self.draw_tool = None
        self._clear_draw_preview_item()

        to_save = RectAnnotation(
            pos_si=new_rect.position,
            size_si=new_rect.size_si,
            color=str(new_rect.color),
            chart_id=self.chart_id,
            rect_id=new_rect.id,
        )
        self.view.annotations.append(to_save)
        self.project.mark_modified()

        if self.annotations_bar is not None:
            self.annotations_bar.clear_tool_selection()

    def _end_draw_straight_line(self) -> None:
        new_line = StraightLine(
            self,
            starting_point=self.first_click,
            end_point=self.line_end,
        )
        self.addItem(new_line)
        self.all_lines.append(new_line)
        new_line.refresh_geometry()

        self.draw_tool = None
        self._clear_draw_preview_item()

        to_save = StraightLineAnnotation(
            start_si=new_line.starting_point,
            end_si=new_line.end_point,
            color=new_line.color,
            chart_id=self.chart_id,
            line_id=new_line.id,
        )
        self.view.annotations.append(to_save)
        self.project.mark_modified()

        if self.annotations_bar is not None:
            self.annotations_bar.clear_tool_selection()

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

    def _finish_draw(self) -> None:
        if self.draw_tool == self.TOOL_LINE:
            self._end_draw_straight_line()
        elif self.draw_tool == self.TOOL_SQUARE:
            self._end_draw_square()

    def _format_chart(self) -> None:
        self.setBackground("white")
        self.invertY(True)

        y_label = f"{CANONICAL_VERTICAL_DEPTH} ({self.y_unit})"
        self.setLabel("left", y_label)
        x_label = f"{CANONICAL_SURFACE_PRESSURE} ({self.x_unit})"
        self.setLabel("bottom", x_label)

        self.getAxis("left").enableAutoSIPrefix(False)
        self.getAxis("bottom").enableAutoSIPrefix(False)

    def _is_in_rectangle(
            self,
            rect: RectangleAnnotation,
            mouse_view: object,
            ) -> bool:
        pos = rect.pos()
        size = rect.size()
        x0, x1 = sorted((float(pos.x()), float(pos.x()) + float(size.x())))
        y0, y1 = sorted((float(pos.y()), float(pos.y()) + float(size.y())))
        mx, my = float(mouse_view.x()), float(mouse_view.y())
        return x0 <= mx <= x1 and y0 <= my <= y1

    def _is_near_line(
            self,
            line: StraightLine,
            mouse_view: object,
            px_tol: float = 30,
            ) -> bool:
        p0, p1 = line.listPoints()
        p0 = line.mapToView(p0)
        p1 = line.mapToView(p1)

        x0, y0 = p0.x(), p0.y()
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

    def _on_plot_left_click_rebuild(self, event) -> None:
        if not self.draw_tool or event.button() != Qt.MouseButton.LeftButton:
            return

        mouse_point = self.getViewBox().mapSceneToView(event.scenePos())
        x, y = mouse_point.x(), mouse_point.y()
        if self.first_click is None:
            self.first_click = (x, y)
            self._begin_draw_preview()
        else:
            self._finish_draw()

    def _on_plot_mouse_move(self, pos: QPoint) -> None:
        if self.first_click is None or self.preview_drawing_item is None:
            return
        if self.draw_tool == self.TOOL_LINE:
            self._track_preview_line(pos)
        elif self.draw_tool == self.TOOL_SQUARE:
            self._track_rectangle_size(pos)

    def _paint_all_lines(self) -> None:
        for line in self.all_lines:
            self.removeItem(line)
            line.extract_units_and_quantities()
            line.refresh_geometry()
            self.addItem(line)

    def _paint_all_rectangles(self) -> None:
        for rect in self.all_rectangles:
            self.removeItem(rect)
            rect.extract_units_and_quantities()
            rect.refresh_geometry()
            self.addItem(rect)

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
            for rect in self.all_rectangles:
                if self._is_in_rectangle(rect, mouse):
                    menu = rect.build_menu()
                    break

        if menu is None:
            menu = self._build_plot_menu()
        menu.exec(self.mapToGlobal(pos))

    def _track_preview_line(self, pos: QPoint) -> None:
        mouse_point = self.getViewBox().mapSceneToView(pos)
        x0, y0 = self.first_click
        x1, y1 = mouse_point.x(), mouse_point.y()
        self.line_end = x1, y1
        self.preview_drawing_item.setData([x0, x1], [y0, y1])
        self.preview_drawing_item.show()

    def _track_rectangle_size(self, pos: QPoint) -> None:
        mouse = self.getViewBox().mapSceneToView(pos)
        x0, y0 = self.first_click
        x1, y1 = mouse.x(), mouse.y()

        rect_pos = (min(x0, x1), min(y0, y1))
        size = (abs(x1 - x0), abs(y1 - y0))
        self.preview_drawing_item.setPos(rect_pos)
        self.preview_drawing_item.setSize(size)
        self.preview_drawing_item.show()

    #--------Public API--------

    def enter_add_text(self) -> None:
        pass

    def enter_draw_arrow(self) -> None:
        pass

    def enter_draw_circle(self) -> None:
        pass

    def enter_draw_square(self) -> None:
        self._clear_draw_preview_item()
        self.draw_tool = self.TOOL_SQUARE

    def enter_draw_straight_line(self) -> None:
        self._clear_draw_preview_item()
        self.draw_tool = self.TOOL_LINE

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
        self._paint_all_lines()
        self._paint_all_rectangles()
