from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.models import AnalysisObject


class GraphicalSidebar(QFrame):
    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager,
            col_specs: list[ColumnSpec],
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = project
        self.col_specs: list[ColumnSpec] = col_specs
        self.analysis: AnalysisObject = self.parent().analysis
        self.view: AnalysisView = self.parent().view

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addStretch()

        self.ref_fluid_label = QLabel("Reference Fluid")
        self.ref_fluid_combo = QComboBox(self)
        self.grid_layout.addWidget(self.ref_fluid_label, 0, 0)
        self.grid_layout.addWidget(self.ref_fluid_combo, 0, 1)
        self._populate_ref_fluid_combo()

        self.active_fluid_label = QLabel("Active Fluid")
        self.active_fluid_combo = QComboBox(self)
        self.grid_layout.addWidget(self.active_fluid_label, 1, 0)
        self.grid_layout.addWidget(self.active_fluid_combo, 1, 1)

    def _populate_ref_fluid_combo(self) -> None:
        if len(self.analysis.fluids) == 0:
            return
        combo = self.ref_fluid_combo
        combo.addItem("None", None)
        for fluid in self.analysis.fluids:
            combo.addItem(fluid.name, fluid)

    #--------Public API--------
    # No public methods yet.
