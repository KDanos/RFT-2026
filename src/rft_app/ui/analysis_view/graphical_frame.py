from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
import pyqtgraph as pg
import pandas as pd

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE
from ui.analysis_view.analysis_view_data_manager import build_scatter_series
from utilities import print_current_location_function
from ui.main_window.signal_collection_protocol import SignalCoordinator
from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart


class GraphicalFrame(QFrame):
    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager,
            col_specs: list[ColumnSpec],
            view: AnalysisView,
            signal_coordinator: SignalCoordinator,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = project
        self.view: AnalysisView = view
        self.col_specs: list[ColumnSpec] = col_specs
        self.signal_coordinator = signal_coordinator


        # Set module variables
        self.all_plots:list[pg.PlotWidget] = []

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Pressure pane (stretch 4)
        self.pressure_frame = QFrame(self)
        self.pressure_layout = QVBoxLayout(self.pressure_frame)
        self.pressure_layout.setContentsMargins(0, 0, 0, 0)
        self.pressure_chart = DepthGradientChart(
            parent=self.pressure_frame,
            view=self.view,
            project=self.project,
            signal_coordinator= self.signal_coordinator,
            x_axis=CANONICAL_FORMATION_PRESSURE,
            col_specs=self.col_specs,
            chart_id="pressure_plot",
        )
        self.pressure_layout.addWidget(self.pressure_chart)
        self.all_plots.append(self.pressure_chart)

        # CPI pane (stretch 1) — placeholder until CPI chart is designed
        self.cpi_frame = QFrame(self)
        self.cpi_frame.setVisible(False)
        self.cpi_layout = QVBoxLayout(self.cpi_frame)
        self.cpi_layout.setContentsMargins(0, 0, 0, 0)
        self.cpi_chart = pg.PlotWidget(self.cpi_frame)
        self.cpi_chart.setVisible(False)
        self.cpi_layout.addWidget(self.cpi_chart)
        # self.all_plots.append(self.cpi_chart)

        # Excess-pressure pane (stretch 4)
        self.xs_pressure_frame = QFrame(self)
        self.xs_pressure_layout = QVBoxLayout(self.xs_pressure_frame)
        self.xs_pressure_layout.setContentsMargins(0, 0, 0, 0)
        self.xs_pressure_chart = DepthGradientChart(
            parent=self.xs_pressure_frame,
            view=self.view,
            project=self.project,
            signal_coordinator=self.signal_coordinator,
            x_axis=CANONICAL_EXCESS_PRESSURE,
            col_specs=self.col_specs,
            chart_id="xs_pressure_plot",
        )
        self.xs_pressure_layout.addWidget(self.xs_pressure_chart)
        self.xs_pressure_chart.setVisible(False)

        self.main_layout.addWidget(self.pressure_frame, 4)
        self.main_layout.addWidget(self.cpi_frame, 1)
        self.main_layout.addWidget(self.xs_pressure_frame, 4)
        self.all_plots.append(self.xs_pressure_chart)

        for frame in (self.pressure_frame, self.cpi_frame, self.xs_pressure_frame):
            frame.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
            )
        for chart in self.all_plots:
            chart.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
            )

    def _connect_signals(self)-> None:
        for plot in self.all_plots:
            plot.sigRangeChanged.connect(self._sync_depth_axis)
 
    def _sync_depth_axis(self, plot_widget:pg.PlotWidget, view_range:list[[float, float],[float, float]])->None:
        
        # range is [[xmin, xmax], [ymin, ymax]]
        y_range = view_range[1]
        plots_to_adjust = [plot for plot in self.all_plots if plot is not plot_widget and plot.isVisible()]
        for plot in plots_to_adjust:
            with QSignalBlocker(plot):
                plot.getViewBox().setYRange(*y_range)
       
    #--------Public API--------
    def refresh_charts(
        self,
        df: pd.DataFrame,
        primary_identifier: str | None,
        secondary_identifier: str | None,
        show_xs: bool,
        ) -> None:
        series = build_scatter_series(df, primary_identifier, secondary_identifier)
        self.pressure_chart.df= df
        self.pressure_chart.create_all_scatter_plot_items(series)
        self.pressure_chart.refresh_self

        self.xs_pressure_frame.setVisible(show_xs)
        self.xs_pressure_chart.setVisible(show_xs)
        if show_xs:
            self.xs_pressure_chart.df = df
            self.xs_pressure_chart.create_all_scatter_plot_items(series)
            self.xs_pressure_chart.refresh_self()
