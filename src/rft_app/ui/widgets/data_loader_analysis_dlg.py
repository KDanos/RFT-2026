from pprint import pprint
from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtWidgets import (QCheckBox, QDialog, QGridLayout, QLabel, QSplitter, QTableWidget, QTreeWidget, QTreeWidgetItem, 
                            QTreeWidgetItemIterator, QVBoxLayout, QWidget, QComboBox, QFrame, QHBoxLayout, 
                            QLineEdit, QSpinBox, QTableWidgetItem)
from qtpy.QtWidgets import QMessageBox, QPushButton

from project import AnalysisObject, ColumnSpec, DataSet, ProjectDataManager
from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units, get_project_default_units
from .all_datasets_tree import AllDataSetsTree
from utilities import get_tree_top_level_item_by_name, get_tree_item_by_name, is_numeric, round_str_to_decimal_points, unique_name, update_tree_descendants, update_tree_ancestors
import pandas as pd


class DataLoaderDialogAnalysis(QDialog):
    def __init__(self,
                parent: QWidget = None,
                project: ProjectDataManager = None,
                ) -> None:
        super().__init__(parent)

        # Initialise the module variables
        self.project = project
        self.analysis_dataset: DataSet = None
        self.selected_dataset = None
        self.selected_columns = []
        self.selected_columns_specs = []
        self.result_analysis = None

        # Execute the build functions
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:

        # Build the window
        self.setWindowTitle("Data import for analysis")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )

        # Build the main frames and splitter
        self.data_frame = QFrame(self)
        self.data_frame_layout = QVBoxLayout(self.data_frame)
        self.table_frame = QFrame(self)
        main_splitter = QSplitter(self)
        main_splitter.addWidget(self.data_frame)
        main_splitter.addWidget(self.table_frame)
        main_splitter.setSizes([1000, 5000])

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(main_splitter)
        self.setLayout(self.main_layout)

        # Option to name the analysis
        self.name_lineEdit = QLineEdit(self.data_frame)
        self.name_lineEdit.setPlaceholderText("Analysis Name")
        self.data_frame_layout.addWidget(self.name_lineEdit)

        # Mapping primary depth and pressure data
        self.mapping_layout=QGridLayout()
        self.depth_label = QLabel("Depth Column")
        self.pressure_label = QLabel("Pressure Column")
        self.depth_combo = QComboBox(self.data_frame)
        self.pressure_combo = QComboBox(self.data_frame)
        self.mapping_layout.addWidget(self.depth_label, 1,1)
        self.mapping_layout.addWidget(self.pressure_label, 2,1)
        self.mapping_layout.addWidget(self.depth_combo, 1,2)
        self.mapping_layout.addWidget(self.pressure_combo, 2,2)
        self.data_frame_layout.addLayout(self.mapping_layout)
       
        # Create the data tree
        self.loaded_data_tree = AllDataSetsTree(self.data_frame, self.project)
        self.data_frame_layout.addWidget(self.loaded_data_tree)
        self._make_tree_tristate_checkable(self.loaded_data_tree)

        #Create a start analysis button
        self.start_btn = QPushButton("Start Analysis",self.data_frame)
        self.data_frame_layout.addWidget(self.start_btn)
        
        #Create the decimal rounding options
        decimalsContainer = QHBoxLayout()
        self.decimals_check_box = QCheckBox("Round decimals")
        self.decimals_check_box.setCheckState(Qt.CheckState.Checked)
        self.decimal_limit_spin = QSpinBox()
        self.decimal_limit_spin.setValue(1)
        self.decimal_limit_spin.setMaximum(10000)
        self.decimal_limit_spin.setEnabled(True)
        decimalsContainer.addWidget(self.decimals_check_box)
        decimalsContainer.addWidget(self.decimal_limit_spin)
        self.data_frame_layout.addLayout(decimalsContainer)

        #Ensure manual typing works in the decimals spinbox
        self.decimal_limit_spin.setReadOnly(False)
        self.decimal_limit_spin.lineEdit().setReadOnly(False)
        self.decimal_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.decimal_limit_spin.setKeyboardTracking(False)
        
        # Create the table preview
        self.preview_table = QTableWidget()
        table_layout = QVBoxLayout(self.table_frame)
        table_layout.addWidget(self.preview_table)
        self.preview_table.setRowCount(20)
        self.preview_table.setColumnCount(10)
        self.preview_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self._update_table()

    def _connect_signals(self) -> None:
        self.loaded_data_tree.itemChanged.connect(self._on_tree_item_changed)
        self.decimal_limit_spin.valueChanged.connect(self._update_table_values)
        self.start_btn.clicked.connect(self._start_analysis)

    def _make_tree_tristate_checkable(self, tree: QTreeWidget) -> None:
        it = QTreeWidgetItemIterator(tree)
        while item := it.value():
            item.setFlags(item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(0, Qt.CheckState.Unchecked)
            # Move to next Tree Widget Item
            it += 1

    def _enforce_only_one_dataset(self, changed_item: QTreeWidgetItem) -> None:
        active_top = changed_item
        while active_top.parent() is not None:
            active_top = active_top.parent()

        # Ensure this runs only when the top node is either checked or partially checked
        if active_top.checkState(0) == Qt.CheckState.Unchecked:
            return

        tree = active_top.treeWidget()
        if tree is None:
            return

        active_index = tree.indexOfTopLevelItem(active_top)

        tree.blockSignals(True)
        try:
            for i in range(tree.topLevelItemCount()):
                if i == active_index:
                    continue
                other_top = tree.topLevelItem(i)
                if other_top.checkState(0) == Qt.CheckState.Unchecked:
                    continue
                other_top.setCheckState(0, Qt.CheckState.Unchecked)
                update_tree_descendants(other_top, Qt.CheckState.Unchecked)
        finally:
            tree.blockSignals(False)

    def _extract_dataset_and_columns(self, name) -> None:

        # Extract the selected dataset
        self.selected_dataset = self.project.get_dataset_by_name(name)

        # Extract the selected column names
        top_level_item = get_tree_top_level_item_by_name(self.loaded_data_tree, name)
        columns_node = get_tree_item_by_name(self.loaded_data_tree, top_level_item, "Columns")
        self.selected_columns = []
        self.selected_columns_specs = []
        for i in range(columns_node.childCount()):
            item = columns_node.child(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                self.selected_columns.append(item.text(0))
                column_spec = self.selected_dataset.column_specs[i]
                self.selected_columns_specs.append(column_spec)

    # Extract the name of the dataset by identifying the top level item of the item emitting the signal
    def _dataset_name_for_item(self, item) -> str:
        top = item
        while top.parent() is not None:
            top = top.parent()
        return top.text(0)

    def _on_tree_item_changed(self, item, column: int) -> None:
        if column != 0:
            return

        self._set_descendants(item)
        self._update_ancestors(item)
        self._enforce_only_one_dataset(item)
        dataset_name = self._dataset_name_for_item(item)
        self._extract_dataset_and_columns(dataset_name) 
        self._create_analysis_dataframe()
        self._update_mapping_combos()
        self._update_table()

    def _update_table(self) -> None:

        # Create the dimensions of the table
        if not self.selected_dataset or not self.selected_columns:
            self._create_empty_preview_table()
            return
        else:
            column_count = len(self.selected_columns)
            header_list = self.selected_columns
        self.preview_table.setColumnCount(column_count)
        self.preview_table.setHorizontalHeaderLabels(header_list)

        if len(self.selected_columns) > 0:
            all_columns = list(self.selected_dataset.dataframe.columns)

            for c in range(column_count):
                units_combo = QComboBox()
                units_combo.currentTextChanged.connect(self._update_table_values)
                header = header_list[c]
                idx = all_columns.index(header)
                quantity_key = self.selected_dataset.column_specs[idx].quantity_key
                units_list = STANDARD_QUANTITIES[quantity_key].units
                default_unit = get_project_default_units(self.project, quantity_key)

                # Silence currentTextChanged during addItems/setCurrentText
                units_combo.blockSignals(True)
                try:
                    units_combo.addItems(units_list)
                    units_combo.setCurrentText(default_unit)
                finally:
                    units_combo.blockSignals(False)
                self.preview_table.setCellWidget(0, c, units_combo)

            # Update the values in the new table
            self._update_table_rows()
            self._update_table_values()

    def _update_table_rows(self) -> None:
        row_count, _ = self.selected_dataset.dataframe.shape
        self.preview_table.setRowCount(row_count + 1)
        vert_headers = ["Units"] + [str(i + 1) for i in range(row_count + 1)]
        self.preview_table.setVerticalHeaderLabels(vert_headers)

    def _create_analysis_dataframe(self) -> None:
        if not self.selected_dataset or not self.selected_columns:
            self.analysis_dataset = None
            return
        df = self.selected_dataset.dataframe[self.selected_columns].copy()

        # Append the dataframe to the analysis dataset
        self._create_analysis_dataset(df)

    def _create_analysis_dataset(self, dataframe: pd.DataFrame) -> None:
        name = self._get_analysis_name()
        column_specs = self.selected_columns_specs
        self.analysis_dataset = DataSet(name, dataframe, column_specs)

    def _update_table_values(self):

        if self.analysis_dataset is None:
            return

        df = self.analysis_dataset.dataframe
        row_count, column_count = df.shape

        for c in range(column_count):
            units_combo = self.preview_table.cellWidget(0, c)
            user_unit = units_combo.currentText() if units_combo is not None else ""
            quantity_key = self.analysis_dataset.column_specs[c].quantity_key
            quantity_type = STANDARD_QUANTITIES[quantity_key]
            for r in range(row_count):
                value = df.iat[r, c]

                if quantity_type.is_numeric:
                    if pd.isna(value):
                        value = ""
                    elif not is_numeric(value):
                        value = ""
                    elif user_unit != "":
                        value = convert_from_normalised_to_user_units(
                            user_output_unit=user_unit,
                            quantity_type=quantity_key,
                            value=value)
                
                        #Round the values to selected decimal points
                        value = round_str_to_decimal_points(value,self.decimals_check_box, self.decimal_limit_spin)
                display = str(value)
                
                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(r + 1, c, item)

    def _get_analysis_name(self) -> str:
        name = self.name_lineEdit.text() if self.name_lineEdit.text() else "Analysis"
        existing_names = self._extract_existing_analysis_names()
        name = unique_name(name, existing_names)
        return name

    def _extract_existing_analysis_names(self) -> list[str]:
        existing_names = []
        if len(self.project.analyses) == 0:
            return []
        for analysis in self.project.analyses:
            existing_names.append(analysis.name)
        return existing_names

    def _create_analysis_object(self) -> AnalysisObject:
        name = self.analysis_dataset.name
        source_datasets = [self.selected_dataset.name]
        analysis_dataset = self.analysis_dataset

        formation_pressure_src_col =self.pressure_combo.currentText().strip()
        vert_depth_src_col = self.depth_combo.currentText().strip()

        new_analysis_object = AnalysisObject(
            name=name,
            source_datasets=source_datasets,
            analysis_dataset=analysis_dataset,
            formation_pres_src_col=formation_pressure_src_col,
            vert_depth_src_col = vert_depth_src_col,
            )
        return new_analysis_object

    def _create_displayed_data_dataframe(self) -> None:
        pass

    def _set_descendants(self, item: QTreeWidgetItem) -> None:

        tree = item.treeWidget()
        state = item.checkState(0)
        if tree is not None:
            with QSignalBlocker(tree):
                update_tree_descendants(item, state)

    def _update_ancestors(self, item: QTreeWidgetItem) -> None:
        tree = item.treeWidget()
        if tree is not None:
            with QSignalBlocker(tree):
                update_tree_ancestors(item)

    def _create_empty_preview_table(self):
        table = self.preview_table
        table.setColumnCount(5)
        table.setRowCount(5)
        table.clear()

    def _create_options_list(
        self,
        user_quantity:str, 
        column_specs:list[ColumnSpec]
        )->list[str]:
        
        options = []
        for spec in column_specs:
            name = spec.name
            quantity_key = spec.quantity_key
            if user_quantity  == quantity_key:
                options.append(name)
        return options

    def _update_mapping_combos(self):
        if self.analysis_dataset is None or not self.analysis_dataset.column_specs:
            self.depth_combo.clear()
            self.pressure_combo.clear()
            return
        
        #Update depth combo
        depth_options = self._create_options_list("length", self.analysis_dataset.column_specs)
        self.depth_combo.clear()
        self.depth_combo.addItems(depth_options)

        #Update pressure combo
        pressure_options = self._create_options_list("pressure", self.analysis_dataset.column_specs)        
        self.pressure_combo.clear()
        self.pressure_combo.addItems(pressure_options)

    def _start_analysis(self)->AnalysisObject:
        if not self.selected_columns:
            QMessageBox.warning(
                self,
                "Start New Analysis",
                "No columns have been selected. Check at least on column in the tree"
            )
            return
        if self.depth_combo == "":
            QMessageBox.warning(
                self,
                "Start New Analysis",
                """Ensure that a column defined as a 'length' quantity has been selected to serve 
                as the base depth axis for the analysis"""
            )
            return
        if self.pressure_combo == "":
            QMessageBox.warning(
                self,
                "Start New Analysis",
                """Ensure that a column defined as a 'pressure' quantity has been selected to serve 
                as the base formation pressure for the analysis """
            )
        else:
            self.result_analysis = self._create_analysis_object()
            pprint(self.result_analysis)
            self.accept()