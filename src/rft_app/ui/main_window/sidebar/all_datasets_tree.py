from PyQt6.QtCore import QPoint, QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QDialog, QMessageBox, QMenu, QTreeWidget, QTreeWidgetItem, QWidget

from project import DataSet, ProjectDataManager
from ui.main_window.sidebar.merge_datasets_dialog import MergeDatasetsDialog
from utilities import show_dataframe_table_dialog, show_import_log_or_user_comments_table


class AllDataSetsTree(QTreeWidget):
    dataset_renamed = pyqtSignal(str, str)  # old_name, new_name
    dataset_deleted = pyqtSignal(str)  # deleted name only
    merged_dataset_created = pyqtSignal()

    def __init__(
        self,
        dataset_list:list[DataSet],
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        label:str= "Dataset"
        
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.parent = parent
        self.project = project
        self.dataset_list= dataset_list
        self.label= label

        # Initialisation methods
        self.setHeaderLabel(self.label)
        self._connect_signals()

    #--------Private UI--------

    def _build_tree(self) -> None:
                
        for dataset in self.dataset_list:
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
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemChanged.connect(self._on_item_changed)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _create_menu_actions(self, item: QTreeWidgetItem) -> list[QAction]:
        list_of_actions: list[QAction] = []

        # Rename
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(
            lambda _checked=False, item=item: self._rename_item(item))
        list_of_actions.append(rename_action)

        # Delete
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            lambda _checked=False, item=item: self._delete_item(item))
        list_of_actions.append(delete_action)

        # Show Import Log
        show_import_log_action = QAction("Show Import log", self)
        show_import_log_action.triggered.connect(
            lambda _checked=False, item=item: 
            self._show_import_log_or_user_comment(item, "import_log"))
        list_of_actions.append(show_import_log_action)

        # Show Dataframe
        show_dataframe_action = QAction("Show Data", self)
        show_dataframe_action.triggered.connect(
            lambda _checked=False, item=item: self._show_data_table(item))
        list_of_actions.append(show_dataframe_action)

        # Show User Comments
        show_comments_action = QAction("Show Comments", self)
        show_comments_action.triggered.connect(
            lambda _checked=False, item=item: 
            self._show_import_log_or_user_comment(item, "user_comments"))
        list_of_actions.append(show_comments_action)

        # Merge Datasets
        merge_datasets_action = QAction("Merge Datasets", self)
        merge_datasets_action.triggered.connect(
            lambda _checked=False:
            self._merge_datasets())
        list_of_actions.append(merge_datasets_action)
        return list_of_actions

    def _delete_dataset(self, item: QTreeWidgetItem) -> None:
        dataset = item.data(0, Qt.ItemDataRole.UserRole)
        
        if dataset is None:
            return
        
        # Mutate the SAME list object that the project holds
        self.dataset_list[:]=[ds for ds in self.dataset_list if ds is not dataset]
        
        #Rename the deleted loaded dataset in the analyses_tree
        self._rename_deleted_dataset_on_analyses_tree(item)

        #Remove from UI
        index = self.indexOfTopLevelItem(item)
        if index >= 0:
            self.takeTopLevelItem(index)

        #Mark Modified and refresh analyses tree
        self.project.mark_modified()
        self.dataset_deleted.emit(dataset.name)

    def _delete_item(self, item: QTreeWidgetItem) -> None:
        if item.parent() is not None:  # only remove top level items for now
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Function",
            f"""Please confirmt deletion of {item.text(0)}. 
                    \n This action is not reversible""",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )  # default to No
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        self._delete_dataset(item)

    def _merge_datasets(self)->None:
        # Exit if a second dataset does not exist
        if len(self.project.all_datasets)<2:
            QMessageBox.critical(
                self, 
                "Merge Datasets", 
                "There must be at least 2 loaded or merged datasets available\n"
                "Please load more data via the 'Load Data' module first.")
            return
        
        dialog = MergeDatasetsDialog(self, self.project)
        dialog.accepted.connect(self.merged_dataset_created.emit)
        dialog.show()
    
    def _on_context_menu(self, position: QPoint) -> None:
        item = self.itemAt(position)
        if item is None:  # to ensure that menu is only build on non-white space
            return

        if item.parent() is not None:  # apply drop down menu only to top level items
            return

        menu_actions = self._create_menu_actions(item)
        menu = QMenu(self)
        for action in menu_actions:
            menu.addAction(action)

        menu.exec(self.viewport().mapToGlobal(position))

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

    def _rename_item(self, item: QTreeWidgetItem) -> None:
        if item.parent() is not None:
            return
        self.setCurrentItem(item, 0)  # focus on the row
        self.editItem(item, 0)  # open inline editor (like F2)

    def _show_data_table(self, item: QTreeWidgetItem) -> None:
        dataset = item.data(0, Qt.ItemDataRole.UserRole)
        df = dataset.dataframe
        column_specs = dataset.column_specs
        title = dataset.name
        show_dataframe_table_dialog(df, column_specs, title, self, self.project)

    def _show_import_log_or_user_comment(
        self,
        item: QTreeWidgetItem,
        table_type: str,
        ) -> None:
        dataset = item.data(0, Qt.ItemDataRole.UserRole)
        name = dataset.name
        show_import_log_or_user_comments_table(dataset, table_type, name, self)

    #--------Public API--------

    def reload_from_project(self, dataset_list:list[DataSet]|None = None) -> None:
        if dataset_list is not None:
            self.dataset_list = dataset_list #re-bind after set-project/open
        
        with QSignalBlocker(self):
            self.clear()
            self._build_tree()
