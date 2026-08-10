from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QCheckBox, QSpinBox, QTableView

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.proxy_model import ProxyFilterModel
from ui.filterable_table.filterable_header_view import FilterableHeaderView
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
        
        #Replace the default header with the custom one to capture the filtering options
        self.setHorizontalHeader(FilterableHeaderView(Qt.Orientation.Horizontal, self))

        #Create a model to read the dataframe. 
        self.table_model = PandasTableModel(self, self.decimals_check_box, self.decimal_limit_spin)
        
        #Define the proxy model. It reads the PandasTableModel, applies the filters and feeds into the tabular and graphical views
        self.proxy_model = ProxyFilterModel(self)
        self.proxy_model.setSourceModel(self.table_model)
        self.setSortingEnabled(True)
        self.setModel(self.proxy_model) 

    #--------Private UI--------
  
    #--------Public API--------
    def load_from_view(self)->None:
        """Show current view.df + view.column_specs"""
        self.table_model.set_dataframe(
            self.view.df,
            self.view.column_specs,
            self.project,
        )
        self.proxy_model.restore_filters_from_view()
        self.proxy_model.notify_filters_changed()
        self.resizeColumnsToContents()






