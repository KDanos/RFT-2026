from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QRadioButton, QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout
import csv
from io import StringIO
import units.units_manager as um

class DataLoaderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("Data Loader")       
        self.build_ui()
        self._connect_signals()
        self.show()
        
    def _connect_signals(self):
        self.paste_clipboard_btn.clicked.connect(self._parse_data)
        self.row_limit_spin.valueChanged.connect(self._update_preview)
        self.show_all_data_radio.toggled.connect(self._on_show_all_toggled)
    
    def build_ui(self):
        #Initilise with empty attributes
        self.headers =[]
        self.units = []
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
        rowsContainer.addWidget(rowLabel)
        rowsContainer.addWidget(self.row_limit_spin)
        controls_layout.addLayout(rowsContainer)

        self.show_all_data_radio = QRadioButton("Show All")
        controls_layout.addWidget(self.show_all_data_radio)
        
        #Right: preview controls
        self.preview_frame = QFrame()
        preview_layout = QVBoxLayout()
        
        #Right-top:column mapping
        self.mapping_table = QTableWidget()
        preview_layout.addWidget(self.mapping_table)
        
        #Right-bottom: data preview
        self.preview_table=QTableWidget()
        preview_layout.addWidget(self.preview_table)
        
        #Main Layout
        mainLayout.addWidget(self.controls_frame)
        mainLayout.addLayout(preview_layout)
        
        #Update tables
        self._update_preview()
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
            self.headers = parsed_rows[0]
            self.units = parsed_rows [1]
            self.data_rows = parsed_rows[2:]
            self._update_preview()
        except Exception as e: 
            QMessageBox.warning(self,"Invalid Clipboard Data", f"Could not parse data from clipboard. \n {e}")
            return 

    def _on_show_all_toggled(self): 
        if self.show_all_data_radio.isChecked() and self.data_rows:
            self.row_limit_spin.setValue(len(self.data_rows))
        else: 
            self.row_limit_spin.setValue(12)

    def _update_preview(self):
        column_count = 5
        
        #Show all data is the radio button is checked
        if self.show_all_data_radio.isChecked():
            self.row_limit_spin.setValue(len(self.data_rows))
        max_rows = self.row_limit_spin.value()

        if self.headers:
            column_count = len(self.headers)
        if self.data_rows:
            max_rows = min(self.row_limit_spin.value(),len(self.data_rows))
        
        self.preview_table.setColumnCount(column_count)
        self.preview_table.setRowCount(max_rows+1)
        
        #Create Headers
        self.preview_table.setHorizontalHeaderLabels(self.headers)
        for c in range(column_count):
            text = self.units[c] if c <len(self.units) else ""
            self.preview_table.setItem(0,c,QTableWidgetItem(text))

        #Pastew the values in the table
        for r in range (max_rows):
            try: 
                row_values = self.data_rows[r]
                table_row = r+1
                for c in range(column_count):
                    text = row_values[c] if c<len(row_values) else ""
                    self.preview_table.setItem(table_row,c,QTableWidgetItem(text))
            except:
                return
         #Correct the numbering on the rows
        v_header = ["Units"]+[str(i+1) for i in range (max_rows)]
        self.preview_table.setVerticalHeaderLabels(v_header)

    def _update_mapping_table(self):
        column_count = 5
        
        if self.headers:
            column_count = len(self.headers)
        
        self.mapping_table.setColumnCount(column_count)
        self.mapping_table.setRowCount(3)
        self.mapping_table.horizontalHeader().setVisible(False)

        #Define the row names
        v_header = ["Quantity", "Units", "Column Name"]
        self.mapping_table.setVerticalHeaderLabels(v_header)

        #Parse  quantities and units to the imported data
        quantity_list = sorted(q.label for q in um.STANDARD_QUANTITIES.values())
        
        for c in range(column_count):
            
            #Select a quantity type
            quantity_combo = QComboBox()
            for q in um.STANDARD_QUANTITIES.values():
                quantity_combo.addItem(q.label, q.key)
                quantity_combo.currentIndexChanged.connect(
                    lambda _, col=c: self._refresh_units_for_column(col)
                )
            self.mapping_table.setCellWidget(0,c,quantity_combo)
            

            #Selct the units associated with the quantity
            quantity_chosen = quantity_combo.currentData()
            quantity_object = um.STANDARD_QUANTITIES[quantity_chosen]
            units_list = quantity_object.units
            units_combo = QComboBox()
            units_combo.addItems(units_list)
            self.mapping_table.setCellWidget(1,c,units_combo)
        
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


