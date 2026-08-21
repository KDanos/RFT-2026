from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from .analyses_tree_functions import on_all_analyses_tree_context_menu


class AnalysesTree(QTreeWidget):
    analysis_renamed = pyqtSignal()
    analysis_deleted = pyqtSignal()
    analysis_visibility_changed = pyqtSignal()
    new_view_requested = pyqtSignal(AnalysisObject)

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
        # (none)

        # Initialisation methods
        self.setHeaderLabel("Analyses")
        self._connect_signals()

    #--------Private UI--------

    def _build_tree(self) -> None:
        # Create the drop down menu options on right click of the menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        for analysis in self.project.analyses:
            #Add the top level item
            text = analysis.name
            if not analysis.is_visible:
                text = text + " [hidden]"
            top_level = QTreeWidgetItem([text])
            top_level.setFlags(top_level.flags() | Qt.ItemFlag.ItemIsEditable)
            top_level.setData(0, Qt.ItemDataRole.UserRole, analysis)
            top_level.setExpanded(True)
            self.addTopLevelItem(top_level)

            # Add the second level items
            # Dataset
            dataset_node = QTreeWidgetItem(["Dataset:"])
            top_level.addChild(dataset_node)
            dataset_node.setData(0, Qt.ItemDataRole.UserRole, analysis.analysis_dataset)

            # Dataframe shape
            rows, col = analysis.analysis_dataset.dataframe.shape
            shape_item = QTreeWidgetItem([f"Shape: {rows} rows x {col} columns"])
            dataset_node.addChild(shape_item)
            # Dataframe Columns
            column_item = QTreeWidgetItem(["Columns"])
            dataset_node.addChild(column_item)
            for header in analysis.analysis_dataset.dataframe.columns:
                item = QTreeWidgetItem([header])
                column_item.addChild(item)

            #Source Data
            source_node = QTreeWidgetItem(["Source Datasets:"])
            top_level.addChild(source_node)
            for name in analysis.source_datasets:
                source_node.addChild(QTreeWidgetItem([name]))

            #Depth reference
            text = f"Depth Column: {analysis.vert_depth_src_col}"
            top_level.addChild(QTreeWidgetItem([text]))

            # Pressure reference
            text = f"Pressure Column: {analysis.formation_pres_src_col}"
            top_level.addChild(QTreeWidgetItem([text]))

            #Displayed dataframe
            #hold, not sure what this represents yet

            #Analysis frame
            view_node = QTreeWidgetItem(["Analysis Views:"])
            top_level.addChild(view_node)
            for view in analysis.analysis_views:
                text = view.name
                if not view.is_visible:
                    text = text + " [hidden]"
                view_item = QTreeWidgetItem([text])
                view_item.setFlags(view_item.flags() | Qt.ItemFlag.ItemIsEditable)
                view_item.setData(0, Qt.ItemDataRole.UserRole, view)
                view_node.addChild(view_item)

    def _connect_signals(self) -> None:
        self.itemChanged.connect(self._on_item_changed)
        self.customContextMenuRequested.connect(
            lambda position: on_all_analyses_tree_context_menu(self, position)
        )

    def _delete_analysis(self, item: QTreeWidgetItem) -> None:
        analysis = item.data(0, Qt.ItemDataRole.UserRole)
        if analysis is None:
            return

        if analysis not in self.project.analyses:
            return

        self.project.analyses = [a for a in self.project.analyses if a is not analysis]
        self.project.mark_modified()
        self.analysis_deleted.emit()

    def _on_item_changed(self, item: QTreeWidgetItem, col: int) -> None:
        if col != 0:
            return

        obj = item.data(0, Qt.ItemDataRole.UserRole)

        if obj is None:
            return

        if isinstance(obj, AnalysisObject):
            self._rename_analysis(item)
        elif isinstance(obj, AnalysisView):
            self._rename_view(item)

    def _rename_analysis(self, item: QTreeWidgetItem) -> None:
        analysis = item.data(0, Qt.ItemDataRole.UserRole)
        analysis.name = item.text(0).strip()
        self.analysis_renamed.emit()
        self.project.mark_modified()

    def _rename_view(self, item: QTreeWidgetItem) -> None:
        view = item.data(0, Qt.ItemDataRole.UserRole)
        view.name = item.text(0).strip()
        self.analysis_visibility_changed.emit()
        self.project.mark_modified()

    #--------Public API--------

    def reload_from_project(self) -> None:
        with QSignalBlocker(self):
            self.clear()
            self._build_tree()
