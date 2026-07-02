
import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt


from project import ColumnSpec, ProjectDataManager
from ui.analysis_view.model.view_table_formatting import DecimalDisplaySettings, format_cell_for_table


class PandasTableModel(QAbstractTableModel):
    """Qt table model over a normalised view dataframe(display-only)."""
    def __init__(self, parent = None)->None:
        super().__init__(parent)
        self._df:pd.DataFrame = pd.DataFrame()
        self._column_specs:list[ColumnSpec] = []
        self._project:ProjectDataManager|None = None
        self._decimal_settings = DecimalDisplaySettings()
    
    # --------------------data--------------------
    def set_dataframe(
        self, 
        df:pd.DataFrame|None, 
        column_specs:list[ColumnSpec], 
        project:ProjectDataManager|None = None,
        decimal_settings:DecimalDisplaySettings|None = None,
        )->None:
        """Replace underlying data and notity views(e.g. column selection)."""
        self.beginResetModel()
        self._df = df if df is not None else pd.DataFrame()
        self._column_specs = list(column_specs)
        self._project = project
        if decimal_settings is not None:
            self._decimal_settings = decimal_settings
        
        self.endResetModel()
    
    def set_column_unit(self, col:int, unit:str)->None:
        """Update display unit for one column and refresh its cells."""
        if col<0 or col >= len(self._column_specs):
            return 

        old = self._column_specs[col]
        self._column_specs[col] = ColumnSpec(old.name, old.quantity_key, unit)
        
        if self.rowCount()==0:
            return
        
        top_left = self.index(0,col)
        bottom_right = self.index(self.rowCount()-1, col)
        self.dataChanged.emit(
            top_left, 
            bottom_right,
            [Qt.ItemDataRole.DisplayRole],
            )
    
    def set_decimal_settings(self, decimal_settings:DecimalDisplaySettings)->None:
        """Update decimal rounding and refresh all formatted cells."""

        self._decimal_settings = decimal_settings

        if self.rowCount()==0 or self.columnCount()==0:
            return
        
        top_left = self.index(0,0)
        bottom_right = self.index(self.rowCount()-1, self.columnCount()-1)
        self.dataChanged.emit(
            top_left, 
            bottom_right, 
            [Qt.ItemDataRole.DisplayRole]
        )
    
    # --------------------QAbstractTableModel--------------------
    def rowCount(self, parent:QModelIndex=QModelIndex())->int:
        if parent.isValid():
            return 0 
        return 0 if self._df is None else len(self._df)  

    def columnCount(self, parent:QModelIndex = QModelIndex())->int:
        if parent.isValid():
            return 0

        if self._df is None or self._df.empty:
            return len(self._column_specs)

        return self._df.shape[1]

    def headerData(
        self,
        section:int,
        orientation:Qt.Orientation,
        role:int = Qt.ItemDataRole.DisplayRole
        ):
        
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._column_specs):
                return self._column_specs[section].name
            if self._df is not None and section <self._df.shape[1]:
                return str(self._df.columns[section])    
            return None
        return None #no header rows for now

    def data(self, index:QModelIndex, role:int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._df is None or self._df.empty:
            return None
        row = index.row()
        col = index.column()
        if row<0 or col<0 or row >= len(self._df) or col >= self._df.shape[1]:
            return None
        if col >= len(self._column_specs):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iat[row,col]
            spec = self._column_specs[col]
            output_unit = spec.unit or ""
            return format_cell_for_table(
                value,
                spec,
                output_unit,
                self._decimal_settings,
                )
        
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def flags(self, index:QModelIndex)->Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        