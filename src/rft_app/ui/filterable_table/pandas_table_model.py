
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt
from PyQt6.QtWidgets import QSpinBox,QCheckBox
import pandas as pd

from project import ProjectDataManager
from project.models import ColumnSpec
from utilities import round_str_to_decimal_points


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
        self.column_specs = list(column_specs) 
        self.project = project 
        self.endResetModel() 

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: # what is the QModelIndexClass and why is it needed, and why do i default to a new instance?
                                                                    # do i understand it correctly that rowCount is an existing method of the AbstractTableModel Class 
                                                                    # and I am overwriting it here?                            
        if parent.isValid():  # i pressume that the parent is an attribute of the QAbstractModelClass. 
                                #Why am i checking for validity and why if valid do i set my row count to 0. Or is it just the parent past into the class at instantiation?
            return 0          #shouldnt it be self.parent instead of parent and have 
                            #self.parent = parent under __init__? How is this function accessing the parent in the class instantiation if it is not allocated to the class via self.parent = parent?
        return len(self.df) 

    def columnCount(self, parent:QModelIndex = QModelIndex())->int:
        if parent.isValid():
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
        
        # is section intented to represent the column index? Does it make sense to replace section with col_idx?
        if role!=Qt.ItemDataRole.DisplayRole: #dont understand what we are doing here at all
            return None #i dont understand what this if loop aims to achieve

        if orientation ==Qt.Orientation.Horizontal:
            if 0<=section<len(self.column_specs):
                return self.column_specs[section].name
            if section <self.df.shape[1]:
                return(str(self.df.columns[section]))
        if orientation == Qt.Orientation.Vertical:
            return str(section+1)
        return # i dont understand neither what the function is supposed to achieve, nor how it does that

    def data(
        self, 
        index:QModelIndex, 
        role:int=Qt.ItemDataRole.DisplayRole,
        )->str:

        if not index.isValid() or self.df.empty:
            return None
        row, col = index.row(), index.column()
        
        if row <0 or col <0 or row >=len(self.df) or col >= self.df.shape[1]:
            return None
        
        if role ==Qt.ItemDataRole.DisplayRole:           
            value = self.df.iat[row,col]
            if pd.isna(value): 
                return ""
            #Round the value to the desired decimal points
            value =round_str_to_decimal_points(value,self.decimals_check_box, self.decimal_limit_spin)
            return str(value)
        
        if role ==Qt.ItemDataRole.TextAlignmentRole: #how under what circomstances is this role called?
            return Qt.AlignmentFlag.AlignCenter  
        
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