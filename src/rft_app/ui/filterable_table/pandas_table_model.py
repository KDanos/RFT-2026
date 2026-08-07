
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt
from PyQt6.QtWidgets import QSpinBox,QCheckBox
import pandas as pd

from project import ProjectDataManager
from project.models import ColumnSpec
from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units
from utilities import is_numeric, round_value_to_decimal_points


class PandasTableModel(QAbstractTableModel):
    """QT table model over a normalised view dataframe (display-only)."""
    
    def __init__(
            self, 
            parent:QObject,
            decimals_check_box:QCheckBox,
            decimal_limit_spin:QSpinBox,
            )->None:

        super().__init__(parent)
        self.df:pd.DataFrame = pd.DataFrame()
        self.column_specs:list[ColumnSpec] = []
        self.project:ProjectDataManager|None = None

        self.decimals_check_box = decimals_check_box
        self.decimal_limit_spin = decimal_limit_spin

    def set_dataframe(
        self, 
        df:pd.DataFrame, 
        column_specs:list[ColumnSpec], 
        project:ProjectDataManager
        )->None:

        self.beginResetModel() 
        self.df = df.copy() if df is not None else pd.DataFrame()
        self.column_specs = column_specs
        self.project = project 
        self.endResetModel() 

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: 
                                                                    
                                                                                             
        if parent.isValid():  
                                
            return 0          
                            
        return len(self.df) 

    def columnCount(self, parent:QModelIndex = QModelIndex())->int:
        if parent.isValid(): # flat table: no child rows/columns
            return 0
        if self.df.empty:
            return len(self.column_specs) 
        return self.df.shape[1]

    def headerData(
        self,
        section:int, 
        orientation:Qt.Orientation, 
        role:int=Qt.ItemDataRole.DisplayRole
        )->str:
        
        if role!=Qt.ItemDataRole.DisplayRole: 
            return None

        if orientation ==Qt.Orientation.Horizontal:
            if 0<=section<len(self.column_specs):
                return self.column_specs[section].name
            if section <self.df.shape[1]:
                return(str(self.df.columns[section]))
        if orientation == Qt.Orientation.Vertical:
            return str(section+1)
        return 

    def data(
        self, 
        index:QModelIndex, 
        role:int=Qt.ItemDataRole.DisplayRole,
        )-> str | float | Qt.AlignmentFlag | None:

        if not index.isValid() or self.df.empty:
            return None
        row, col = index.row(), index.column()
        
        if row <0 or col <0 or row >=len(self.df) or col >= self.df.shape[1]:
            return None
        
        #Extract the value from the df and convert to user selected units
        value = self.df.iat[row,col]

        # 1. blanks - all roles
        if pd.isna(value):
            if role == Qt.ItemDataRole.DisplayRole:
                return ""
            if role == Qt.ItemDataRole.UserRole:
                return None
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignCenter
            return # all other roles (EditRole, BackgroundRole, ToolTipRole etc.)
         
         # 2. alignment only, nor conversion needed:
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        # 3. Numeric columns
        user_unit = self.column_specs[col].unit
        quantity_type = self.column_specs[col].quantity_key
        if STANDARD_QUANTITIES[quantity_type].is_numeric:
            value = convert_from_normalised_to_user_units(user_unit, quantity_type, value)
            value =round_value_to_decimal_points(value,self.decimals_check_box, self.decimal_limit_spin)
        
            if role == Qt.ItemDataRole.DisplayRole:
                return str(value)
            if role == Qt.ItemDataRole.UserRole:
                return float(value)
            return None

        # 4. Text Columns
        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)
        if role ==Qt.ItemDataRole.UserRole: 
            return str(value)
        
        return None

    def refresh_display(self)->None:
        if self.df.empty:
            return
        top_left= self.index(0,0)
        bottom_right = self.index(
            self.rowCount()-1, 
            self.columnCount()-1
        )
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])