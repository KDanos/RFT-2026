import uuid

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QMenu
import pyqtgraph as pg

from units import convert_from_normalised_to_user_units, normalise_from_user_units


class StraightLine(pg.PlotDataItem):
    def __init__(
            self,
            parent: pg.PlotWidget | None = None,
            color: QColor | str = "black",
            style: Qt.PenStyle = Qt.PenStyle.DashLine,
            starting_point: tuple[float, float] | None = None,
            end_point: tuple[float, float] | None = None,
            points_are_si: bool = False,
            ) -> None:
        super().__init__()

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
        self.hovering: bool = False

        # Initialisation methods
        self._build_ui()
        self._define_menu_actions()
        self._connect_signals()
        self.extract_units_and_quantities()
        if not points_are_si:
            self._convert_argument_values_to_SI()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.setCurveClickable(True, width=12)

    def _connect_signals(self) -> None:
        self.actionConvertLineToFluid.triggered.connect(self._convert_line_to_fluid)
        self.actionDuplicateLine.triggered.connect(self._duplicate_self)
        self.actionDeleteLine.triggered.connect(self._delete_self)

    def _convert_argument_values_to_SI(self) -> None:
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

    def _convert_line_to_fluid(self) -> None:
        pass

    def _define_menu_actions(self) -> None:
        self.actionConvertLineToFluid = QAction("Convert to Fluid", self)
        self.actionDuplicateLine = QAction("Duplicate", self)
        self.actionDeleteLine = QAction("Delete", self)

    def _delete_self(self) -> None:
        pass

    def _duplicate_self(self) -> None:
        pass

    def _highlight_line_end_points(self) -> None:
        x, y = self.curve.getData()
        self.temp_scatter = pg.ScatterPlotItem(
            x=x,
            y=y,
            symbol="o",
            size=15,
            brush=pg.mkBrush(0, 0, 0, 0),
            pen=pg.mkPen("#F0D78C", width=2),
        )
        self.parent_chart.addItem(self.temp_scatter)

    def _is_close_to_point(
            self,
            pos: QPoint,
            px_tol: float = 10,
            ) -> QPointF | None:
        vb = self.parent_chart.getViewBox()
        x, y = self.curve.getData()

        for i in range(len(x)):
            # View coordinates are in axis units, scene coordinates are in pixels
            point_view = QPointF(float(x[i]), float(y[i]))
            point_pxl = vb.mapViewToScene(point_view)

            dx = abs(pos.x() - point_pxl.x())
            dy = abs(pos.y() - point_pxl.y())
            if dx <= px_tol and dy <= px_tol:
                return point_view
        return None

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

    def on_hover(self, pos: QPoint) -> None:
        self.hovering = True
        self.pen.setWidth(4)
        self.setPen(self.pen)
        self._highlight_line_end_points()

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
        if self.starting_point and self.end_point:
            super().setData([x0, x1], [y0, y1], pen=self.pen)

    def stop_hovering(self) -> None:
        self.hovering = False
        self.pen.setWidth(2)
        self.setPen(self.pen)

        # Remove the highlight of the ends
        self.parent_chart.removeItem(self.temp_scatter)
