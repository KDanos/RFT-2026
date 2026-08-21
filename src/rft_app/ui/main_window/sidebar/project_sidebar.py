from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QFrame, QTreeWidget, QVBoxLayout, QWidget

from project import ProjectDataManager
from .all_datasets_tree import AllDataSetsTree
from .analyses_tree import AnalysesTree


class ProjectSidebar(QFrame):
    """Left Panel: Data and Analysis Trees"""

    def __init__(
        self,
        project: ProjectDataManager,
        parent: QWidget | None = None,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()
        self._connect_signals()
        self.refresh()

    #--------Private UI--------

    def _apply_column_units_to_tree(self, tree: QTreeWidget) -> None:
        """Append the on-load units labels to the columns names in the dataset tree"""
        with QSignalBlocker(tree):
            for i in range(tree.topLevelItemCount()):
                dataset_name = tree.topLevelItem(i).text(0)
                columns_node = tree.topLevelItem(i).child(1)
                dataset = self.project.get_dataset_by_name(dataset_name)
                if dataset is None or columns_node is None:
                    continue

                for k in range(columns_node.childCount()):
                    col_item = columns_node.child(k)
                    header = col_item.text(0).split(" [")[0]
                    units = dataset.column_specs[k].unit
                    text = f"{header} [{units}]" if units else f"{header}"
                    col_item.setText(0, text)

    def _build_ui(self) -> None:
        # Create a frame to hold the data trees
        self.project_data_frame = QFrame(self)
        self.data_trees_layout = QVBoxLayout(self.project_data_frame)

        #Create the loaded datasets tree
        self.all_loaded_datasets_tree = AllDataSetsTree(self.project_data_frame, self.project)
        self.data_trees_layout.addWidget(self.all_loaded_datasets_tree)

        #Create a frame to hold analyses tree
        self.project_analyses_frame = QFrame(self)
        self.analyses_tree_layout = QVBoxLayout(self.project_analyses_frame)

        #Create the analyses tree
        self.all_analyses_tree = AnalysesTree(self.project_analyses_frame, self.project)
        self.analyses_tree_layout.addWidget(self.all_analyses_tree)

        #Create the main sidebar layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.project_data_frame)
        layout.addWidget(self.project_analyses_frame)

    def _connect_signals(self) -> None:
        # Loaded Datasets Tree
        self.all_loaded_datasets_tree.dataset_renamed.connect(self.refresh_all_analyses_tree)
        self.all_loaded_datasets_tree.dataset_deleted.connect(self.refresh_all_analyses_tree)

        # Analyses Tree
        self.all_analyses_tree.analysis_renamed.connect(self.refresh_all_analyses_tree)
        self.all_analyses_tree.analysis_deleted.connect(self.refresh_all_analyses_tree)

    #--------Public API--------

    def refresh(self) -> None:
        """Reload all tree from the current project"""
        self.refresh_all_loaded_datasets_tree()
        self.refresh_all_analyses_tree()

    def refresh_all_analyses_tree(self) -> None:
        self.all_analyses_tree.project = self.project
        self.all_analyses_tree.reload_from_project()

    def refresh_all_loaded_datasets_tree(self) -> None:
        self.all_loaded_datasets_tree.project = self.project
        self.all_loaded_datasets_tree.reload_from_project()
        self._apply_column_units_to_tree(self.all_loaded_datasets_tree)

    def set_project(self, project: ProjectDataManager) -> None:
        self.project = project
        self.all_loaded_datasets_tree.project = project
        self.all_analyses_tree.project = project
