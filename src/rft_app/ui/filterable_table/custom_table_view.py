from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QCheckBox, QSpinBox, QTableView

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.pandas_table_model import PandasTableModel


class CustomTableView(QTableView):
    def __init__(self, 
                parent:QObject,
                project:ProjectDataManager,
                analysis:AnalysisObject,
                view:AnalysisView,
                decimals_check_box:QCheckBox,
                decimal_limit_spin:QSpinBox
                )->None:
        super().__init__(parent)
        self.project = project
        self.analysis = analysis
        self.view = view
        self.decimals_check_box = decimals_check_box
        self.decimal_limit_spin = decimal_limit_spin
        
        self.table_model = PandasTableModel(self, self.decimals_check_box, self.decimal_limit_spin)
        self.setModel(self.table_model) 

    #--------Private UI--------
  
    #--------Public API--------
    def load_from_view(self)->None:
        """Show current view.df +view.column_specs"""
        self.table_model.set_dataframe(
            self.view.df,
            self.view.column_specs,
            self.project
        )
        self.resizeColumnsToContents() #is this a TableWidget method? Wasnt this available to my other tablewidgets or tableviewWidgets?





