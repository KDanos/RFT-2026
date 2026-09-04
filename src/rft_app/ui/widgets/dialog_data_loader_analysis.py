from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)
import pandas as pd

from project import AnalysisObject, ColumnSpec, DataSet, ProjectDataManager
from project.canonical_names import CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units
from utilities import (
    get_tree_item_by_name,
    get_tree_top_level_item_by_name,
    is_numeric,
    round_value_to_decimal_points,
    unique_name,
    update_tree_ancestors,
    update_tree_descendants,
)
from .table_widgets import UnitsComboBox
from ui.main_window.sidebar import AllDataSetsTree


class DataLoaderDialogAnalysis(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
    ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project

        # Set module variables
        self.analysis_dataset: DataSet | None = None
        self.selected_dataset = None
        self.selected_columns: list = []
        self.selected_columns_specs: list = []
        self.result_analysis = None

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ordered_analysis_dataframe(
        self,
        source_df: pd.DataFrame,
        column_specs: list[ColumnSpec],
        *,
        vert_depth_src_col: str,
        formation_pres_src_col: str,
    ) -> tuple[pd.DataFrame, list[ColumnSpec]]:
        #Map the original name -> ColumnSpec for quick Lookup
        spec_by_name = {spec.name: spec for spec in column_specs}

        #Other selected columns (preserve stable order, exclude the two mapped cols)
        other_cols = [
            name
            for name in source_df.columns
            if name not in (vert_depth_src_col, formation_pres_src_col)
        ]

        ordered_src_names = [vert_depth_src_col, formation_pres_src_col, *other_cols]

        df = source_df[ordered_src_names].copy()
        df = df.rename(
            columns={
                vert_depth_src_col: CANONICAL_VERTICAL_DEPTH,
                formation_pres_src_col: CANONICAL_FORMATION_PRESSURE,
            }
        )
        #Rebuild specs in the same order, with updated names for the first two
        new_specs: list[ColumnSpec] = []
        for col_name in df.columns:
            if col_name == CANONICAL_VERTICAL_DEPTH:
                old = spec_by_name[vert_depth_src_col]
                new_specs.append(ColumnSpec(CANONICAL_VERTICAL_DEPTH, old.quantity_key, old.unit))
            elif col_name == CANONICAL_FORMATION_PRESSURE:
                old = spec_by_name[formation_pres_src_col]
                new_specs.append(
                    ColumnSpec(CANONICAL_FORMATION_PRESSURE, old.quantity_key, old.unit)
                )
            else:
                new_specs.append(spec_by_name[col_name])

        return df, new_specs

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
        self.mapping_layout = QGridLayout()
        self.depth_label = QLabel("Depth Column")
        self.pressure_label = QLabel("Pressure Column")
        self.depth_combo = QComboBox(self.data_frame)
        self.pressure_combo = QComboBox(self.data_frame)
        self.mapping_layout.addWidget(self.depth_label, 1, 1)
        self.mapping_layout.addWidget(self.pressure_label, 2, 1)
        self.mapping_layout.addWidget(self.depth_combo, 1, 2)
        self.mapping_layout.addWidget(self.pressure_combo, 2, 2)
        self.data_frame_layout.addLayout(self.mapping_layout)

        # Create the data tree
        self.loaded_data_tree = AllDataSetsTree(
            self.project.loaded_datasets,
            self.data_frame,
            self.project, 
            label = "Loaded DataSets")
        self.loaded_data_tree.reload_from_project(self.project.loaded_datasets)
        self.data_frame_layout.addWidget(self.loaded_data_tree)
        self._make_tree_tristate_checkable(self.loaded_data_tree)

        #Create a start analysis button
        self.start_btn = QPushButton("Start Analysis", self.data_frame)
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
        self.preview_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_table()

    def _connect_signals(self) -> None:
        self.loaded_data_tree.itemChanged.connect(self._on_tree_item_changed)
        self.decimal_limit_spin.valueChanged.connect(self._update_table_values)
        self.start_btn.clicked.connect(self._start_analysis)

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

    def _create_analysis_object(self) -> AnalysisObject:
        formation_pres_src_col = self.pressure_combo.currentText().strip()
        vert_depth_src_col = self.depth_combo.currentText().strip()

        #Re-order the dataframe so that the depth and pressure are the first two columns
        df, specs = self._build_ordered_analysis_dataframe(
            self.analysis_dataset.dataframe,
            self.analysis_dataset.column_specs,
            vert_depth_src_col=vert_depth_src_col,
            formation_pres_src_col=formation_pres_src_col,
        )

        #Re-create the dataset
        self.analysis_dataset = DataSet(self.analysis_dataset.name, df, specs)

        new_analysis_object = AnalysisObject(
            name=self.analysis_dataset.name,
            source_datasets=[self.selected_dataset.name],
            analysis_dataset=self.analysis_dataset,
            vert_depth_src_col=vert_depth_src_col,
            formation_pres_src_col=formation_pres_src_col,
        )

        return new_analysis_object

    def _create_empty_preview_table(self) -> None:
        table = self.preview_table
        table.setColumnCount(5)
        table.setRowCount(5)
        table.clear()

    def _create_options_list(
        self,
        user_quantity: str,
        column_specs: list[ColumnSpec],
    ) -> list[str]:
        options = []
        for spec in column_specs:
            name = spec.name
            quantity_key = spec.quantity_key
            if user_quantity == quantity_key:
                options.append(name)
        return options

    def _dataset_name_for_item(self, item: QTreeWidgetItem) -> str:
        top = item
        while top.parent() is not None:
            top = top.parent()
        return top.text(0)

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

    def _extract_dataset_and_columns(self, name: str) -> None:
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

    def _extract_existing_analysis_names(self) -> list[str]:
        existing_names = []
        if len(self.project.analyses) == 0:
            return []
        for analysis in self.project.analyses:
            existing_names.append(analysis.name)
        return existing_names

    def _get_analysis_name(self) -> str:
        name = self.name_lineEdit.text() if self.name_lineEdit.text() else "Analysis"
        existing_names = self._extract_existing_analysis_names()
        name = unique_name(name, existing_names)
        return name

    def _make_tree_tristate_checkable(self, tree: QTreeWidget) -> None:
        it = QTreeWidgetItemIterator(tree)
        while item := it.value():
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            # Move to next Tree Widget Item
            it += 1

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
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

    def _set_descendants(self, item: QTreeWidgetItem) -> None:
        tree = item.treeWidget()
        state = item.checkState(0)
        if tree is not None:
            with QSignalBlocker(tree):
                update_tree_descendants(item, state)

    def _start_analysis(self) -> AnalysisObject | None:
        if not self.selected_columns:
            QMessageBox.warning(
                self,
                "Start New Analysis",
                "No columns have been selected. Check at least on column in the tree",
            )
            return None
        if not self.depth_combo.currentText().strip():
            QMessageBox.warning(
                self,
                "Start New Analysis",
                """Ensure that a column defined as a 'length' quantity has been selected to serve 
                as the base depth axis for the analysis""",
            )
            return None
        if not self.pressure_combo.currentText().strip():
            QMessageBox.warning(
                self,
                "Start New Analysis",
                """Ensure that a column defined as a 'pressure' quantity has been selected to serve 
                as the base formation pressure for the analysis """,
            )
            return None

        self.result_analysis = self._create_analysis_object()
        self.accept()
        return self.result_analysis

    def _update_ancestors(self, item: QTreeWidgetItem) -> None:
        tree = item.treeWidget()
        if tree is not None:
            with QSignalBlocker(tree):
                update_tree_ancestors(item)

    def _update_mapping_combos(self) -> None:
        if self.analysis_dataset is None or not self.analysis_dataset.column_specs:
            self.depth_combo.clear()
            self.pressure_combo.clear()
            return

        #Update depth combo
        depth_options = self._create_options_list("length", self.analysis_dataset.column_specs)
        self.depth_combo.clear()
        self.depth_combo.addItems(depth_options)

        #Update pressure combo
        pressure_options = self._create_options_list(
            "pressure", self.analysis_dataset.column_specs
        )
        self.pressure_combo.clear()
        self.pressure_combo.addItems(pressure_options)

    def _update_table(self) -> None:
        # Create the dimensions of the table
        if not self.selected_dataset or not self.selected_columns:
            self._create_empty_preview_table()
            return

        column_count = len(self.selected_columns)
        header_list = self.selected_columns
        self.preview_table.setColumnCount(column_count)
        self.preview_table.setHorizontalHeaderLabels(header_list)

        if len(self.selected_columns) > 0:
            all_columns = list(self.selected_dataset.dataframe.columns)

            for c in range(column_count):
                header = header_list[c]
                idx = all_columns.index(header)
                quantity_key = self.selected_dataset.column_specs[idx].quantity_key
                units_combo = UnitsComboBox(quantity_key, self.project)
                units_combo.currentTextChanged.connect(self._update_table_values)

                self.preview_table.setCellWidget(0, c, units_combo)

            # Update the values in the new table
            self._update_table_rows()
            self._update_table_values()

    def _update_table_rows(self) -> None:
        row_count, _ = self.selected_dataset.dataframe.shape
        self.preview_table.setRowCount(row_count + 1)
        vert_headers = ["Units"] + [str(i + 1) for i in range(row_count + 1)]
        self.preview_table.setVerticalHeaderLabels(vert_headers)

    def _update_table_values(self) -> None:
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
                            value=value,
                        )

                        #Round the values to selected decimal points
                        value = round_value_to_decimal_points(
                            value, self.decimals_check_box, self.decimal_limit_spin
                        )
                display = str(value)

                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(r + 1, c, item)

    #--------Public API--------
