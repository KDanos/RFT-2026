from PyQt6.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.widgets import UnitsComboBox
from utilities import unique_name


class NewFluidDialog(QDialog):
    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager ,
            view: AnalysisView ,
            gradient: float| None = None,
            gradient_in_SI: bool = False) -> None:
        super().__init__(parent)
            
        self.parent = parent
        self.gradient = gradient
        self.gradient_in_SI = gradient_in_SI

        # Set project variables
        self.project: ProjectDataManager  = project
        self.view: AnalysisView= view
        self.analysis: AnalysisObject  = self.view.analysis_object
        

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.setWindowTitle("New Fluid")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addStretch()

        # Name
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setPlaceholderText("New Fluid Name")
        self.grid_layout.addWidget(self.name_line_edit,0,0,1,2)

        # Gradient
        self.gradient_label = QLabel("Gradient")
        self.gradient_line_edit = QLineEdit(self)
        self.gradient_units = UnitsComboBox("pressure_gradient", self.project)
        self.grid_layout.addWidget(self.gradient_label, 1,0)
        self.grid_layout.addWidget(self.gradient_line_edit,1,1)
        self.grid_layout.addWidget(self.gradient_units,1,2)


    def _connect_signals(self) -> None:
        self.name_line_edit.editingFinished.connect(self._check_name_uniqueness)

    def _check_name_uniqueness(self):
        name = self.name_line_edit.text()
        all_names  = [fluid.name for fluid in self.analysis.fluids ]
        
        name = unique_name(name,all_names)
        print (name)

    #--------Public API--------
    # No public methods yet.
