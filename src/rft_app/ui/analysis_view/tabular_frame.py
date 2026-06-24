from PyQt6.QtWidgets import QFrame, QTableWidget, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from utilities import create_table_view_frame
class TabularFrame(QFrame):
    def __init__(self,
                parent:QWidget|None = None,
                project:ProjectDataManager|None= None,
                analysis: AnalysisObject|None = None, 
                view:AnalysisView|None= None,
                )->None:
        super().__init__(parent)
        
        #Pass on the working variables
        self.project = project
        self.analysis = analysis

        self.view = view
        if analysis:
            self.dataset= analysis.analysis_dataset

        #Build the sidebar
        self._build_ui()
        self.update_column_specs()
    
    #--------Public API--------
    def update_column_specs(self):
        self.view.column_specs = []
        for c in range(self.table.columnCount()):
            combo_widget = self.table.cellWidget(0,c)
            name = self.table.horizontalHeaderItem(c).text()
            quantity_key = combo_widget.quantity_key
            current_unit = combo_widget.currentText()
            spec = ColumnSpec(name, quantity_key, current_unit)
            self.view.column_specs.append(spec)

    #--------Private UI--------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.table_frame, self.table, update_columns_values = create_table_view_frame(
                                            self.view.df,
                                            self.dataset.column_specs, 
                                            self, 
                                            self.project )
        main_layout.addWidget(self.table_frame)
        
        