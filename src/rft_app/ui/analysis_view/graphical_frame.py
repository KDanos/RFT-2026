from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
import pyqtgraph

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE
from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart


class GraphicalFrame(QFrame):
    def __init__(
            self,
            parent: QWidget | None = None,
            project: ProjectDataManager | None = None,
            col_specs: list[ColumnSpec] | None = None,
            view: AnalysisView | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project
        self.view = view
        self.col_specs = col_specs

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
            self.pressure_frame,
            CANONICAL_FORMATION_PRESSURE,
            self.col_specs,
            "pressure_plot",
            self.view,
        )
        self.pressure_chart.project = self.project
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
            self.xs_pressure_frame,
            CANONICAL_EXCESS_PRESSURE,
            self.col_specs,
            "xs_pressure_plot",
            self.view,
        )
        self.xs_pressure_chart.project = self.project
        self.xs_pressure_layout.addWidget(self.xs_pressure_chart)
        self.xs_pressure_chart.setVisible(False)

        self.main_layout.addWidget(self.pressure_frame, 4)
        self.main_layout.addWidget(self.cpi_frame, 1)
        self.main_layout.addWidget(self.xs_pressure_frame, 4)

        for frame in (self.pressure_frame, self.cpi_frame, self.xs_pressure_frame):
            frame.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
        for chart in (self.pressure_chart, self.cpi_chart, self.xs_pressure_chart):
            chart.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

    #--------Public API--------
    # No public methods yet.
