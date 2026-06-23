from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QPushButton, QTreeWidgetItem, QTreeWidgetItemIterator
from qtpy.QtCore import QSignalBlocker
from qtpy.QtWidgets import QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities import get_tree_item_by_name, get_tree_top_level_item_by_name, make_tree_item_checkable
from ui.widgets import DataframeTree



class ViewSidebar(QFrame):
    
    def __init__(self,
                parent: QWidget|None = None,
                project: ProjectDataManager|None =None,
                analysis: AnalysisObject|None = None,
                view: AnalysisView|None = None ):
        super().__init__(parent)

        #Pass on the working variables
        self.project = project
        self.analysis = analysis
        self.view = view

        #Build the sidebar
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        btn1 = QPushButton("placeholder 11")
        btn2 = QPushButton("placeholder 12")
        self.main_layout.addWidget(btn1)
        self.main_layout.addWidget(btn2)
        
        # Build the data tree
        analysis_dataset = self.analysis.analysis_dataset
        self.data_tree = DataframeTree(self,analysis_dataset,"Data")
        self.main_layout.addWidget(self.data_tree)
        #Make the column headers checkable
        tree_top_level = get_tree_top_level_item_by_name(self.data_tree, self.data_tree.dataset.name)
        columns_item = get_tree_item_by_name(self.data_tree, tree_top_level, "Columns")
        with QSignalBlocker(self.data_tree):
            make_tree_item_checkable(columns_item)

    def _connect_signals(self):
        self.data_tree.itemChanged.connect(self._on_column_selection_change)

    def _on_column_selection_change(self, item:QTreeWidgetItem, column:int):->None:
        _get