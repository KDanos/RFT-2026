from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QPushButton, QTreeWidget, QTreeWidgetItem
from qtpy.QtCore import QSignalBlocker
from qtpy.QtWidgets import QDialog, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities.filterable_table.filterable_table import FilterableTableView
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

        self.project = project
        self.analysis = analysis
        self.view = view

        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.btn1 = QPushButton("Test Filtered Table View")
        self.btn2 = QPushButton("placeholder 12")
        self.main_layout.addWidget(self.btn1)
        self.main_layout.addWidget(self.btn2)
        
        analysis_dataset = self.analysis.analysis_dataset
        self.data_tree = DataframeTree(self,analysis_dataset,"Data")
        self.main_layout.addWidget(self.data_tree)
        with QSignalBlocker(self.data_tree):
            make_tree_item_checkable(self.data_tree.columns_level)
        self._make_items_not_selectable(self.data_tree, self.data_tree.columns_level,2)
        self.sync_checkboxes_from_view(self.view)

    def _connect_signals(self):
        self.data_tree.itemChanged.connect(self._on_column_selection_change)
        self.btn1.clicked.connect(self._test_filterable_table)
        

    def _on_column_selection_change(self, item:QTreeWidgetItem, column:int)->None:
        if column != 0:
            return
        
        if item.parent() is not self.data_tree.columns_level:
            return
        index = item.parent().indexOfChild(item)
        if index<=1:
            with QSignalBlocker(self.data_tree):
                item.setCheckState(0,Qt.CheckState.Checked)
                return
        self.view_df_changed.emit()

    def _make_items_not_selectable (self, tree: QTreeWidget,node: QTreeWidgetItem,  count:int)->None:
        for i in range(count):
            item = node.child(i)
            item.setFlags (Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsUserCheckable)

    def get_selected_columns_names (self)->list[str]:
        names = []
        columns_level = self.data_tree.columns_level
        for i in range(columns_level.childCount()):
            item = columns_level.child(i)
            if item.checkState(0)==Qt.CheckState.Checked:
                names.append(item.text(0))
        return names          
    
    def sync_checkboxes_from_view(self, view:AnalysisView)->None:
        """On open, reflect which optional columns are currently in view.df"""
        if view.df is None:
            return
        
        view_optional = set(view.df.columns[3:])
        with QSignalBlocker(self.data_tree):
            columns_level = self.data_tree.columns_level
            for i in range(2, columns_level.childCount()):
                item = columns_level.child(i)
                checked = item.text(0) in view_optional
                item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _test_filterable_table(self)->None:
        window = QDialog(self)
        table_view = FilterableTableView(self,self.project, self.analysis, self.view)
        table_frame= table_view.frame
        window_layout = QVBoxLayout(window)
        window_layout.addWidget(table_frame)
        window.show()