from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
import pyqtgraph as pg

from project import AnalysisView, ColumnSpec, ProjectDataManager
from model.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE
from ui.main_window.project_signals import ProjectSignals
from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart
from ui.depth_gradient_chart.excess_pressure_chart import ExcessPressureChart


class GraphicalFrame(QFrame):
    # Inherited variables
    # None

    def __init__(
        self,
        parent: QWidget,
        project: ProjectDataManager,
        col_specs: list[ColumnSpec],
        view: AnalysisView,
        signals: ProjectSignals,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = project
        self.view: AnalysisView = view
        self.col_specs: list[ColumnSpec] = col_specs
        self.signals: ProjectSignals = signals

        # Set module variables
        self.all_plots: list[pg.PlotWidget] = []
        self.y_range: list[float, float] | None = None  # (ymin, ymax)

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
            signals=self.signals,
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

        # Excess-pressure pane (stretch 4)
        self.xs_pressure_frame = QFrame(self)
        self.xs_pressure_layout = QVBoxLayout(self.xs_pressure_frame)
        self.xs_pressure_layout.setContentsMargins(0, 0, 0, 0)
        self.xs_pressure_chart = ExcessPressureChart(
            parent=self.xs_pressure_frame,
            view=self.view,
            project=self.project,
            signals=self.signals,
            x_axis=CANONICAL_EXCESS_PRESSURE,
            col_specs=self.col_specs,
            chart_id="xs_pressure_plot",
        )
        self.xs_pressure_layout.addWidget(self.xs_pressure_chart)
        # Hide the xs pressure chart on load when no reference fluid is defined
        self.xs_pressure_frame.setVisible(False)  # if not hidden, it takes space and remains empty. An option if desired
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

    def _connect_signals(self) -> None:
        for plot in self.all_plots:
            plot.sigRangeChanged.connect(self._update_common_y_range)

    def _update_common_y_range(
        self,
        plot_widget: pg.PlotWidget,
        view_range: list[[float, float], [float, float]],
        ) -> None:
        # range is [[xmin, xmax], [ymin, ymax]]
        # Exit if the chart is not allowed to emit-avoid ping-pong
        if not plot_widget.can_emit_y_range:
            return

        # SSOT from the chart that changed
        self.y_range = list(view_range[1])

        # Ensure all plots are synced to the new range
        self._sync_all_plots_y_range()

    def fit_and_sync_y_from_pressure_plots(self) -> None:
        """After data/scatter rebuild: fill SSOT from pressure chart, then push to the other plots."""
        # Avoid ping-pong
        for plot in self.all_plots:
            plot.can_emit_y_range = False

        vb = self.pressure_chart.getViewBox()

        # One-shot fit from scatters only (ROIs poison full autoRange)
        scatters = self.pressure_chart.all_scatter_plot_items
        if scatters:
            vb.autoRange(items=scatters)
        vb.enableAutoRange(x=False, y=False)

        # Extract the y_range
        self.y_range = list(vb.viewRange()[1])

        # One-shot X fit on peer charts, then shared Y (pan must not re-run this)
        for plot in self.all_plots:
            if plot is self.pressure_chart or not plot.isVisible():
                continue
            with QSignalBlocker(plot):
                peer_vb = plot.getViewBox()
                if plot.all_scatter_plot_items:
                    peer_vb.autoRange(items=plot.all_scatter_plot_items)
                peer_vb.setYRange(*self.y_range, padding=0)
                peer_vb.enableAutoRange(x=False, y=False)

        self._sync_all_plots_y_range()

    def _sync_all_plots_y_range(self) -> None:
        """Push Y SSOT to all visible plots; leave axes manual so pan works in X and Y."""
        for plot in self.all_plots:
            plot.can_emit_y_range = False
            if plot.isVisible() and self.y_range is not None:
                with QSignalBlocker(plot):
                    vb = plot.getViewBox()
                    vb.setYRange(*self.y_range, padding=0)
                    vb.enableAutoRange(x=False, y=False)

            # Reset the plots to be able to emit their y-change in the future
            plot.can_emit_y_range = True

    #--------Public API--------
    # (none)
