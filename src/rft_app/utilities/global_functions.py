from typing import Any, Iterable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,QCheckBox, QDialog, QSpinBox, 
                            QTableWidget, QVBoxLayout)
import pandas as pd
from qtpy.QtWidgets import QTableWidgetItem
from dataclasses import fields


from project.models import ColumnSpec, DataSet, DataSetLogEntry



def unique_name(
    name:str="",
    existing: Iterable[str]|None=None
    )->str:
    
    """ Create a name as unique identifier
        Returns a string that is not included in iterable list"""
    
    existing = existing or ()
    taken = set (existing)
    n = (name or "").strip()
    
    #Check if the desired name is not use and apply it   
    if n and n not in taken:
        return n

    #Create naming options with the smallest possible index and the prefered name, and check if it is free
    i = 0
    candidate = f"{n}_{i}"
    while candidate in taken:
        i +=1
        candidate = f"{n}_{i}"
    return candidate
    
def is_numeric(value)-> bool: 
    if value is None:
        return False
    if isinstance(value,float) and pd.isna(value):
        return False
    if isinstance(value,(int,float)):
        return True
    if not isinstance(value,str):
        return False
    try:
        float(value.strip())
        return True
    except ValueError:
        return False
    
def force_numeric(value:Any)->float| None:
    if value is None:
        return None
    if isinstance(value, str):
        value= value.strip()
        if value =="":
            return None
    try:
         return(float(value))
    except(TypeError, ValueError):
        return None

def get_tree_top_level_item_by_name(tree:QTreeWidget, name:str)->QTreeWidgetItem:
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        if item.text(0)==name:
            return item
    return None
    
def get_tree_item_by_name(tree:QTreeWidget, top_level_item:QTreeWidgetItem, name:str)->QTreeWidgetItem:

    it = QTreeWidgetItemIterator(top_level_item)
    while node := it.value():
        if node.text(0)==name:
            return node
        it += 1
    return None

def update_tree_ancestors( item: QTreeWidgetItem) -> None:
    parent = item.parent()
    while parent is not None:
        checked = 0
        unchecked = 0
        for i in range(parent.childCount()):
            state = parent.child(i).checkState(0)
            if state == Qt.CheckState.Checked:
                checked += 1
            elif state == Qt.CheckState.Unchecked:
                unchecked += 1
        if checked == parent.childCount():
            parent.setCheckState(0, Qt.CheckState.Checked)
        elif unchecked == parent.childCount():
            parent.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)
        # Iterate to the next parent
        parent = parent.parent()

def update_tree_descendants(item: QTreeWidgetItem, state: Qt.CheckState):
    for i in range(item.childCount()):
        child = item.child(i)
        child.setCheckState(0, state)
        update_tree_descendants(child, state)

def round_str_to_decimal_points(
                                value:float,
                                check_box:QCheckBox,
                                spin_box: QSpinBox
                                )->str:

    if not check_box.isChecked():
        return str(value) if value is not None else ""

    if value =="" or not is_numeric(value):
        return str(value) if value !="" else ""

    decimal_points = spin_box.value()
    if decimal_points == 0:
        value = int(round(float(value),decimal_points))
    else:
        value = round(float(value),decimal_points)
    return(str(value))          

def create_dataframe_table(df:pd.DataFrame, spec:ColumnSpec=None, parent = None)->QTableWidget:
    from ui.widgets.table_widgets import UnitsComboBox
    rows, columns = df.shape
    data_table = QTableWidget(rows+1, columns,parent)
    data_table.setHorizontalHeaderLabels([str(column) for column in df.columns])
    for c in range(columns):
        quantity = spec[c].quantity_key
        units_combo=UnitsComboBox(quantity)
        data_table.setCellWidget(0,c,units_combo)
        for r in range(rows):
            item = str(df.iat[r,c])
            data_table.setItem(r+1,c,QTableWidgetItem(item))

    return data_table

def show_data_frame_table(df:pd.DataFrame, spec:ColumnSpec=None,title:str=None, parent=None)->QDialog:
    if title is None or "":
        title = "Data Table"
    
    window = QDialog(parent)
    window.setWindowTitle(title)
    window.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
    window.setWindowFlags(window.windowFlags()
        |Qt.WindowType.WindowMaximizeButtonHint 
        |Qt.WindowType.WindowMinimizeButtonHint
    )
    table = create_dataframe_table(df,spec, parent )
    layout = QVBoxLayout(window)
    layout.addWidget(table)
    window.show()

def create_log_table(dataset:DataSet, parent = None)->QTableWidget:
    
    # Define Column Count and Name
    log_fields = fields(DataSetLogEntry)  
    columns = len(log_fields)
    column_names = [f.name for f in log_fields]
    # Define Row Count
    rows = len(dataset.info_log)
    # Define the table structure
    table=QTableWidget(rows, columns, parent)
    table.setHorizontalHeaderLabels(column_names)
    # table.setVerticalHeader()
    
    for r, entry in enumerate(dataset.info_log):
        for c, f in enumerate(log_fields):  
            value = getattr(entry,f.name)
            # optional:format datetimes for display
            if value is None:
                text = ""
            else:
                text = str(value)
            table.setItem(r,c,QTableWidgetItem  (text))
    return table

def show_log_table(dataset:DataSet,title:str = None,parent=None)->QDialog:
    if title is None or "":
        title = "Data Table"
    
    window = QDialog(parent)
    window.setWindowTitle(title)
    window.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
    window.setWindowFlags(window.windowFlags()
        |Qt.WindowType.WindowMaximizeButtonHint 
        |Qt.WindowType.WindowMinimizeButtonHint
    )
    table = create_log_table(dataset)
    layout = QVBoxLayout(window)
    layout.addWidget(table)
    window.show()


