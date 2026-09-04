from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QCheckBox, QSpinBox, QTableView

from project import ColumnSpec, ProjectDataManager
from ui.filterable_table.filterable_header_view import FilterableHeaderView
from ui.filterable_table.pandas_table_model import PandasTableModel
from ui.filterable_table.proxy_model import ProxyFilterModel
import pandas as pd


class CustomTableView(QTableView):
    def __init__(
            self,
            parent: QObject,
            project: ProjectDataManager,
            df: pd.DataFrame,
            column_specs: list[ColumnSpec],
            decimals_check_box: QCheckBox,
            decimal_limit_spin: QSpinBox,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project

        # Set module variables
        self.df = df
        self.column_specs = column_specs
        self.decimals_check_box = decimals_check_box
        self.decimal_limit_spin = decimal_limit_spin

        # Initialisation methods
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.setHorizontalHeader(FilterableHeaderView(Qt.Orientation.Horizontal, self))

        self.table_model = PandasTableModel(self, self.decimals_check_box, self.decimal_limit_spin)

        self.proxy_model = ProxyFilterModel(self)
        self.proxy_model.setSourceModel(self.table_model)
        self.setSortingEnabled(True)
        self.setModel(self.proxy_model)

    #--------Public API--------

    def load_data(
            self,
            df: pd.DataFrame,
            column_specs: list[ColumnSpec],
            column_filters: dict | None = None,
            ) -> None:
        self.df = df
        self.column_specs = column_specs
        self.proxy_model.column_filters = column_filters
        self.table_model.set_dataframe(
            self.df,
            self.column_specs,
            self.project,
        )
        self.proxy_model.restore_filters_from_view()
        self.proxy_model.notify_filters_changed()
        self.resizeColumnsToContents()
