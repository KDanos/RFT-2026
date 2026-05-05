from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QRadioButton, QSpacerItem, QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout
import csv
from io import StringIO
import units.units_manager as um

class DataLoaderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("Data Loader")       
        self.build_ui()
        
        # Create a sync guard flag to prevent column resizing ping-pong loops
        self._is_syncing_columns = False
        
        self._connect_signals()
        self.show()

    def _connect_signals(self):
        self.paste_clipboard_btn.clicked.connect(self._parse_data)
        self.row_limit_spin.valueChanged.connect(self._update_preview_table)
        self.show_all_data_radio.toggled.connect(self._on_show_all_toggled)
        self.mapping_table.horizontalHeader().sectionResized.connect(self._sync_mapping_to_preview)
        self.preview_table.horizontalHeader().sectionResized.connect(self._sync_preview_to_mapping)

    def build_ui(self):
        #Initilise with empty attributes
        self.data_rows = []
        
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)

        #Left: import controls
        self.controls_frame = QFrame()
        controls_layout = QVBoxLayout()
        self.controls_frame.setLayout(controls_layout)
        
        self.paste_clipboard_btn = QPushButton("Update Clipboard")      
        controls_layout.addWidget(self.paste_clipboard_btn)

        rowsContainer = QHBoxLayout()
        rowLabel = QLabel("Show max rows")
        self.row_limit_spin = QSpinBox()
        self.row_limit_spin.setValue(12)
        self.row_limit_spin.setMaximum(10000)
        #Ensure manual typing works
        self.row_limit_spin.setReadOnly(False)
        self.row_limit_spin.lineEdit().setReadOnly(False)
        self.row_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        rowsContainer.addWidget(rowLabel)
        rowsContainer.addWidget(self.row_limit_spin)
        controls_layout.addLayout(rowsContainer)

        self.show_all_data_radio = QRadioButton("Show All")
        controls_layout.addWidget(self.show_all_data_radio)
        controls_layout.addStretch()
        self.delete_row_btn = QPushButton("Delete selected rows")
        controls_layout.addWidget(self.delete_row_btn)
        
        #Right: preview controls
        self.preview_frame = QFrame()
        preview_layout = QVBoxLayout()
        
        #Right-top:column mapping
        self.mapping_table = QTableWidget()
        preview_layout.addWidget(self.mapping_table)
        
        #Right-bottom: data preview
        self.preview_table=QTableWidget()
        self.preview_table.horizontalHeader().setVisible(False)
        preview_layout.addWidget(self.preview_table)
        
        #Main Layout
        mainLayout.addWidget(self.controls_frame)
        mainLayout.addLayout(preview_layout)
        
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
        except Exception as e: 
            QMessageBox.warning(self,"Invalid Clipboard Data", f"Could not parse data from clipboard. \n {e}")
            return 

    def _on_show_all_toggled(self): 
        if self.show_all_data_radio.isChecked() and self.data_rows:
            self.row_limit_spin.setValue(len(self.data_rows))
        else: 
            self.row_limit_spin.setValue(12)

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
        
        #Paste the values in the table
        for r in range (max_rows):
            try: 
                #Create the "delete" checkbox
                if r<len(self.data_rows): #to capture the case of empty clipboard data, otherwise cell(0,0) creates a checkbox when one is not wanted
                    self.preview_table.setItem(r,0,self._make_delete_checkbox_item())
                else:
                    self.preview_table.setItem(r,0,QTableWidgetItem(""))
                
                
                row_values = self.data_rows[r]
                for c in range(data_column_count):
                    text = row_values[c] if c<len(row_values) else ""
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.preview_table.setItem(r,c+1,item)
            except:
                return
        
        #Correct the numbering on the rows
        v_header = [str(i+1) for i in range (max_rows)]
        self.preview_table.setVerticalHeaderLabels(v_header)
        self.preview_table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def _update_mapping_table(self):
        data_column_count = len(self.data_rows[0]) if self.data_rows else 5
        mapping_column_count =data_column_count+1
        
        self.mapping_table.setColumnCount(mapping_column_count)
        self.mapping_table.setRowCount(3)
        self.mapping_table.horizontalHeader().setVisible(False)

        #Define the row names
        v_header = ["Quantity", "Units", "Column Name"]
        self.mapping_table.setVerticalHeaderLabels(v_header)
       
        for c in range(data_column_count):
            mapping_column = c+1

            #Select a quantity type
            quantity_combo = QComboBox()
            for q in um.STANDARD_QUANTITIES.values():
                quantity_combo.addItem(q.label, q.key)
            quantity_combo.currentIndexChanged.connect(
                lambda _, col=mapping_column: self._refresh_units_for_column(col)
            )
            self.mapping_table.setCellWidget(0,mapping_column,quantity_combo)
            
            #Select the units associated with the quantity
            quantity_chosen = quantity_combo.currentData()
            quantity_object = um.STANDARD_QUANTITIES[quantity_chosen]
            units_list = quantity_object.units
            units_combo = QComboBox()
            units_combo.addItems(units_list)
            self.mapping_table.setCellWidget(1,mapping_column,units_combo)
        
    def _refresh_units_for_column(self, col:int):
        quantity_combo = self.mapping_table.cellWidget(0,col)
        units_combo = self.mapping_table.cellWidget(1,col)
        if not quantity_combo or not units_combo:
            return
        
        qkey = quantity_combo.currentData()
        qobj = um.STANDARD_QUANTITIES[qkey]

        units_combo.blockSignals(True)
        units_combo.clear()
        units_combo.addItems(qobj.units)
        units_combo.blockSignals(False)

    def _make_delete_checkbox_item(self) -> QTableWidgetItem:
        item = QTableWidgetItem("Delete")
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsSelectable
        )
        item.setCheckState(Qt.CheckState.Unchecked)
        return item

    def _sync_mapping_to_preview(self, logical_index:int, old_size:int, new_size:int):
        pass

    def _sync_preview_to_mapping(self, logical_index:int, old_size:int, new_size:int ):
        pass