from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.fluids_model import Fluid
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
        self.ref_fluid: Fluid | None = None
        self.active_fluid: Fluid | None = None

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

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

        self.active_fluid_label = QLabel("Active Fluid")
        self.active_fluid_combo = QComboBox(self)
        self.grid_layout.addWidget(self.active_fluid_label, 1, 0)
        self.grid_layout.addWidget(self.active_fluid_combo, 1, 1)
        self._populate_ref_or_active_fluid_combo()

    def _connect_signals(self) -> None:
        self.ref_fluid_combo.currentTextChanged.connect(self._on_ref_fluid_combo_changed)
        self.active_fluid_combo.currentTextChanged.connect(self._on_active_fluid_combo_changed)

    def _on_active_fluid_combo_changed(self) -> None:
        self.active_fluid = self.active_fluid_combo.currentData()
        self.project.mark_modified()

    def _on_ref_fluid_combo_changed(self) -> None:
        self.ref_fluid = self.ref_fluid_combo.currentData()
        self.project.mark_modified()

    def _populate_ref_or_active_fluid_combo(self) -> None:
        if len(self.analysis.fluids) == 0:
            return
        combos = [self.ref_fluid_combo, self.active_fluid_combo]
        for combo in combos:
            combo.addItem("None", None)
            for fluid in self.analysis.fluids:
                combo.addItem(fluid.name, fluid)

    #--------Public API--------
    # No public methods yet.
