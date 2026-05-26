
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QSplitter, QTableWidget, QTreeWidget, QTreeWidgetItemIterator,QVBoxLayout, QWidget, QComboBox, QFrame
from qtpy.QtWidgets import QTableWidgetItem

from project import  LoadedDataSet, ProjectDataManager
from units import STANDARD_QUANTITIES,get_project_default_units
from .all_datasets_tree import AllDataSetsTree
from utils import get_tree_top_level_item_by_name,get_tree_item_by_name
import pandas as pd


class DataLoaderDialogAnalysis(QDialog):
    def __init__(self,
                parent:QWidget=None, 
                project:ProjectDataManager=None,
                )->None:
        super().__init__(parent)
        
        self.project = project
        self.df_analysis:pd.DataFrame = None
        # self.column_specs_analyis:list[ColumnSpec]= []
        self.selected_dataset = None
        self.selected_columns = []
        self.selected_columns_idx = []
        self._build_ui()
        self._connect_signals()
        
    def _build_ui(self)->None:

        #Build the window
        self.setWindowTitle("Data import for analysis")
        self.setWindowFlags(
            self.windowFlags()
            |Qt.WindowType.WindowMinimizeButtonHint
            |Qt.WindowType.WindowMaximizeButtonHint
        )
        
        #Build the main frames and splitter
        self.data_frame = QFrame(self)
        self.data_frame_layout = QVBoxLayout(self.data_frame)
        self.table_frame = QFrame(self)
        main_splitter = QSplitter(self)
        main_splitter.addWidget(self.data_frame)
        main_splitter.addWidget(self.table_frame)
        main_splitter.setSizes([2000,4000])

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(main_splitter)
        self.setLayout(self.main_layout)
        
        #Create the data tree
        self.loaded_data_tree = AllDataSetsTree(self.data_frame,self.project)
        self.data_frame_layout.addWidget(self.loaded_data_tree)
        self._make_tree_tristate_checkable(self.loaded_data_tree)

        #Create the table preview
        self.preview_table = QTableWidget()
        table_layout = QVBoxLayout(self.table_frame)
        table_layout.addWidget(self.preview_table)
        self.preview_table.setRowCount(20)
        self.preview_table.setColumnCount(10)
        self.preview_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self._update_table_headers()

    def _connect_signals(self)->None:
        self.loaded_data_tree.itemClicked.connect(self._select_only_one_dataset) 
        self.loaded_data_tree.itemChanged.connect(self._on_tree_item_changed)

    def _make_tree_tristate_checkable(self,tree:QTreeWidget)->None:
        it = QTreeWidgetItemIterator(tree)
        while item := it.value():
            item.setFlags(item.flags()
            |Qt.ItemFlag.ItemIsUserCheckable
            |Qt.ItemFlag.ItemIsAutoTristate
            )
            item.setCheckState(0, Qt.CheckState.Unchecked)
            
            #Move to next Tree Widget Item
            it +=1
        
        # #Connect signal to slot
        # self.loaded_data_tree.itemClicked.connect(self._select_only_one_dataset)      
    
    def _select_only_one_dataset(self, clicked, column:int)->None:
        """On any check, keep checks only under that item’s top-level dataset; uncheck all other datasets."""

        if column != 0:
            return
        if clicked.checkState(0)==Qt.CheckState.Unchecked:
            return
        self.loaded_data_tree.blockSignals(True)
        
        top_level_item = clicked

        while top_level_item.parent() is not None:
            top_level_item = top_level_item.parent()

        try:
            it = QTreeWidgetItemIterator(self.loaded_data_tree)
            while tree_item :=it.value():
                if tree_item.parent() is not None:
                    it += 1
                    continue
                if tree_item is top_level_item:            
                    it += 1
                    continue
                
                tree_item.setCheckState(0, Qt.CheckState.Checked)
                tree_item.setCheckState(0, Qt.CheckState.Unchecked)
                it += 1
        finally:
            self.loaded_data_tree.blockSignals(False)
        
    def _extract_dataset_and_columns(self,name)->tuple[LoadedDataSet,list[str]]:
        
        #Extract the selected dataset
        self.selected_dataset = self.project.get_loaded_dataset(name)
        
        # Extract the selected column names
        top_level_item = get_tree_top_level_item_by_name(self.loaded_data_tree,name)
        columns_node = get_tree_item_by_name(self.loaded_data_tree, top_level_item,"Columns")
        self.selected_columns = []
        self.selected_columns_idx = []
        for i in range(columns_node.childCount()):
            item = columns_node.child(i)
            if item.checkState(0)==Qt.CheckState.Checked:
                self.selected_columns.append(item.text(0))
                self.selected_columns_idx.append(i)

    #Extract the name of the dataset by identifying the top level item of the item emmiting the signal
    def _dataset_name_for_item(self, item)->str:
        top = item
        while top.parent() is not None:
            top = top.parent()
        return top.text(0)

    def _on_tree_item_changed(self, item, column:int)->None:
        if column !=0:
            return
        dataset_name = self._dataset_name_for_item(item)
        self._extract_dataset_and_columns(dataset_name)
        self._create_analysis_dataframe()
        self._update_table_headers()
        self._update_table_rows()
        self._update_table_values()

    def _update_table_headers(self)->None:     

        #Create the dimensions of the table
        if not self.selected_dataset or not self.selected_columns:
            column_count = 10
            header_list = [""]*10
            return
        else:
            column_count = len(self.selected_columns) 
            header_list = self.selected_columns 
        self.preview_table.setColumnCount(column_count)
        self.preview_table.setHorizontalHeaderLabels(header_list)
        
        if len(self.selected_columns)>0:
            all_columns = list(self.selected_dataset.dataframe.columns)
            
            for c in range(column_count):
                units_combo = QComboBox()
                header = header_list[c]
                idx = all_columns.index(header)
                quantity_key = self.selected_dataset.column_specs[idx].quantity_key
                units_list = STANDARD_QUANTITIES[quantity_key].units
                default_unit = get_project_default_units(self.project,quantity_key)
                units_combo.addItems(units_list)
                units_combo.setCurrentText(default_unit)
                self.preview_table.setCellWidget(0,c,units_combo)

    def _update_table_rows(self)->None:
        row_count, _ =self.selected_dataset.dataframe.shape
        self.preview_table.setRowCount(row_count+1)
        vert_headers = ["Units"]+[str(i+1) for i in range(row_count+1)]
        self.preview_table.setVerticalHeaderLabels(vert_headers)

    def _create_analysis_dataframe(self)->None:
        if not self.selected_dataset or not self.selected_columns:
            self.df_analysis = None
            return 
        self.df_analysis = self.selected_dataset.dataframe[self.selected_columns].copy()
    
    def _update_table_values(self):

        
        row_count, column_count = self.df_analysis.shape
        for c in range(column_count):
            for r in range(row_count):
                value = self.df_analysis.iat[r, c]
                display = str(value)
                self.preview_table.setItem(r+1,c,QTableWidgetItem(display))

        
        