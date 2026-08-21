from PyQt6.QtWidgets import QTreeWidget, QWidget, QTreeWidgetItem
from project import DataSet


class DataframeTree(QTreeWidget):
    def __init__(self, 
                parent: QWidget | None = None, 
                dataset: DataSet | None = None,
                title: str ="") -> None:
        super().__init__(parent)
        
        if dataset is None:
            raise ValueError("DataFrameTree requires a LoadedDataSet")
        self.dataset = dataset
        self.setHeaderLabel(title)
        self._design_tree()
        
    def _design_tree(self):
        #Create the dataframe object
        df = self.dataset.dataframe
        
        #Add the top level
        self.top_level = QTreeWidgetItem([self.dataset.name])
        self.addTopLevelItem(self.top_level)

        #Add second level item of dataframe shape
        row_count, column_count = df.shape
        text = f"Shape: {row_count} rows x {column_count} columns"
        self.top_level.addChild (QTreeWidgetItem ([text]))
        self.top_level.setExpanded (True)

        #Add second level item of column headers
        self.columns_level = QTreeWidgetItem(["Columns"])
        self.top_level.addChild(self.columns_level)
        for c,header in enumerate(df.columns):            
            header_item = QTreeWidgetItem([(header)])
            self.columns_level.addChild(header_item)

def make_tree_item_tristate(self)->None:
    pass



        
        

        