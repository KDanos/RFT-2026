from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from project import ProjectDataManager
from .all_datasets_tree_functions import on_all_dataset_tree_context_menu


class AllDataSetsTree(QTreeWidget):
    dataset_renamed = pyqtSignal(str, str)  # old_name, new_name
    dataset_deleted = pyqtSignal(str)  # deleted name only

    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.parent = parent
        self.project = project

        # Set module variables
        self.datasets = self.project.datasets

        # Initialisation methods
        self.setHeaderLabel("Loaded Data Sets")
        self._connect_signals()

    #--------Private UI--------

    def _build_tree(self) -> None:
        #Create the drop down menu options on right click a tree item
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        for dataset in self.project.datasets:
            df = dataset.dataframe
            # Add a top level item
            top_level = QTreeWidgetItem([dataset.name])
            top_level.setFlags(top_level.flags() | Qt.ItemFlag.ItemIsEditable)
            top_level.setData(0, Qt.ItemDataRole.UserRole, dataset)  # store dataset for later
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
                text = header
                column_level.addChild(QTreeWidgetItem([text]))

    def _connect_signals(self) -> None:
        self.itemChanged.connect(self._on_item_changed)
        self.customContextMenuRequested.connect(
            lambda position: on_all_dataset_tree_context_menu(self, position)
        )

    def _delete_dataset(self, item: QTreeWidgetItem) -> None:
        dataset = item.data(0, Qt.ItemDataRole.UserRole)
        if dataset is None:
            return

        #Rename the deleted loaded dataset in the analyses_tree
        self._rename_deleted_dataset_on_analyses_tree(item)

        #Remove from the project model
        self.project.datasets = [ds for ds in self.project.datasets if ds is not dataset]

        #Remove from UI
        index = self.indexOfTopLevelItem(item)
        if index >= 0:
            self.takeTopLevelItem(index)

        #Mark Modified and refresh analyses tree
        self.project.mark_modified()
        self.dataset_deleted.emit(dataset.name)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if item.parent() is not None:  # only execute on top level items
            return
        old_name = item.data(0, Qt.ItemDataRole.UserRole).name
        self._rename_dataset(old_name, item)

    def _rename_dataset(self, old_name: str, item: QTreeWidgetItem) -> None:
        dataset = item.data(0, Qt.ItemDataRole.UserRole)
        dataset.name = item.text(0).strip()

        #look for the old name in the analyses reference of loaded datasets
        for analysis in self.project.analyses:
            for idx, name in enumerate(analysis.source_datasets):
                if name == old_name:
                    analysis.source_datasets[idx] = dataset.name

        self.dataset_renamed.emit(old_name, dataset.name)
        self.project.mark_modified()

    def _rename_deleted_dataset_on_analyses_tree(self, item: QTreeWidgetItem) -> None:
        dataset = item.data(0, Qt.ItemDataRole.UserRole)
        deleted_name = dataset.name

        #look for the deleted name in the analyses reference of loaded datasets
        for analysis in self.project.analyses:
            for idx, name in enumerate(analysis.source_datasets):
                if name == deleted_name:
                    analysis.source_datasets[idx] = deleted_name + " [deleted]"

    #--------Public API--------

    def reload_from_project(self) -> None:
        with QSignalBlocker(self):
            self.clear()
            self._build_tree()
