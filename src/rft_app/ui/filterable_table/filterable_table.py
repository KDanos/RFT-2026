from PyQt6.QtWidgets import QFrame, QLabel, QSpinBox, QVBoxLayout,QHBoxLayout, QCheckBox
from PyQt6.QtCore import QObject, Qt

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.custom_table_view import CustomTableView


class FilterableTable(QFrame):
    def __init__(
            self, 
            parent:QObject,
            project:ProjectDataManager, 
            analysis:AnalysisObject, 
            view:AnalysisView
            )->None:
        super().__init__(parent)
        
        parent=parent
        self.project = project
        self.analysis = analysis
        self.view = view
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------
    def _build_ui(self)->None:

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        #Create the widgets frame on top
        widgets_frame = QFrame(self)
        main_layout.addWidget(widgets_frame)
        widgets_layout = QHBoxLayout(widgets_frame)
        
        # Define number of decimals to view
        self.decimals_container = QHBoxLayout()
        self.decimals_check_box = QCheckBox("Round decimals")
        self.decimals_check_box.setCheckState(Qt.CheckState.Checked)
        self.decimal_limit_spin = QSpinBox()
        self.decimal_limit_spin.setValue(1)
        self.decimal_limit_spin.setMaximum(10000)
        self.decimal_limit_spin.setEnabled(True)
        self.decimals_container.addWidget(self.decimals_check_box)
        self.decimals_container.addWidget(self.decimal_limit_spin)
        widgets_layout.addLayout(self.decimals_container)
        widgets_layout.addStretch()# pushes everything to the left
        
        # Ensure manual typing works in the decimals spinbox
        self.decimal_limit_spin.setReadOnly(False)
        self.decimal_limit_spin.lineEdit().setReadOnly(False)
        self.decimal_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.decimal_limit_spin.setKeyboardTracking(False)
        
        #Create the table frame at the bottom and ad the tableview
        table_frame= QFrame(self)
        main_layout.addWidget(table_frame)        
        self.table = CustomTableView(
                self, 
                self.project, 
                self.analysis, 
                self.view, 
                self.decimals_check_box,
                self.decimal_limit_spin)
        table_layout = QVBoxLayout(table_frame)
        table_layout.addWidget(self.table)
    
    def _connect_signals(self):
        self.decimal_limit_spin.valueChanged.connect(self.refresh_display)
        self.decimals_check_box.toggled.connect(self.refresh_display)
    def update_filterable_table(self):
        pass
        
        self._create_table()

    #--------Public API--------
    def load_from_view(self)->None:
        self.table.load_from_view()
    
    def refresh_display(self)->None:
        self.table.model.refresh_display()




