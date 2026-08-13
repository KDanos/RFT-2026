from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QCheckBox, QSpinBox, QTableView

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.filterable_header_view import FilterableHeaderView
from ui.filterable_table.pandas_table_model import PandasTableModel
from ui.filterable_table.proxy_model import ProxyFilterModel


class CustomTableView(QTableView):
    def __init__(
            self,
            parent: QObject,
            project: ProjectDataManager,
            analysis: AnalysisObject,
            view: AnalysisView,
            decimals_check_box: QCheckBox,
            decimal_limit_spin: QSpinBox,
            ) -> None:
        super().__init__(parent)
        self.project = project
        self.analysis = analysis
        self.view = view
        self.decimals_check_box = decimals_check_box
        self.decimal_limit_spin = decimal_limit_spin

        self.setHorizontalHeader(FilterableHeaderView(Qt.Orientation.Horizontal, self))

        self.table_model = PandasTableModel(self, self.decimals_check_box, self.decimal_limit_spin)

        self.proxy_model = ProxyFilterModel(self)
        self.proxy_model.setSourceModel(self.table_model)
        self.setSortingEnabled(True)
        self.setModel(self.proxy_model)

    #--------Private UI--------
    # No private methods: construction and wiring happen in __init__.

    #--------Public API--------
    def load_from_view(self) -> None:
        """Show current view.df + view.column_specs"""
        self.table_model.set_dataframe(
            self.view.df,
            self.view.column_specs,
            self.project,
        )
        self.proxy_model.restore_filters_from_view()
        self.proxy_model.notify_filters_changed()
        self.resizeColumnsToContents()
