
from PyQt6.QtWidgets import QDialog
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget

from project import AnalysisObject, ColumnSpec, ProjectDataManager
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
        for dataset in project.loaded_datasets:
            label = QLabel(dataset.name)
            self.main_layout.addWidget(label)
