from datetime import datetime
from typing import Any, Callable, Iterable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,QCheckBox, QDialog, QSpinBox, 
                            QTableWidget, QVBoxLayout,QFrame, QHBoxLayout, QPushButton, QSplitter, QTableWidgetItem)
import pandas as pd
from dataclasses import fields

from qtpy.QtWidgets import QTableView

from project.models import ColumnSpec, DataSet, DataSetLogEntry

from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units


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

def round_value_to_decimal_points(
                                value:Any, #str | int | float
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

def create_dataframe_table( df:pd.DataFrame, 
                            column_specs:list[ColumnSpec]|None=None, 
                            parent = None, 
                            project = None
                                )->QTableWidget:
    from ui.widgets.table_widgets import UnitsComboBox
    
    rows, columns = df.shape
    data_table = QTableWidget(rows+1, columns,parent)
    data_table.setHorizontalHeaderLabels([str(column) for column in df.columns])
    
    def update_column_values(c:int):
        units_combo = data_table.cellWidget(0,c)

        if units_combo is None:
            return
        
        quantity_key = column_specs[c].quantity_key
        output_unit = units_combo.currentText()
        qty = STANDARD_QUANTITIES.get(quantity_key,STANDARD_QUANTITIES["undefined"])

        for r in range(rows):
            normalised_value = df.iat[r,c]
           
            if pd.isna(normalised_value):
                display = ""
            elif qty.is_numeric:
                converted = convert_from_normalised_to_user_units(
                    output_unit, quantity_key, normalised_value)
                display = str(converted)
            else:
                display = normalised_value

            item = QTableWidgetItem(str(display))
            data_table.setItem(r+1,c,item)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    for c in range(columns):
        #Create the units combo box
        quantity_key = column_specs[c].quantity_key
        units_combo = UnitsComboBox(quantity_key,project)
        data_table.setCellWidget(0,c,units_combo)
        # units_combo.currentIndexChanged.connect (lambda _index, col=c: update_column_values(col))
        
        #Fill in the rows of the column
        update_column_values(c)

    return data_table, update_column_values

def show_dataframe_table_dialog(
    df:pd.DataFrame,
    column_specs:list[ColumnSpec]|None=None,
    title:str=None, 
    parent=None,
    project = None
    )->QDialog:
    if not title:
        title = "Data Table"
    # Define the dialog window
    window = QDialog(parent)
    window.setWindowTitle(f"Data Table: {title}")
    window.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
    window.setWindowFlags(window.windowFlags()
        |Qt.WindowType.WindowMaximizeButtonHint 
        |Qt.WindowType.WindowMinimizeButtonHint
    )
    _,table_window,_ = create_table_view_frame(df, column_specs,parent, project)
    window_layout = QVBoxLayout(window)
    window_layout.setContentsMargins(0,0,0,0)
    window_layout.addWidget(table_window)
    window.show()
   
def create_table_view_frame(
    df:pd.DataFrame,
        column_specs:list[ColumnSpec]|None=None,
    parent=None,
    project = None
    )->(QFrame, QTableWidget, Callable[[int],None] ):
    
    frame = QFrame(parent)
    # Create the main layout
    main_layout = QVBoxLayout(frame)
    widgets_frame = QFrame(frame)
    table_frame = QFrame(frame)
    splitter= QSplitter(frame)
    splitter.addWidget(widgets_frame)
    splitter.addWidget(table_frame)
    splitter.setSizes([10000,50000])
    main_layout.addWidget(splitter)

    # Create and add the table
    table, update_column_values = create_dataframe_table(df,column_specs, table_frame,project )
    table_layout = QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0,0,0,0)
    table_layout.addWidget(table)

    # Create Table widgets
    widget_layout = QVBoxLayout(widgets_frame)

    # Define number of decimals to view
    decimals_container = QHBoxLayout()
    decimals_check_box = QCheckBox("Round decimals")
    decimals_check_box.setCheckState(Qt.CheckState.Checked)
    decimal_limit_spin = QSpinBox()
    decimal_limit_spin.setValue(1)
    decimal_limit_spin.setMaximum(10000)
    decimal_limit_spin.setEnabled(True)
    decimals_container.addWidget(decimals_check_box)
    decimals_container.addWidget(decimal_limit_spin)
    widget_layout.addStretch()  # pushes everything below it
    widget_layout.addLayout(decimals_container)

    # Ensure manual typing works in the decimals spinbox
    decimal_limit_spin.setReadOnly(False)
    decimal_limit_spin.lineEdit().setReadOnly(False)
    decimal_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    decimal_limit_spin.setKeyboardTracking(False)

    def apply_rounding_to_column(col:int)->None:
        for row in range(1,table.rowCount()):
            item = table.item(row, col)
            if item is None: 
                continue
            rounded_value =round_value_to_decimal_points(
                item.text(),decimals_check_box, decimal_limit_spin)
            item.setText(rounded_value)

    def refresh_column(col:int)->None:
        update_column_values(col)       #convert units (from create dataframe_table)
        apply_rounding_to_column(col)   # round (only frame knows these widgets)
    
    def refresh_all_columns()->None:
        for col in range(table.columnCount()):
            refresh_column(col)

    def _connect_signals():
        #Connect all units_combo_boxes
        for col in range (table.columnCount()):
            units_combo = table.cellWidget(0,col)
            units_combo.currentIndexChanged.connect(
                lambda _index, column_idx = col: refresh_column(column_idx)
            )
        decimal_limit_spin.valueChanged.connect(lambda _v: refresh_all_columns())
        decimals_check_box.toggled.connect (lambda _checked: refresh_all_columns())
    
    _connect_signals()
    refresh_all_columns()
    
    return frame, table, update_column_values

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
    
    for r, entry in enumerate(dataset.info_log):
        for c, f in enumerate(log_fields):  
            value = getattr(entry,f.name)
            # optional:format datetimes for display
            if value is None:
                text = ""
            elif isinstance(value, datetime):
                text = value.strftime("%Y-%m-%d %H:%M")
            else:
                text = str(value)
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(r,c,item)
    return table

def show_log_table(dataset:DataSet,title:str = None,parent=None)->QDialog:
    if title is None or "":
        title = "Data Table"
    
    #Define the dialog window
    window = QDialog(parent)
    window.setWindowTitle(f"Log Table: {title}")
    window.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
    window.setWindowFlags(window.windowFlags()
        |Qt.WindowType.WindowMaximizeButtonHint 
        |Qt.WindowType.WindowMinimizeButtonHint
    )
    #Create the main layout
    main_layout = QVBoxLayout(window)
    widgets_frame = QFrame(window)
    table_frame = QFrame(window)
    splitter= QSplitter(window)
    splitter.addWidget(widgets_frame)
    splitter.addWidget(table_frame)
    splitter.setSizes([1000,5000])
    main_layout.addWidget(splitter)
    
    #Create and add the table
    table = create_log_table(dataset,table_frame)
    table_layout= QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0,0,0,0)
    table_layout.addWidget(table)
    
    # Create Table widgets
    widget_layout = QVBoxLayout(widgets_frame)
    bt1 = QPushButton()
    bt1.setText("button 1")
    widget_layout.addWidget(bt1)

    bt2 = QPushButton()
    bt2.setText("button 2")
    widget_layout.addWidget(bt2)

    window.show()

def make_tree_item_checkable(item:QTreeWidgetItem)->None:
    for idx in range(item.childCount()):     
        column_item = item.child(idx)
        column_item.setFlags(column_item.flags()
        |Qt.ItemFlag.ItemIsUserCheckable
        )
        column_item.setCheckState(0, Qt.CheckState.Checked)

