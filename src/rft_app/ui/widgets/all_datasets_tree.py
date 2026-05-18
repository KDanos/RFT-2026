from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from project import ProjectDataManager


class AllDataSetsTree(QTreeWidget):
    def __init__(self, 
                parent:QWidget=None, 
                project: ProjectDataManager= None
                )->QTreeWidget:
        super().__init__(parent)

        self.parent = parent
        self.project = project
        self.loaded_datasets = self.project.loaded_datasets
        self.setHeaderLabel("Loaded Data Sets")
        
        
        for set in self.project.loaded_datasets:
            df = set.dataframe
            top_level = QTreeWidgetItem([set.name])
            # Add a top level item
            self.addTopLevelItem(top_level)
            
            # Add second level item of the dataframe shape
            row_count, column_count = df.shape
            text = f"Shape: {row_count} rows x {column_count} columns"
            top_level.addChild(QTreeWidgetItem([text]))
            top_level.setExpanded(True)

            # Add second level item of column headers
            column_level = QTreeWidgetItem(["Columns"])
            top_level.addChild(column_level)
            for idx, header in enumerate(df.columns):
                units = set.column_specs[idx].unit if set.column_specs[idx].unit else "no units"
                text = f"{header} [unit]"
                column_level.addChild(QTreeWidgetItem([text]))
