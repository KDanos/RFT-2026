from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,  QMessageBox, QPushButton, QRadioButton, QSizePolicy,  QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout  
import csv
from io import StringIO
from project import ColumnSpec, DataFrameSpecs, DataFrameSpecs
import units.units_manager as um
import pandas as pd

class DataLoaderDialogProject(QDialog):
    def __init__(self, parent=None, project = None):
        super().__init__(parent)
        
        self.imported_df:Optional[pd.DataFrame] = None #placeholder, will be replaced when the _create_dataframe function is run
        self.imported_column_specs: list[ColumnSpec] = []
        self.imported_dataframe_specs: DataFrameSpecs = None
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("Data Loader")       
        self.setWindowFlags(
            self.windowFlags()
            |Qt.WindowType.WindowMinimizeButtonHint
            |Qt.WindowType.WindowMaximizeButtonHint
        )
        #Provide access to the project data, imported as the project object when the DataLoaderDialog load function is called in the main window (load_data(self)) 
        self.project = project
        
        self.build_ui()
        
        # Create a sync guard flag to prevent column resizing ping-pong loops
        self._is_syncing_columns = False
        self._connect_signals()

    def _connect_signals(self):
        self.paste_clipboard_btn.clicked.connect(self._parse_data)
        self.row_limit_spin.valueChanged.connect(self._update_spin_box_manually)
        self.decimals_check_box.toggled.connect(self._on_decimal_check_toggled)
        self.decimal_limit_spin.valueChanged.connect(self._round_decimal_points_in_preview_table)
        self.show_all_data_radio.toggled.connect(self._on_show_all_toggled)     
        self.import_data_btn.clicked.connect(self._create_dataframe)
        self.preview_table.horizontalHeader().sectionResized.connect(self._sync_resizing_table_column_width)
        self.preview_table.itemChanged.connect(self._deletion_selection_changed)
        self.mapping_table.horizontalHeader().sectionResized.connect(self._sync_resizing_table_column_width)

    def build_ui(self):
        #Initilise with empty attributes
        self.data_rows = []
        self.rows_to_ignore = []
        self.columns_to_ignore =[]

        #Left: import controls
        self.controls_frame = QFrame()
        controls_layout = QVBoxLayout(self.controls_frame)
        
        # Option to name the dataset
        self.name_line_edit = QLineEdit()
        self.name_line_edit.setPlaceholderText("Dataset Name")
        controls_layout.addWidget(self.name_line_edit)

        # Button to update the clipboard
        self.paste_clipboard_btn = QPushButton("Update Clipboard")      
        controls_layout.addWidget(self.paste_clipboard_btn)
        
        #Define the rows in preview table
        rowsContainer = QHBoxLayout()
        rowLabel = QLabel("Show max rows")
        
        self.row_limit_spin = QSpinBox()
        self.row_limit_spin.setValue(12)
        self.row_limit_spin.setMaximum(10000)
        
        #Ensure manual typing works in the rows limit spinbox
        self.row_limit_spin.setReadOnly(False)
        self.row_limit_spin.lineEdit().setReadOnly(False)
        self.row_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.row_limit_spin.setKeyboardTracking(False)

        rowsContainer.addWidget(rowLabel)
        rowsContainer.addWidget(self.row_limit_spin)
        controls_layout.addLayout(rowsContainer)

        self.show_all_data_radio = QRadioButton("Show All")
        controls_layout.addWidget(self.show_all_data_radio)
        controls_layout.addStretch()
        self.import_data_btn = QPushButton("Import Data")
        controls_layout.addWidget(self.import_data_btn)
        
        #Define number of decimals at import
        decimalsContainer = QHBoxLayout()
        self.decimals_check_box = QCheckBox("Round decimals")
        self.decimal_limit_spin = QSpinBox()
        self.decimal_limit_spin.setValue(0)
        self.decimal_limit_spin.setMaximum(10000)
        self.decimal_limit_spin.setEnabled(False)
        decimalsContainer.addWidget(self.decimals_check_box)
        decimalsContainer.addWidget(self.decimal_limit_spin)
        controls_layout.addLayout(decimalsContainer)

        #Ensure manual typing works in the decimals spinbox
        self.decimal_limit_spin.setReadOnly(False)
        self.decimal_limit_spin.lineEdit().setReadOnly(False)
        self.decimal_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.decimal_limit_spin.setKeyboardTracking(False)
       
        #Right: preview controls
        self.preview_frame = QFrame()
        preview_layout = QVBoxLayout()
        
        #Right-top:column mapping
        self.mapping_table = QTableWidget()       
        mapping_hdr = self.mapping_table.horizontalHeader()
        mapping_hdr.setVisible(True)
        mapping_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        #Right-bottom: data preview
        self.preview_table=QTableWidget()
        preview_hdr = self.preview_table.horizontalHeader()
        preview_hdr.setVisible(True)
        preview_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        preview_layout.addWidget(self.mapping_table,0)
        preview_layout.addWidget(self.preview_table,1)

        #Main Layout
        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.controls_frame)
        mainLayout.addLayout(preview_layout)
        self.setLayout(mainLayout)

        #Update tables
        self._update_preview_table()
        self._update_mapping_table()
    
    def _parse_data(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
    
        if not text:
            QMessageBox.warning(self, "Clipboard is empty", "No tabular text found in clipboard.")
            return 

        #Identify the delimiter
        sample = text[:1000]
        delimiter = "\t"
        try: 
            dialect=csv.Sniffer().sniff(sample,delimiters = "\t,;|")
            delimiter= dialect.delimiter
        except csv.Error:
            pass
            
        reader = csv.reader(StringIO(text), delimiter = delimiter)
        try:
            parsed_rows = [[cell.strip() for cell in row] for row in reader if row]
            
            #Make every row the same length
            max_cols = max(len(r) for r in parsed_rows)
            self.data_rows = [r +[""]*(max_cols-len(r)) for r in parsed_rows]

            self._update_mapping_table()
            self._update_preview_table()
            self._sync_initial_table_column_width()

        except Exception as e: 
            QMessageBox.warning(self,"Invalid Clipboard Data", f"Could not parse data from clipboard. \n {e}")
            return 

    def _on_show_all_toggled(self): 
        if self.show_all_data_radio.isChecked() and self.data_rows:
            self.row_limit_spin.setValue(len(self.data_rows))
        else: 
            current_value = self.row_limit_spin.value()
            self.row_limit_spin.setValue(current_value)
        
    def _update_preview_table(self):
        data_column_count = len(self.data_rows[0]) if self.data_rows else 5
        preview_column_count = data_column_count +1
        
        #Show all data if the radio button is checked
        if self.show_all_data_radio.isChecked():
            self.row_limit_spin.setValue(len(self.data_rows))
        max_rows = self.row_limit_spin.value()
        
        if self.data_rows:
            max_rows = min(self.row_limit_spin.value(),len(self.data_rows))
        
        self.preview_table.setColumnCount(preview_column_count)
        self.preview_table.setRowCount(max_rows)
        
        #Clear the header labels
        self.preview_table.setHorizontalHeaderLabels([""]*self.preview_table.columnCount())
        
        #Paste the values in the table
        for r in range (max_rows):
            try: 
                #Block any change signals during build
                self.preview_table.blockSignals(True)
                
                #Create the "Ignore" checkbox
                if r<len(self.data_rows): #to capture the case of empty clipboard data, otherwise cell(0,0) creates a checkbox when one is not wanted
                    self.preview_table.setItem(r,0,self._make_checkbox_item("Ignore"))
                else:
                    self.preview_table.setItem(r,0,QTableWidgetItem(""))
                
                row_values = self.data_rows[r]
                for c in range(data_column_count):
                    text = row_values[c] if c<len(row_values) else ""
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.preview_table.setItem(r,c+1,item)

                #Un-block change signals 
                self.preview_table.blockSignals(False)
            except:
                return
        
        #Correct the numbering on the rows
        v_header = [str(i+1) for i in range (max_rows)]
        self.preview_table.setVerticalHeaderLabels(v_header)
        self.preview_table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        #Check any rows that have been previously selected for deletion
        self._recheck_rows_to_ignore()

    def _update_mapping_table(self):
        data_column_count = len(self.data_rows[0]) if self.data_rows else 5
        mapping_col_count =data_column_count+1
        
        self.mapping_table.setColumnCount(mapping_col_count)
        self.mapping_table.setRowCount(3)

        #Clear the header labels
        self.mapping_table.setHorizontalHeaderLabels([""]*self.mapping_table.columnCount())

        #Define the row names
        v_header = ["Quantity", "Units", "Column Name"]
        self.mapping_table.setVerticalHeaderLabels(v_header)
       
        #Create a widget to bring in the headers from the table.
        headers_query = QCheckBox("Headers from row 1?")
        headers_query.toggled.connect(self._import_headers_from_preview_table)
        self.mapping_table.setCellWidget(2,0,headers_query)
        
        for c in range(data_column_count):
            mapping_col = c+1
            #Select a quantity type
            quantity_combo = QComboBox()
            
            priority_keys = ("undefined", "ignore")
            priority_quantities = [
                um.STANDARD_QUANTITIES[key]
                for key in priority_keys
                if key in um.STANDARD_QUANTITIES
            ]

            other_quantities = sorted(
                (
                q 
                for key,q in um.STANDARD_QUANTITIES.items()
                if key not in priority_keys
                ),
                key = lambda q: q.label.casefold()
                                    )

            for q in priority_quantities+other_quantities:
                quantity_combo.addItem(q.label, q.key)
                
            quantity_combo.currentIndexChanged.connect(
                lambda _, col=mapping_col: self._refresh_units_for_column(col)
            )       
            
            # #Set the initial quantity to undefined
            quantity_combo.blockSignals(True)
            i = quantity_combo.findData("undefined")
            if i>=0:
                quantity_combo.setCurrentIndex(i)
            quantity_combo.blockSignals(False)

            #Select the units associated with the quantity
            quantity_chosen = quantity_combo.currentData()
            quantity_object = um.STANDARD_QUANTITIES[quantity_chosen]
            units_list = quantity_object.units
            units_combo = QComboBox()
            units_combo.addItems(units_list)

            default_unit = self._get_project_default_units(quantity_chosen)
            idx = units_combo.findText(default_unit)
            if idx >= 0:
                units_combo.setCurrentIndex(idx)
            
            self.mapping_table.setCellWidget(0,mapping_col,quantity_combo)
            self.mapping_table.setCellWidget(1,mapping_col,units_combo)
        
    def _refresh_units_for_column(self, col:int):
        quantity_combo = self.mapping_table.cellWidget(0,col)
        units_combo = self.mapping_table.cellWidget(1,col)
        if not quantity_combo or units_combo is None:
            return
        
        qkey = quantity_combo.currentData()
        qobj = um.STANDARD_QUANTITIES[qkey]

        units_combo.blockSignals(True)
        units_combo.clear()
        units_combo.addItems(qobj.units)
        
        
        default_unit=self._get_project_default_units(qkey)
        idx = units_combo.findText(default_unit)
        if idx >= 0:
            units_combo.setCurrentIndex(idx)
        
        units_combo.blockSignals(False)

    def _make_checkbox_item(self,name:str) -> QTableWidgetItem:
        item = QTableWidgetItem(name)
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsSelectable
        )
        item.setCheckState(Qt.CheckState.Unchecked)
        return item

    def _sync_initial_table_column_width(self):
        for c in range(self.preview_table.columnCount()):
                width = max(self.preview_table.columnWidth(c),self.mapping_table.columnWidth(c))
                self.mapping_table.setColumnWidth(c,width)
                self.preview_table.setColumnWidth(c,width)
        v_header_width = max(self.preview_table.verticalHeader().width(),self.mapping_table.verticalHeader().width())
        self.mapping_table.verticalHeader().setFixedWidth(v_header_width)
        self.preview_table.verticalHeader().setFixedWidth(v_header_width)
        
    def _sync_resizing_table_column_width(self,logical_index:int, old_zise:int, new_size:int):
        #Exit the function if already in it
        if self._is_syncing_columns:
            return
        
        
        
        sender = self.sender()
        if sender is self.mapping_table.horizontalHeader():
            target = self.preview_table
        elif sender is self.preview_table.horizontalHeader():
            target = self.mapping_table
        else:
            return

        #Protect against column number mismatch during rebuilds
        if logical_index < 0 or logical_index >= target.columnCount():
            return  
        
        #Engage the guard, to avoide ping-pong resizing
        self._is_syncing_columns = True
        try:
            target.setColumnWidth(logical_index,new_size)
        finally:
            #Remore the guard to allow entry into the function again
            self._is_syncing_columns = False

    def _select_rows_to_ignore(self):
        self.rows_to_ignore =[]
        for r in range(self.preview_table.rowCount()):
           item = self.preview_table.item(r,0)
           if item and item.checkState()==Qt.CheckState.Checked:
                self.rows_to_ignore.append(r)
       
    def _select_columns_to_ignore(self):
        self.columns_to_ignore = []
        for c in range(self.mapping_table.columnCount()):
            quantity_combo = self.mapping_table.cellWidget(0,c)
            if quantity_combo and quantity_combo.currentData() == "ignore":
                self.columns_to_ignore.append(c)
    
    def _deletion_selection_changed(self, item:QTableWidgetItem):
        if item.column()!= 0 or not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        self._select_rows_to_ignore()

    def _recheck_rows_to_ignore(self):     
        if not self.rows_to_ignore:
            return
        
        self.preview_table.blockSignals(True)   
        try:
            for r in self.rows_to_ignore:
                if r < self.preview_table.rowCount():    
                    self.preview_table.item(r,0).setCheckState(Qt.CheckState.Checked)
        finally: 
            self.preview_table.blockSignals(False)

    def _update_spin_box_manually(self):
        self.show_all_data_radio.setChecked(False)
        self._update_preview_table()

    def _import_headers_from_preview_table (self, checked:bool):

        for c in range (1,self.preview_table.columnCount()):
            item = self.preview_table.item(0,c)
            text = item.text() if item is not None else ""
            if checked:
                self.mapping_table.setItem(2,c,QTableWidgetItem(text))
            else: 
                self.mapping_table.setItem(2,c,QTableWidgetItem(""))

    def _create_dataframe(self)-> Optional[pd.DataFrame]:
        #Ensure the rows and columns to ingore list is alligned with the preview_table at its current state
        self._select_rows_to_ignore()
        self._select_columns_to_ignore()

        #Bring in the decimal points limit
        decimals = self.decimal_limit_spin.value() if self.decimal_limit_spin.isEnabled() else None
        
        #Exit the function if there is no data from the clipboard
        if not self.data_rows:
            QMessageBox.information(self, "Data Import", "No data was selected for import")
            return None

        #Define the Column names and assign the units (ColumnSpec)
        selected_mapping_cols = [c for c in range(1,self.mapping_table.columnCount()) if c not in self.columns_to_ignore]
        if not selected_mapping_cols:
            QMessageBox.information(self, "Data Import", "No columns have been selected for import")
            return None
        
        col_names = []
        
        #Ensure that the column specs are empty before appending 
        self.imported_column_specs = []
        
        for mapping_col in selected_mapping_cols:
            item = self.mapping_table.item(2,mapping_col)
            name = item.text().strip() if item and item.text().strip() else f"col_{mapping_col}"
            col_names.append(name)

            #Create the column specs, to hold the units
            quantity_combo = self.mapping_table.cellWidget(0,mapping_col)
            quantity_key = (
                quantity_combo.currentData()
                if quantity_combo is not None and quantity_combo.currentData()
                else "undefined"
            )
            units_combo = self.mapping_table.cellWidget(1,mapping_col)
            units = units_combo.currentText() if units_combo is not None else ""
   
            current_spec = ColumnSpec(name,quantity_key, units )
            self.imported_column_specs.append(current_spec)
        
        #Collect values in the data rows, ignoring the appropriate ones from the preview table
        rows = []
        for r in range(len(self.data_rows)):  
            #Skip any rows that have been clicked to ignore
            if r in self.rows_to_ignore:
                continue

            row_values_to_import = self.data_rows[r]
            row_vals_for_df = []
            
            for mapping_col in selected_mapping_cols:
                source_column = mapping_col-1
                value = row_values_to_import[source_column] if 0<=source_column<len(row_values_to_import) else ""
                #Round to decimal points if requested:
                if decimals is not None and self._is_numeric(value):
                    if decimals ==0:
                        value = int(round(float(value),decimals))
                    else:
                        value = round(float(value),decimals)
                elif self._is_numeric(value):
                    value = float(value)
                elif value.strip() =="":
                    value=None
                    
                row_vals_for_df.append(value)
            rows.append(row_vals_for_df)
        
        if not rows: 
            QMessageBox.information(self, "Data Import", "No rows were selected for import")
            return None
        mydf =  pd.DataFrame(rows, columns=col_names)
        self.imported_df = mydf

        # Create the dataframe metadata
        name = self.name_line_edit.text().strip()
        self.dataframe_specs = DataFrameSpecs(name)
        
        #Call the preview window of the dataframe
        result = self._create_the_dataframe_preview_table(mydf, name)
        if result != QDialog.DialogCode.Accepted:
            self.imported_df = None
            self.imported_column_specs = []
            self.imported_dataframe_specs = []
            return None
        
        self.accept()
        return mydf

    def _create_the_dataframe_preview_table(self, dataframe:pd.DataFrame, name:str) -> int:
        mydf = dataframe
        
        #Load Preview Widget
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(name)
        preview_table = QTableWidget()
        layout = QVBoxLayout()
        layout.addWidget(preview_table)
        
        #Create a button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent = preview_dialog
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Import")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Back to mapping")
        button_box.accepted.connect(preview_dialog.accept)
        button_box.rejected.connect(preview_dialog.reject)

        #Complete the layout
        layout.addWidget(button_box)
        preview_dialog.setLayout(layout)
        
        #Define the dimensions of the table
        preview_table.setRowCount(len(mydf)+1)
        preview_table.setColumnCount(len(mydf.columns))
        preview_table.setHorizontalHeaderLabels([str(c) for c in mydf.columns])
        
        for r in range (preview_table.rowCount()):
            for c in range(len(mydf.columns)):
                #Place the units:
                if r == 0:
                   spec = self.imported_column_specs[c]
                   item = QTableWidgetItem(spec.unit)
                else:
                    value =mydf.iat[r-1,c]
                    display_text = "" if pd.isna(value) else str(value)              
                    item = QTableWidgetItem(display_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                preview_table.setItem(r,c,item)
        v_labels = ["Units"]+[str (i+1) for i in range (len(mydf))]
        preview_table.setVerticalHeaderLabels(v_labels)
        
        return preview_dialog.exec()

    def _round_decimal_points_in_preview_table(self, decimal_points:int = 1000)->None:
        self.preview_table.blockSignals(True)
        
        if self.decimals_check_box.isChecked():
            decimal_points = self.decimal_limit_spin.value()
        try:
            for r in range(self.preview_table.rowCount()):
                for c in range(1,self.preview_table.columnCount()):#skip the index 0 which is the "ignore row" collumn
                    item = self.preview_table.item(r,c)
                    if item is None:
                        continue
                    if not self._is_numeric(item.text()):
                        continue
                    value = self.data_rows[r][c-1]#This works only so long as data_rows are mirrored in the preview table
                    if decimal_points == 0:
                        value = int(round(float(value),decimal_points))
                    else:
                        value = round(float(value),decimal_points)
                    
                    item.setText(str(value))        
        finally:
            self.preview_table.blockSignals(False)
   
    def _is_numeric(self, text:str)-> bool: 
        try:
            float(text.strip())
            return True
        except ValueError:
            return False

    def _on_decimal_check_toggled(self, checked:bool):
        self.decimal_limit_spin.setEnabled(checked)

        if checked:
            self._round_decimal_points_in_preview_table()
        else: 
            self._update_preview_table()

    def _get_project_default_units (self, quantity_key:str)->str:
        if self.project is None: 
            return ""
        return self.project.current_unit_system.units_by_quantity.get (quantity_key,"")