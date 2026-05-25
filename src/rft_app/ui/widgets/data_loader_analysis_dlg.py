
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QTreeWidgetItemIterator,QVBoxLayout, QWidget


from project import  ColumnSpec, ProjectDataManager
from .all_datasets_tree import AllDataSetsTree

import pandas as pd


class DataLoaderDialogAnalysis(QDialog):
    def __init__(self,
                parent:QWidget=None, 
                project:ProjectDataManager=None,
                )->None:
        super().__init__(parent)

        self.project = project
        self.df_analysis:pd.DataFrame = None
        self.column_specs_analyis:list[ColumnSpec]= []
        self.main_layout = QVBoxLayout(self)

        #Create the loaded data tree and make items checkable
        self.loaded_data_tree = AllDataSetsTree(self,self.project)
        
        it = QTreeWidgetItemIterator(self.loaded_data_tree)
        while item := it.value():
            item.setFlags(item.flags()
            |Qt.ItemFlag.ItemIsUserCheckable
            |Qt.ItemFlag.ItemIsAutoTristate
            )
            item.setCheckState(0, Qt.CheckState.Unchecked)
            
            #Move to next Tree Widget Item
            it +=1
        
        # Add the widget to the frame
        self.main_layout.addWidget(self.loaded_data_tree)
        
        #Connect signal to slot
        self.loaded_data_tree.itemClicked.connect(self._select_only_one_dataset)
    
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
        



        
        