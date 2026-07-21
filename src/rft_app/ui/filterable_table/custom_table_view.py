from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QTableView

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.pandas_table_model import PandasTableModel


class CustomTableView(QTableView):
    def __init__(self, 
                parent:QObject,
                project:ProjectDataManager,
                analysis:AnalysisObject,
                view:AnalysisView
                )->None:
        super().__init__(parent)
        self.project = project
        self.analysis = analysis
        self.view = view
        self.model = PandasTableModel(self)
        self.setModel(self.model) #what does this method achieve?

    #--------Public API--------
    def load_from_view(self)->None:
        """Show current view.df +view.column_specs"""
        self.model.set_dataframe(
            self.view.df,
            self.view.column_specs,
            self.project
        )
        self.resizeColumnsToContents() #is this a TableWidget method? Wasnt this available to my other tablewidgets or tableviewWidgets?





