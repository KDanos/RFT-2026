import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
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

        # Initialisation methods
        self._build_ui()
        self._connect_signals()
        self.extract_units_and_quantities()
        if not points_are_si:
            self._convert_argument_values_to_SI()

    #--------Private UI--------

    def _build_ui(self) -> None:
        pass

    def _connect_signals(self) -> None:
        pass

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

    #--------Public API--------

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
        if self.starting_point and self.end_point:
            super().setData([x0, x1], [y0, y1], pen=self.pen)
