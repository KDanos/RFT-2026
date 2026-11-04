from PyQt6.QtCore import QPoint, Qt, pyqtSignal, QSignalBlocker
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFrame, QMenu, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.main_window.project_signals import ProjectSignals
from ui.widgets.dialog_edit_analysis_dataset import DialogEditViewAnalysisDataSet
from utilities import make_tree_item_checkable
from ui.widgets import DataframeTree


class TabularSidebar(QFrame):
    view_df_changed = pyqtSignal()

    # Inherited variables
    # None

    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        analysis: AnalysisObject | None = None,
        view: AnalysisView | None = None,
        signals: ProjectSignals | None = None,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager | None = project
        self.analysis: AnalysisObject | None = analysis
        self.view: AnalysisView | None = view
        self.signals: ProjectSignals | None = signals

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)

        self.build_analysis_data_tree()

    def _connect_signals(self) -> None:
        self.connect_analysis_data_tree_signals()

    def _make_items_not_selectable(
        self,
        tree: QTreeWidget,
        node: QTreeWidgetItem,
        count: int,
        ) -> None:
        for i in range(count):
            item = node.child(i)
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable)

    def _on_change_analysis_dataset_requested(self)->None:
        dlg = DialogEditViewAnalysisDataSet(
            parent = self, 
            project = self.project,
            analysis = self.analysis, 
            signals = self.signals
           )
               
        dlg.exec()

    def _on_column_selection_change(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return

        if item.parent() is not self.analysis_data_tree.columns_level:
            return
        index = item.parent().indexOfChild(item)
        if index <= 1:
            with QSignalBlocker(self.analysis_data_tree):
                item.setCheckState(0, Qt.CheckState.Checked)
                return
        self.view_df_changed.emit()

    def _on_data_tree_context_menu_requested(self, position:QPoint)-> None:
        tree = self.analysis_data_tree
        
        #Define the actions
        self.actionChangeAnalysisDataset = QAction("Change Analysis Dataset",tree)
        self.actionChangeAnalysisDataset.triggered.connect(self._on_change_analysis_dataset_requested)
        # Define the menu
        menu = QMenu(tree)
        menu.addAction(self.actionChangeAnalysisDataset)
        pos = tree.mapToGlobal(position)
        # Call the menu
        menu.exec(pos)

    #--------Public API--------

    def build_analysis_data_tree(self) -> None:
        
        # Clear an existing analyisis data tree, if present
        old = getattr(self, "analysis_data_tree", None)
        if old:
            self.main_layout.removeWidget(old)
            old.deleteLater()

        # Build a new instance of the analysis data tree
        analysis_dataset = self.analysis.analysis_dataset
        self.analysis_data_tree = DataframeTree(self, analysis_dataset, "Analysis Data")
        self.analysis_data_tree.header().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_layout.addWidget(self.analysis_data_tree)
        with QSignalBlocker(self.analysis_data_tree):
            make_tree_item_checkable(self.analysis_data_tree.columns_level)
        self._make_items_not_selectable(self.analysis_data_tree, self.analysis_data_tree.columns_level, 2)
        self.sync_checkboxes_from_view(self.view)

    def connect_analysis_data_tree_signals(self) -> None:
        self.analysis_data_tree.itemChanged.connect(self._on_column_selection_change)
        self.analysis_data_tree.header().customContextMenuRequested.connect(self._on_data_tree_context_menu_requested)


    def get_selected_columns_names(self) -> list[str]:
        names = []
        columns_level = self.analysis_data_tree.columns_level
        for i in range(columns_level.childCount()):
            item = columns_level.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                names.append(item.text(0))
        return names

    def sync_checkboxes_from_view(self, view: AnalysisView) -> None:
        """On open, reflect which optional columns are currently in view.df"""
        view_optional = set(view.df.columns[3:])
        with QSignalBlocker(self.analysis_data_tree):
            columns_level = self.analysis_data_tree.columns_level
            for i in range(2, columns_level.childCount()):
                item = columns_level.child(i)
                checked = item.text(0) in view_optional
                item.setCheckState(
                    0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )
