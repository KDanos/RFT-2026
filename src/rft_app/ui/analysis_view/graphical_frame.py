from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
import pyqtgraph

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE
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
        # (none)

        # Initialisation methods
        self._build_ui()

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

        # CPI pane (stretch 1) — placeholder until CPI chart is designed
        self.cpi_frame = QFrame(self)
        self.cpi_frame.setVisible(False)
        self.cpi_layout = QVBoxLayout(self.cpi_frame)
        self.cpi_layout.setContentsMargins(0, 0, 0, 0)
        self.cpi_chart = pyqtgraph.PlotWidget(self.cpi_frame)
        self.cpi_chart.setVisible(False)
        self.cpi_layout.addWidget(self.cpi_chart)

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

        for frame in (self.pressure_frame, self.cpi_frame, self.xs_pressure_frame):
            frame.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
            )
        for chart in (self.pressure_chart, self.cpi_chart, self.xs_pressure_chart):
            chart.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
            )

    #--------Public API--------
    # No public methods yet.
