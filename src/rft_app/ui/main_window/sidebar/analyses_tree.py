from PyQt6.QtCore import QPoint, QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMessageBox, QTreeWidget, QTreeWidgetItem, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities import show_dataframe_table_dialog


class AnalysesTree(QTreeWidget):
    analysis_renamed = pyqtSignal(AnalysisObject)
    analysis_deleted = pyqtSignal()
    analysis_visibility_changed = pyqtSignal(object, object)  # (AnalysisObject | None, AnalysisView | None)
    fluids_changed = pyqtSignal()
    new_view_requested = pyqtSignal(AnalysisObject)

    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.parent: QWidget | None = parent
        self.project: ProjectDataManager | None = project

        # Set module variables
        # (none)

        # Initialisation methods
        self.setHeaderLabel("Analyses")
        self._connect_signals()

    #--------Private UI--------

    def _add_a_view(self, item: QTreeWidgetItem) -> None:
        while item.parent() is not None:
            item = item.parent()

        analysis = item.data(0, Qt.ItemDataRole.UserRole)
        self.new_view_requested.emit(analysis)

    def _build_tree(self) -> None:
        for analysis in self.project.analyses:
            # Add the top level item
            text = analysis.name
            if not analysis.is_visible:
                text = text + " [hidden]"
            top_level = QTreeWidgetItem([text])
            top_level.setFlags(top_level.flags() | Qt.ItemFlag.ItemIsEditable)
            top_level.setData(0, Qt.ItemDataRole.UserRole, analysis)
            top_level.setExpanded(True)
            self.addTopLevelItem(top_level)

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

            # Source Data
            source_node = QTreeWidgetItem(["Source Datasets:"])
            top_level.addChild(source_node)
            for name in analysis.source_datasets:
                source_node.addChild(QTreeWidgetItem([name]))

            # Depth reference
            text = f"Depth Column: {analysis.vert_depth_src_col}"
            top_level.addChild(QTreeWidgetItem([text]))

            # Pressure reference
            text = f"Pressure Column: {analysis.formation_pres_src_col}"
            top_level.addChild(QTreeWidgetItem([text]))

            # Displayed dataframe
            # hold, not sure what this represents yet

            # Fluids
            fluids_node = QTreeWidgetItem(["Fluids:"])
            top_level.addChild(fluids_node)
            for fluid in analysis.fluids:
                fluid_item = QTreeWidgetItem([fluid.name])
                fluid_item.setData(0, Qt.ItemDataRole.UserRole, fluid)
                fluids_node.addChild(fluid_item)

                fluid_type = QTreeWidgetItem([fluid.type])
                fluid_item.addChild(fluid_type)

                if fluid.gradient_si is not None:
                    gradient = fluid.values_in_project_units(
                        self.project,
                        "pressure_gradient",
                        fluid.gradient_si,
                    )
                    pressure_gradient_unit = (
                        self.project.current_unit_system.units_by_quantity[
                            "pressure_gradient"
                        ]
                    )
                    gradient_text = f"{gradient:.3} [{pressure_gradient_unit}]"
                    fluid_item.addChild(QTreeWidgetItem([gradient_text]))

                if fluid.zero_pressure_depth_si is not None:
                    zero_depth = fluid.values_in_project_units(
                        self.project,
                        "length",
                        fluid.zero_pressure_depth_si,
                    )
                    depth_unit = (
                        self.project.current_unit_system.units_by_quantity["length"]
                    )
                    zero_depth_text = f"0 pressure at {zero_depth:.3} [{depth_unit}]"
                    fluid_item.addChild(QTreeWidgetItem([zero_depth_text]))

                contact_item = QTreeWidgetItem(["Underlying Contact"])
                fluid_item.addChild(contact_item)

            # Analysis Views
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

    def _capture_expanded_paths(self) -> set[tuple[str, ...]]:
        expanded_nodes: set[tuple[str, ...]] = set()

        def walk(item: QTreeWidgetItem) -> None:
            if item.isExpanded():
                expanded_nodes.add(self._item_path(item))
            for i in range(item.childCount()):
                walk(item.child(i))

        for i in range(self.topLevelItemCount()):
            walk(self.topLevelItem(i))
        return expanded_nodes

    def _confirm_delete_analysis(self, item: QTreeWidgetItem) -> None:
        if item.parent() is not None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Analysis",
            f"Delete Analysis: {item.text(0)}?\nThis action is not reversible!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return
        self._delete_analysis(item)

    def _connect_signals(self) -> None:
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemChanged.connect(self._on_item_changed)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _create_all_views_menu_actions(self, item: QTreeWidgetItem) -> list[QAction]:
        list_of_actions: list[QAction] = []

        show_all_views_action = QAction("Show all views", self)
        show_all_views_action.triggered.connect(
            lambda _checked=False, item=item: self._show_all_views(item)
        )
        list_of_actions.append(show_all_views_action)

        hide_all_views_action = QAction("Hide all views", self)
        hide_all_views_action.triggered.connect(
            lambda _checked=False, item=item: self._hide_all_views(item)
        )
        list_of_actions.append(hide_all_views_action)

        add_view_action = QAction("Add a new view", self)
        add_view_action.triggered.connect(
            lambda _checked=False, item=item: self._add_a_view(item)
        )
        list_of_actions.append(add_view_action)

        return list_of_actions

    def _create_analysis_menu_actions(self, item: QTreeWidgetItem) -> list[QAction]:
        list_of_actions: list[QAction] = []

        rename_analysis_action = QAction("Rename", self)
        rename_analysis_action.triggered.connect(
            lambda _checked=False, item=item: self._start_rename_analysis(item)
        )
        list_of_actions.append(rename_analysis_action)

        delete_analysis_action = QAction("Delete", self)
        delete_analysis_action.triggered.connect(
            lambda _checked=False, item=item: self._confirm_delete_analysis(item)
        )
        list_of_actions.append(delete_analysis_action)

        show_data_table_action = QAction("Show Data", self)
        show_data_table_action.triggered.connect(
            lambda _checked=False, item=item: self._show_data(item)
        )
        list_of_actions.append(show_data_table_action)

        list_of_actions.extend(self._create_all_views_menu_actions(item))
        return list_of_actions

    def _create_single_fluid_menu_actions(self, item: QTreeWidgetItem) -> list[QAction]:
        list_of_actions: list[QAction] = []

        rename_fluid_action = QAction("Rename", self)
        rename_fluid_action.triggered.connect(
            lambda _checked=False: print("I want to be renamed")
        )
        list_of_actions.append(rename_fluid_action)

        edit_fluid_action = QAction("Edit", self)
        edit_fluid_action.triggered.connect(
            lambda _checked=False: print("I want to be edited")
        )
        list_of_actions.append(edit_fluid_action)

        delete_fluid_action = QAction("Delete", self)
        delete_fluid_action.triggered.connect(
            lambda _checked=False, item=item: self._delete_single_fluid(item)
        )
        list_of_actions.append(delete_fluid_action)

        return list_of_actions

    def _create_single_view_menu_actions(self, item: QTreeWidgetItem) -> list[QAction]:
        list_of_actions: list[QAction] = []

        rename_view_action = QAction("Rename", self)
        rename_view_action.triggered.connect(
            lambda _checked=False, item=item: self._start_rename_view(item)
        )
        list_of_actions.append(rename_view_action)

        delete_view_action = QAction("Delete", self)
        delete_view_action.triggered.connect(
            lambda _checked=False, item=item: self._delete_view(item)
        )
        list_of_actions.append(delete_view_action)

        show_single_view_action = QAction("Show", self)
        show_single_view_action.triggered.connect(
            lambda _checked=False, item=item: self._show_single_view(item)
        )
        list_of_actions.append(show_single_view_action)

        hide_single_view_action = QAction("Hide", self)
        hide_single_view_action.triggered.connect(
            lambda _checked=False, item=item: self._hide_single_view(item)
        )
        list_of_actions.append(hide_single_view_action)

        return list_of_actions

    def _delete_analysis(self, item: QTreeWidgetItem) -> None:
        analysis = item.data(0, Qt.ItemDataRole.UserRole)
        if analysis is None:
            return

        if analysis not in self.project.analyses:
            return

        self.project.analyses = [a for a in self.project.analyses if a is not analysis]
        self.project.mark_modified()
        self.analysis_deleted.emit()

    def _delete_single_fluid(self, item: QTreeWidgetItem) -> None:
        top_level = item
        while top_level.parent() is not None:
            top_level = top_level.parent()
        analysis = top_level.data(0, Qt.ItemDataRole.UserRole)
        fluid = item.data(0, Qt.ItemDataRole.UserRole)

        list_of_contacts: list[str] = []
        
        for other in analysis.fluids:
            bottom_fluid = other.bottom_contact.bottom_fluid
            if bottom_fluid is not None and bottom_fluid is fluid:
                list_of_contacts.append(other.name)

        if not list_of_contacts:
            text_1 = f"Are you sure you want to delete fluid {fluid.name}?"
            text_2 = "\n\nThis action is not reversible"
            text_3 = ""
        else:
            text_1 = f"{fluid.name} is the contact fluid of"
            if len(list_of_contacts) == 1:
                text_2 = f" {list_of_contacts[0]}"
            else:
                text_2 = ":\n\t" + "\n\t".join(list_of_contacts)
            text_3 = (
                "\n\nAre you sure you want to proceed?"
                "\nThis action is not reversible"
            )
        message = text_1 + text_2 + text_3

        reply = QMessageBox.question(self, "Delete Fluid", message)
        if reply != QMessageBox.StandardButton.Yes:
            return

        analysis.delete_fluid(fluid)
        self.project.mark_modified()
        self.fluids_changed.emit()

    def _delete_view(self, item: QTreeWidgetItem) -> None:
        top_level_item = item
        while top_level_item.parent() is not None:
            top_level_item = top_level_item.parent()

        view = item.data(0, Qt.ItemDataRole.UserRole)
        if view is None:
            return

        analysis = top_level_item.data(0, Qt.ItemDataRole.UserRole)
        analysis.analysis_views.remove(view)
        self.project.mark_modified()
        self.analysis_visibility_changed.emit(analysis, None)

    def _hide_all_views(self, item: QTreeWidgetItem) -> None:
        while item.parent() is not None:
            item = item.parent()

        analysis = item.data(0, Qt.ItemDataRole.UserRole)
        for view in analysis.analysis_views:
            view.is_visible = False

        self.project.mark_modified()
        self.analysis_visibility_changed.emit(analysis, None)

    def _hide_single_view(self, item: QTreeWidgetItem) -> None:
        view = item.data(0, Qt.ItemDataRole.UserRole)
        if view is None:
            return
        view.is_visible = False
        self.project.mark_modified()
        self.analysis_visibility_changed.emit(view.analysis_object, None)

    def _item_path(self, item: QTreeWidgetItem) -> tuple[str, ...]:
        parts: list[str] = []
        current: QTreeWidgetItem | None = item
        while current is not None:
            parts.append(current.text(0))
            current = current.parent()
        return tuple(reversed(parts))

    def _on_context_menu(self, position: QPoint) -> None:
        item = self.itemAt(position)
        if item is None:  # to ensure that the menu is only build on non-whitespace
            return

        if item.parent() is None:
            menu = QMenu(self)
            menu_actions = self._create_analysis_menu_actions(item)
        elif item.text(0) == "Analysis Views:":
            menu = QMenu(self)
            menu_actions = self._create_all_views_menu_actions(item)
        elif item.parent().text(0) == "Analysis Views:":
            menu = QMenu(self)
            menu_actions = self._create_single_view_menu_actions(item)
        elif item.parent().text(0) == "Fluids:":
            menu = QMenu(self)
            menu_actions = self._create_single_fluid_menu_actions(item)
        else:
            return

        for action in menu_actions:
            menu.addAction(action)
        menu.exec(self.viewport().mapToGlobal(position))

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
        self.analysis_renamed.emit(analysis)
        self.project.mark_modified()

    def _rename_view(self, item: QTreeWidgetItem) -> None:
        view = item.data(0, Qt.ItemDataRole.UserRole)
        view.name = item.text(0).strip()
        self.analysis_visibility_changed.emit(view.analysis_object, view)
        self.project.mark_modified()

    def _restore_expanded_paths(self, expanded_nodes: set[tuple[str, ...]]) -> None:
        def walk(item: QTreeWidgetItem) -> None:
            path = self._item_path(item)
            item.setExpanded(path in expanded_nodes)
            for i in range(item.childCount()):
                walk(item.child(i))

        for i in range(self.topLevelItemCount()):
            walk(self.topLevelItem(i))

    def _show_all_views(self, item: QTreeWidgetItem) -> None:
        while item.parent() is not None:
            item = item.parent()

        analysis = item.data(0, Qt.ItemDataRole.UserRole)
        for view in analysis.analysis_views:
            view.is_visible = True

        self.project.mark_modified()
        self.analysis_visibility_changed.emit(analysis, None)

    def _show_data(self, item: QTreeWidgetItem) -> None:
        obj = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(obj, AnalysisObject):
            return

        df = obj.analysis_dataset.dataframe
        specs = obj.analysis_dataset.column_specs
        name = obj.analysis_dataset.name

        show_dataframe_table_dialog(df, specs, name, self.parent, self.project)

    def _show_single_view(self, item: QTreeWidgetItem) -> None:
        view = item.data(0, Qt.ItemDataRole.UserRole)
        if view is None:
            return
        view.is_visible = True
        self.project.mark_modified()
        self.analysis_visibility_changed.emit(view.analysis_object, view)

    def _start_rename_analysis(self, item: QTreeWidgetItem) -> None:
        if item.parent() is not None:
            return
        self.setCurrentItem(item, 0)  # focus on the row
        self.editItem(item, 0)  # same as pressing F2

    def _start_rename_view(self, item: QTreeWidgetItem) -> None:
        view = item.data(0, Qt.ItemDataRole.UserRole)
        if view is None or not isinstance(view, AnalysisView):
            return
        self.setCurrentItem(item, 0)  # focus on the row
        self.editItem(item, 0)  # same as pressing F2

    #--------Public API--------

    def refresh_self(self) -> None:
        expanded_nodes = self._capture_expanded_paths()
        with QSignalBlocker(self):
            self.clear()
            self._build_tree()
            self._restore_expanded_paths(expanded_nodes)
