from PyQt6.QtCore import Qt, QPoint
import numpy as np
import pandas as pd
import pyqtgraph as pg

from project import ColumnSpec
from project.canonical_names import CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from units.units_normalisation import UREG, app_unit_to_pint, identify_si_storage_unit
from ui.depth_gradient_chart.depth_chart_menu import DepthMenuChart


class DepthGradientChart(pg.PlotWidget):
    def __init__(
            self,
            parent=None,
            x_axis: str = "",
            col_specs: list[ColumnSpec] | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        # (none)

        # Set module variables
        self.x_axis = x_axis
        self.col_specs = col_specs
        self.df: pd.DataFrame | None = None
        self.vb_menu = None

        # Initialisation methods
        self._extract_quantity_and_units()
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self._format_chart()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Keep pyqtgraph default menu for nesting; disable auto-popup on right-click
        self.vb_menu = self.getViewBox().menu
        self.getPlotItem().setMenuEnabled(False)

    def _connect_signals(self) -> None:
        self.customContextMenuRequested.connect(self._show_graph_menu)

    def _convert_array_to_user_units(
            self,
            data: np.ndarray,
            quantity_key: str,
            user_unit: str,
            ) -> np.ndarray:
        si_unit = app_unit_to_pint(identify_si_storage_unit(quantity_key))
        pint_user_unit = app_unit_to_pint(user_unit)
        return UREG.Quantity(data, si_unit).to(pint_user_unit).magnitude

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

    def _point_tip(self, x: float, y: float, data) -> str:
        return (
            f"{CANONICAL_VERTICAL_DEPTH}: {y:.3g} ({self.y_unit})\n"
            f"{self.x_axis}:{x:.3g} ({self.x_unit})"
        )

    def _show_graph_menu(self, pos: QPoint) -> None:
        menu = DepthMenuChart()

        if self.vb_menu is not None:
            self.vb_menu.setTitle("Plot view")
            menu.addMenu(self.vb_menu)

        ctrl = self.getPlotItem().ctrlMenu
        if ctrl is not None:
            ctrl.setTitle("Plot Options")
            menu.addMenu(ctrl)

        menu.exec(self.mapToGlobal(pos))

    #--------Public API--------

    def set_data(self, df: pd.DataFrame) -> None:
        self.df = df
        self.clear()

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
