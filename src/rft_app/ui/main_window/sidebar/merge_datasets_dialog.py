from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,  QPushButton, QVBoxLayout, QWidget
import pandas as pd
import numpy as np
from pandas.core.apply import reconstruct_and_relabel_result
from project import  ColumnSpec, DataSet, ProjectDataManager
from units import STANDARD_QUANTITIES
from utilities import print_current_location_function, show_dataframe_table_dialog, unique_name


class MergeDatasetsDialog(QDialog):
    COL_HEADERS = 0
    COL_BASE = 1
    COL_QUANTITY = 2
    COL_SEPARATOR = 3
    COL_FIRST_MERGE = 4
    FIRST_DATA_ROW = 3
    HEADER_LINE_ROW = FIRST_DATA_ROW - 1
    
    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.parent = parent
        self.project = project if project is not None else ProjectDataManager()

        # Set module variables
        self.merging_sets = []
        self.prefered_sets = []
        self.row_quantity_keys = []
        self.row_headers = []

        # Initialisation methods
        self._build_ui()
        self._connect_signals()
    
    #--------Private UI--------

    def _build_ui(self) -> None:

        self.setWindowTitle("Merge Datasets")
        self.setWindowIcon(QIcon('resources/images/CY_LOGO_RGB.jpg'))
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)
        
        # New Merged Dataset Name
        new_name_label = QLabel("Name: ")
        self.name_line_edit = QLineEdit()
        self.name_line_edit.setPlaceholderText("Merged Dataset")
        self.new_name_layout = QHBoxLayout()
        self.new_name_layout.addWidget(new_name_label)
        self.new_name_layout.addWidget(self.name_line_edit)
        self.new_name_layout.addStretch()
        self.new_name_layout.setContentsMargins(0,0,0,12)
        self.v_layout.addLayout(self.new_name_layout)
        
        # Ensure padding to the bottom of the window
        self.h_layout = QHBoxLayout()
        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addStretch()

        # Add the main (grid layout) and ensure padding to the right of the window
        self.main_layout = QGridLayout()
        self.main_layout.setHorizontalSpacing(15)
        self.h_layout.addLayout(self.main_layout)
        self.h_layout.addStretch()

        # Merge Dataset Column Titles
        title_label = QLabel("New Title")
        self.main_layout.addWidget(title_label, 1, self.COL_HEADERS)

        # Base Dataset User Selection
        base_label = QLabel("Base Dataset")
        self.main_layout.addWidget(base_label, 0, self.COL_BASE)
        self.base_set_combo = QComboBox(self)
        self.main_layout.addWidget(self.base_set_combo, 1, self.COL_BASE)
        for set in self.project.all_datasets:
            self.base_set_combo.addItem(set.name, set)
        
        # Ensure that the top 2 rows do not stretch to accomodate extra space
        self.main_layout.setRowStretch(0,0)
        self.main_layout.setRowStretch(1,0)
        
        #Create a Button Box
        self.preview_button = QPushButton("Preview")
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent = self
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Merge")
        self.button_box.addButton(
            self.preview_button,
            QDialogButtonBox.ButtonRole.ActionRole,
        )

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.button_box)
        self.v_layout.addLayout(self.button_layout)
        
        # Populate Base Set Column Name
        self._populate_base_dataset_column_options()

    def _connect_signals(self)-> None:
        self.base_set_combo.currentIndexChanged.connect(self._populate_base_dataset_column_options)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.preview_button.clicked.connect(self._preview_merged_dataset)
    
    def _create_new_dataset(self)->DataSet:
        new_df = self._create_combined_dataframe()
        new_specs = []
        for i,header in enumerate(new_df.columns):
            new_spec = ColumnSpec(header,self.row_quantity_keys[i])
            new_specs.append(new_spec)
        
        # Extract name
        name = self.name_line_edit.text().strip() or "Merged Dataset"
        list_of_names = [ds.name for ds in self.project.all_datasets]
        name = unique_name(name, list_of_names)

        return DataSet(name, new_df, new_specs)

    def _build_mapping_dict(self) -> dict[str, dict[str, str]]:
        base_ds = self.base_set_combo.currentData()
        all_ds = [base_ds] + self.merging_sets
        mapping_dict: dict[str, dict[str, str]] = {}

        for row_idx, header in enumerate(self.row_headers):
            row = row_idx + self.FIRST_DATA_ROW
            ds_dicts: dict[str, str] = {}
            mapping_dict[header] = ds_dicts

            for col_idx, ds in enumerate(all_ds):
                mapped_header = ""
                if col_idx == 0:
                    col = self.COL_BASE
                else:
                    col = col_idx + self.COL_FIRST_MERGE - 1

                item = self.main_layout.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if widget:
                        if isinstance(widget, QLabel):
                            mapped_header = widget.text()
                        elif isinstance(widget, QComboBox):
                            if widget.currentData() is not None:
                                mapped_header = widget.currentText()

                ds_dicts[ds.name] = mapped_header

        return mapping_dict

    def _create_combined_dataframe(self) -> pd.DataFrame:
        mapping_dict = self._build_mapping_dict()
        base_ds = self.base_set_combo.currentData()
        all_ds = [base_ds] + self.merging_sets
        
        blocks:list[pd.DataFrame] =[]
        for ds in all_ds:
            block_df = pd.DataFrame(index = ds.dataframe.index,columns = self.row_headers)

            for header in self.row_headers:
                column_name = mapping_dict[header].get(ds.name,"")
                if column_name !="":
                    block_df[header] = ds.dataframe[column_name].values
                else:
                    block_df[header] = np.nan
            blocks.append(block_df)

        if not blocks:
            return pd.DataFrame(columns=self.row_headers)
        
        new_df = pd.concat(blocks, ignore_index = True)
        return new_df

    def _create_headers_list(self)->None:

        rows = self.main_layout.rowCount()
        last_merging_column = len(self.merging_sets)+self.COL_FIRST_MERGE
        self.row_headers = []

        #Clear all previous header inputs
        for row in range(self.FIRST_DATA_ROW-1, self.main_layout.rowCount()):
            item = self.main_layout.itemAtPosition(row, self.COL_HEADERS)
            if item:
                widget = item.widget()
                if widget:
                    if isinstance(widget, QLineEdit):
                        self.main_layout.removeWidget(widget)
                        widget.deleteLater()
        
        for col in range(self.COL_BASE, last_merging_column):
            for row in range(self.FIRST_DATA_ROW, rows):
                #Gate for options in the base set
                if col==self.COL_BASE:
                    item = self.main_layout.itemAtPosition(row, col)
                    if item:
                        widget = item.widget()
                        if widget:
                            if isinstance(widget, QLabel):
                                text = widget.text()
                                header = unique_name(text,self.row_headers)
                                self.row_headers.append(header)

                #Gate for merging set columns
                elif col<=last_merging_column and row>=len(self.row_headers)+self.FIRST_DATA_ROW:
                    item = self.main_layout.itemAtPosition(row, col)
                    if item:
                        widget = item.widget()
                        if widget:
                            if isinstance(widget, QComboBox):
                                if widget.currentData() is not None:
                                    text = widget.currentText()
                                    header = unique_name(text,self.row_headers)
                                    self.row_headers.append(header)
                # Row-filtering, i.e.skip rows that have been captured previously
                else:
                    continue

        # Create the header line edits
        for i in range (len(self.row_headers)):
            row = i + self.FIRST_DATA_ROW
            line_edit = QLineEdit()
            self.main_layout.addWidget(line_edit, row, 0)
            line_edit.setPlaceholderText(self.row_headers[i])
            line_edit.setFrame(False)
            line_edit.setToolTip(self.row_headers[i])
            line_edit.editingFinished.connect(lambda idx= i, line_edit= line_edit: self._update_headers_list(idx,line_edit.text()))                  
         
    def _draw_lines(self):
        
        rows = self.main_layout.rowCount()

        # Update the column count in case columns have been deleted and kept empty in the layout
        last_col = self.COL_SEPARATOR
        for col in range (self.COL_FIRST_MERGE, self.main_layout.columnCount()):
            # if (
            #     self.main_layout.itemAtPosition(0,col) is not None
            #     or self.main_layout.itemAtPosition(1,col) is not None
            # ):
            if self.main_layout.itemAtPosition(0,col) is None:
                last_col = col
                break 
        columns = last_col+self.COL_SEPARATOR+1

        #Clear any previous lines
        for row in range(rows):
            for col in range(columns):
                item = self.main_layout.itemAtPosition(row,col)
                if item:
                    widget = item.widget()
                    if widget:
                        if widget.property("separator"):
                            self.main_layout.removeWidget(widget)
                            widget.deleteLater()

        #Define the lines
        all_lines = []
        
        span = self.COL_SEPARATOR
        hline_left = HorizontalSeparator(self.FIRST_DATA_ROW-1,0,span)
        all_lines.append(hline_left)

        span= columns-self.COL_SEPARATOR
        hline_right = HorizontalSeparator(self.FIRST_DATA_ROW-1, self.COL_SEPARATOR, span )
        all_lines.append(hline_right)

        span = self.FIRST_DATA_ROW-1
        vline_top = VerticalSeparator(0, self.COL_SEPARATOR, span)
        all_lines.append(vline_top)
        
        span = rows-self.FIRST_DATA_ROW
        vline_bottom = VerticalSeparator(self.FIRST_DATA_ROW, self.COL_SEPARATOR, span)
        all_lines.append(vline_bottom)
        
        # Add the lines to the layout
        for line in all_lines:
            line.add_to(self.main_layout)
        
    def _on_accept(self):
        new_ds = self._create_new_dataset()
        self.project.merged_datasets.append(new_ds)
        self.project.mark_modified()
        self.accept()

    def _preview_merged_dataset(self) -> None:
        new_ds = self._create_new_dataset()
        new_df= new_ds.dataframe
        new_specs = new_ds.column_specs
        show_dataframe_table_dialog(new_df,new_specs, "Merged Preview", self, self.project)
    
    def _populate_base_dataset_column_options(self)->None:

        #Clear any existing labels
        for row in range(self.FIRST_DATA_ROW, self.main_layout.rowCount()):
            for col in (self.COL_HEADERS, self.COL_BASE, self.COL_QUANTITY):
                item = self.main_layout.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        self.main_layout.removeWidget(widget)
                        widget.deleteLater()

        # Populate the column names of the base set
        base_set = self.base_set_combo.currentData()
        for idx, spec in enumerate(base_set.column_specs):
            next_row = idx + self.FIRST_DATA_ROW
            label = QLabel(spec.name)
            self.main_layout.addWidget(label, next_row, self.COL_BASE)
            quantity = STANDARD_QUANTITIES[spec.quantity_key].label
            quantity_label = QLabel(quantity)
            self.main_layout.addWidget(quantity_label, next_row, self.COL_QUANTITY)

        #Remove any additional columns in the layout
        for col in range(self.COL_FIRST_MERGE, self.main_layout.columnCount()):
            for row in range(self.main_layout.rowCount()):
                item = self.main_layout.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    self.main_layout.removeItem(item)
                    if widget is not None:
                        widget.deleteLater()

        # Create a merging column option for the next column
        self.merging_label = QLabel("Merging Dataset")
        self.main_layout.addWidget(self.merging_label, 0, self.COL_FIRST_MERGE)

        # Populate the merging dataset options
        merging_combo = QComboBox(self)
        self.main_layout.addWidget(merging_combo, 1, self.COL_FIRST_MERGE)
        merging_combo.currentTextChanged.connect(
            lambda _text: self._populate_merging_dataset_column_options(self.COL_FIRST_MERGE)
        )
        self._update_rows_quantity_list(0)
        self._populate_merging_dataset_column_options(self.COL_FIRST_MERGE)
      
    def _populate_merging_dataset_column_options(self, col_idx:int)->None:
        merge_count = col_idx - self.COL_SEPARATOR
        base_set = self.base_set_combo.currentData()
        merging_combo = self.main_layout.itemAtPosition(1, col_idx).widget()  
        available_sets = self._update_list_of_available_datasets(exclude_col=col_idx)
        
        # Index into prefered_sets for this merge column (col 4 -> 0, col 5 -> 1, ...).
        position = merge_count - 1
        selected_set = merging_combo.currentData()

        # currentData() is None in two different situations we must distinguish:
        # 1. User explicitly picked "None" on this column (combo already populated).
        # 2. A column to the left was changed and this header combo was recreated empty.
        # In case 1, keep None. In case 2, restore the last known selection from
        # prefered_sets so right-hand columns survive left-hand rebuilds.
        if (
            selected_set is None
            and merging_combo.count() > 0
            and merging_combo.currentText() == "None"
        ):
            pass  # user chose None; keep selected_set as None
        elif selected_set is None and len(self.prefered_sets) > position:
            selected_set = self.prefered_sets[position]

        # Remove any additional columns and rows after
        for row in range(self.main_layout.rowCount()):
            for col in range (col_idx,self.main_layout.columnCount()):
                # Keep the current column meging_combo and label
                if col== col_idx and row <=1:
                    continue
                item = self.main_layout.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    self.main_layout.removeItem(item)
                    if widget is not None:
                        widget.deleteLater()
        
        # Populate the merging combo options
        with QSignalBlocker(merging_combo):
            merging_combo.clear()
            if merge_count !=1:
                merging_combo.addItem("None", None)
            for ds in available_sets:
                merging_combo.addItem(ds.name, ds)

            # Select a default for the combo 
            if merge_count != 1 and (selected_set is None or selected_set not in available_sets):
                merging_combo.setCurrentIndex(0)   # "None"
            elif selected_set in available_sets:
                idx = merging_combo.findData(selected_set)
                if idx >= 0:
                    merging_combo.setCurrentIndex(idx)
        
        # Save the final selection
        selected_set = merging_combo.currentData()
        if len(self.prefered_sets)>position:
            self.prefered_sets[position] = selected_set
        else: 
            self.prefered_sets.insert(position, selected_set)
         
        # Create the selection of merging columns
        merging_set = merging_combo.currentData()
        if merging_set is not None:
            
            filtered_column_specs = list(merging_set.column_specs) 
            
            if col_idx == self.COL_FIRST_MERGE:
                row_count = len(base_set.column_specs) # applicable if populating only the first merging column
            else: 
                row_count = len (self.row_quantity_keys) # applicable when taking into account rows resulting from previous merging columns
            
            for i in range(row_count):
                current_quantity = self.row_quantity_keys[i]

                #Create a list of specs with the matching quantity key
                matching_column_specs = [spec 
                    for spec in filtered_column_specs
                    if spec.quantity_key == current_quantity
                    ]
                
                options_combo  = QComboBox()
                options_combo.setProperty("quantity_key", current_quantity)                
                options_combo.addItem("None", None)
                # Add the relevant fields in the combo box
                for spec in matching_column_specs:
                    options_combo.addItem(spec.name, spec)
                # Default to not None if possible:
                if len(matching_column_specs)>0:
                    options_combo.setCurrentIndex(1)

                    # Remove the column selected from the available column options of the following rows
                    filtered_column_specs.remove(options_combo.currentData())
                # Update the options combo to reflect user selection on combos of the same quantity
                options_combo.currentTextChanged.connect(lambda _text: self._update_options_combo(col_idx))

                # Add combo-box to the grid
                current_row = i + self.FIRST_DATA_ROW
                self.main_layout.addWidget(options_combo, current_row, col_idx)

            # Hide all no option combos
            for row in range(self.FIRST_DATA_ROW, self.main_layout.rowCount()):
                item = self.main_layout.itemAtPosition(row, col_idx)
                if item:
                    widget = item.widget()
                    if widget:
                        if isinstance(widget, QComboBox):
                            if widget.currentData() is None:
                                widget.setVisible(False)
        
            #Fill-in un-used columns
            self._populate_unused_columns(col_idx)
        
            # Provide the option to merge another dataset
            remaining_sets = self._update_list_of_available_datasets()
            if remaining_sets:
                

                next_col = col_idx+1
                next_label = QLabel("Merging Dataset")
                self.main_layout.addWidget(next_label,0, next_col)
                next_combo = QComboBox()
                self.main_layout.addWidget(next_combo, 1, next_col)
                next_combo.currentTextChanged.connect(
                    lambda _text, c=next_col: self._populate_merging_dataset_column_options(c)
                )
                self._populate_merging_dataset_column_options(next_col)  
        
        else:
            #Ensure that the quantity list is rebuild in column 3 if a merging column is removed
            self._update_rows_quantity_list(col_idx)
        
        self._draw_lines()
        self._create_headers_list()
        return
    
    def _populate_unused_columns(self, col_idx:int)->None:

        merging_set_combo = self.main_layout.itemAtPosition(1, col_idx).widget()  
        merging_set = merging_set_combo.currentData()
        merging_specs = list(merging_set.column_specs)
        
        # List all the specs allready in populate
        used_specs = []
        for row in range(self.FIRST_DATA_ROW, self.main_layout.rowCount()):
            item = self.main_layout.itemAtPosition(row, col_idx)
            if item is not None:
                combo = item.widget()
                if combo is not None:
                    used_specs.append(combo.currentData())

        # Clear any previously un-used spec combos
        starting_row = self.FIRST_DATA_ROW + len(used_specs)
        for row in range(starting_row, self.main_layout.rowCount()):
            for col in (self.COL_QUANTITY, col_idx):
                item = self.main_layout.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        self.main_layout.removeWidget(widget)
                        widget.deleteLater()

        # Create a combo with only the 1 option for the remaining specs
        row = starting_row
        for spec in merging_specs:
            if spec not in used_specs:
                combo = QComboBox()
                combo.addItem(spec.name, spec)
                self.main_layout.addWidget(combo, row, col_idx)
                row += 1
        
        self._update_rows_quantity_list(col_idx)

    def _update_headers_list(self, idx:int, text:str)-> None:
        
        sender = self.sender()
        
        #Check for uniqueness
        testing_list = [header for index,header in enumerate(self.row_headers) if index !=idx]
        header = unique_name(text, testing_list)
        #Update the header list
        self.row_headers[idx]=header
        
        #Update the widget and tooltip
        if isinstance(sender, QLineEdit):
            with QSignalBlocker(sender):
                sender.setText(header)
                sender.setToolTip(header)     

    def _update_list_of_available_datasets(self, exclude_col: int | None = None)->list[DataSet]:
        #Ensure all selected merging datasets have been captured
        self._update_list_of_merging_datasets(exclude_col=exclude_col)

        base_set = self.base_set_combo.currentData()
        return  [ds for ds in self.project.all_datasets
                if ds is not base_set and ds not in self.merging_sets]     

    def _update_list_of_merging_datasets(self, exclude_col:int|None = None)->None:
        self.merging_sets.clear()
        if exclude_col is None:
            # e.g. remaing_sets: exclude every selected merge dataset
            col_range = range(self.COL_FIRST_MERGE, self.main_layout.columnCount())
        else:
            #header for col_idx:only exclude merges to the LEFT
            col_range = range(self.COL_FIRST_MERGE, exclude_col)
        
        for col in col_range:
            item = self.main_layout.itemAtPosition(1,col)
            if item is not None:
                combo = item.widget()
                if combo is not None:
                    dataset = combo.currentData()
                    if dataset is not None:
                        self.merging_sets.append(dataset)

    def _update_options_combo(self, col_idx:int)-> None:
        sender = self.sender()
        quantity_key = sender.property("quantity_key")

        merging_set = self.main_layout.itemAtPosition(1, col_idx).widget().currentData()
        
        # Identify all combos that reflect the specific quantity:
        combos_to_change =[]
        for i in range(self.FIRST_DATA_ROW, self.main_layout.rowCount()):
            item = self.main_layout.itemAtPosition(i, col_idx)
            if item is not None:
                combo = item.widget()
                if combo is not None:
                    if combo.property("quantity_key") == quantity_key:
                        combos_to_change.append(combo)

        # Loop through the combos that need changing
        for combo_to_update in combos_to_change:
             
            if combo_to_update is sender:
                continue # No action, user update already
            
            # Specs already chosen by other combos
            taken = [combo.currentData() for combo in combos_to_change
                    if combo is not combo_to_update and combo.currentData() is not None
                    ]

            available_specs = [spec for spec in merging_set.column_specs
                                if spec.quantity_key == quantity_key and spec not in taken]
            
            current_selection = combo_to_update.currentData()

            with QSignalBlocker(combo_to_update):
                combo_to_update.clear()
                combo_to_update.addItem("None", None)
                for spec in available_specs:
                    combo_to_update.addItem(spec.name, spec)

                if current_selection in available_specs:
                    combo_to_update.setCurrentIndex(combo_to_update.findData(current_selection))
                elif len(available_specs)==1:
                    combo_to_update.setCurrentIndex(1)
                else:
                    combo_to_update.setCurrentIndex(0)

    def _update_rows_quantity_list(self, col_idx)->None:
        base_set = self.base_set_combo.currentData()
        self.row_quantity_keys.clear()

        # Clear all existing labels
        for row in range(self.FIRST_DATA_ROW, self.main_layout.rowCount()):
            item = self.main_layout.itemAtPosition(row, self.COL_QUANTITY)
            if item:
                widget = item.widget()
                if widget:
                    if isinstance(widget, QLabel):
                        self.main_layout.removeWidget(widget)
                        widget.deleteLater()

        # Populate the quantities_keys of the base set in the quantity list
        self.row_quantity_keys = [spec.quantity_key for spec in base_set.column_specs]

        # Loop thought the columns, and find the number of specs in that column
        for col in range(self.COL_FIRST_MERGE, col_idx + 1):
            col_spec_count = 0
            for row in range(self.FIRST_DATA_ROW, self.main_layout.rowCount()):
                item = self.main_layout.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if widget:
                        if isinstance(widget, QComboBox):
                            col_spec_count =col_spec_count+1
            
            # Append the additional qunatity keys to the list of row_quantity keys
            if col_spec_count > len(self.row_quantity_keys):
                for i in range(len(self.row_quantity_keys), col_spec_count):
                    row = self.FIRST_DATA_ROW + i
                    item = self.main_layout.itemAtPosition(row, col)
                    if item is None:
                        continue
                    widget = item.widget()
                    if isinstance(widget, QComboBox):
                        spec=widget.currentData()
                        if spec is not None:
                            self.row_quantity_keys.append(spec.quantity_key)

        # Re-create all the labels
        row_quantity_labels = [STANDARD_QUANTITIES[q].label for q in self.row_quantity_keys]
        for i in range(len(row_quantity_labels)):
            row = i + self.FIRST_DATA_ROW
            label = QLabel(row_quantity_labels[i])
            self.main_layout.addWidget(label, row, self.COL_QUANTITY)








            



    #--------Public API--------

class HorizontalSeparator(QFrame):
    def __init__(self,row:int, col:int, span:int=1, parent = None)->None:
        super().__init__(parent)
        self.row = row
        self.col = col
        self.span = span
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setProperty("separator", True)
    
    def add_to(self,layout:QGridLayout)->None:
        layout.addWidget(self, self.row, self.col, 1,self.span)

class VerticalSeparator(HorizontalSeparator):
    def __init__(self, row: int, col: int, span: int = 1, parent=None)->None:
        super().__init__(row, col, span, parent)
        self.setFrameShape(QFrame.Shape.VLine)

    def add_to(self,layout:QGridLayout)->None:
        layout.addWidget(self, self.row, self.col, self.span,1)
