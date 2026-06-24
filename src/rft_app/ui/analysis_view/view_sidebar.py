from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QPushButton, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from qtpy.QtCore import QSignalBlocker
from qtpy.QtWidgets import QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities import make_tree_item_checkable
from ui.widgets import DataframeTree



class ViewSidebar(QFrame):
    #Custom Singnals
    view_df_changed = pyqtSignal()
    
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
        self._connect_signals()

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
        with QSignalBlocker(self.data_tree):
            make_tree_item_checkable(self.data_tree.columns_level)
        #Block the depth, formation Presure and excess pressure from being un-checkable
        self._make_items_not_selectable(self.data_tree, self.data_tree.columns_level,3)

    def _connect_signals(self):
        self.data_tree.itemChanged.connect(self._on_column_selection_change)

    def _on_column_selection_change(self, item:QTreeWidgetItem, column:int)->None:
        if column != 0: #checkboxes are in column 0
            return
        
        if item.parent() is not self.data_tree.columns_level:
            return
        #Relock the first 3 levels
        index = item.parent().indexOfChild(item)
        if index<=1:
            with QSignalBlocker(self.data_tree):
                item.setCheckState(0,Qt.CheckState.Checked)
                print (f"i is {index} and you cant touch that")
                return

        self.view_df_changed.emit()

    def _make_items_not_selectable (self, tree: QTreeWidget,node: QTreeWidgetItem,  count:int)->None:
        for i in range(count):
            item = node.child(i)
            item.setFlags (Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsUserCheckable)
