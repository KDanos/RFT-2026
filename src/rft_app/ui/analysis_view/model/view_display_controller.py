from PyQt6.QtCore import QObject, QSortFilterProxyModel, pyqtSignal
import pandas as pd
from project import ColumnSpec, ProjectDataManager
from ui.analysis_view.model.pandas_table_model import PandasTableModel
from ui.analysis_view.model.view_table_formatting import DecimalDisplaySettings


class ViewDisplayController(QObject):
    """Owns table source mode+proxy, shared by tabular and graphical frames"""
    display_changed = pyqtSignal()
    def __init__(
        self, 
        project: ProjectDataManager|None = None, 
        parent: 'QObject|None' = None
        ) -> None:
        super().__init__(parent)
        self._project = project
        self._decimal_settings = DecimalDisplaySettings()

        self._source_model = PandasTableModel(self)
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._source_model)

    def set_view_data(
        self, 
        df:pd.DataFrame,
        column_specs:list[ColumnSpec],
        )->None:
        """Push new df/specs into source model (e.g. column selection)"""
        self._source_model.set_dataframe(
            df,
            column_specs, 
            self._project, 
            self._decimal_settings
        )
        
        self.display_changed.emit()

    @property
    def source_model(self)-> PandasTableModel:
        return self._source_model
    
    @property
    def proxy_model (self)->QSortFilterProxyModel:
        return self._proxy_model

    @property
    def decimal_settings (self)->DecimalDisplaySettings:
        return self._decimal_settings

    def refresh_formatting(self,column_specs:list[ColumnSpec]|None = None)->None:
        """Re-apply units/decimals already stored on model specs and settings."""
        if column_specs is not None:
            for col, spec in enumerate(column_specs):
                    self._source_model.set_column_unit(col, spec.unit or "")
        self._source_model.set_decimal_settings(self._decimal_settings)
        self.display_changed.emit()