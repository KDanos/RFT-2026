from PyQt6.QtWidgets import QTreeWidget, QWidget, QTreeWidgetItem
import pandas as pd
from project import LoadedDataSet


class DataFrameTree(QTreeWidget):
    def __init__(self, 
                parent: QWidget | None = None, 
                loaded_dataset: LoadedDataSet | None = None,
                ) -> None:
        super().__init__(parent)
        
        if loaded_dataset is None:
            raise ValueError("DataFrameTree requires a LoadedDataSet")
        self.loaded_dataset = loaded_dataset
        self.setHeaderLabel(self.loaded_dataset.name)
        self._design_tree()
        
    def _design_tree(self):
        #Create the dataframe object
        df = self.loaded_dataset.dataframe
        
        #Add the top level
        self.top_level = QTreeWidgetItem([self.loaded_dataset.name])
        self.addTopLevelItem(self.top_level)

        #Add second level item of dataframe shape
        row_count, column_count = df.shape
        text = f"Shape: {row_count} rows x {column_count} columns"
        self.top_level.addChild (QTreeWidgetItem ([text]))
        self.top_level.setExpanded (True)

        #Add second level item of column headers
        self.columns_level = QTreeWidgetItem(["Columns"])
        self.top_level.addChild(self.columns_level)
        for idx,header in enumerate(df.columns):
            header_text = header 
            unit = self.loaded_dataset.column_specs[idx].unit if not self.loaded_dataset.column_specs[idx].unit=="" else "no units"
            column_text = f"{header_text} [{unit}]"
            self.columns_level.addChild(QTreeWidgetItem([column_text]))




        
        

        