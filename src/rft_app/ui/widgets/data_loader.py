from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QTextEdit, QVBoxLayout
import csv
from io import StringIO

class DataLoaderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("Data Loader")
        self.build_ui()
        self.show()
        
    def build_ui(self):
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)

        #Left: import controls
        self.controlsFrame = QFrame()
        controlsLayout = QVBoxLayout()
        self.controlsFrame.setLayout(controlsLayout)
        
        rowsContainer = QHBoxLayout()
        rowLabel = QLabel("Show max rows")
        rowSpinBox = QSpinBox()
        rowSpinBox.setValue(12)
        rowSpinBox.setMaximum(100)
        rowsContainer.addWidget(rowLabel)
        rowsContainer.addWidget(rowSpinBox)
        controlsLayout.addLayout(rowsContainer)

        btnPasteClipboard = QPushButton("Testing Button")
        btnPasteClipboard.clicked.connect(self._parse_data)

        controlsLayout.addWidget(btnPasteClipboard)
        
        #Right-top: column mapping
        #data preview
        self.previewBox=QTextEdit()
        

        mainLayout.addWidget(self.controlsFrame)
        mainLayout.addWidget(self.previewBox)
    
    def _parse_data(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
    
        if not text:
            QMessageBox.warning(self, "Clipboard is empty", "No tabular text found in clipboard.")
            return [], [],[]

        
        QMessageBox.about(self,"Testing Message Box","There exists data")

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
            headers = parsed_rows[0]
            units = parsed_rows [1]
            data_rows = parsed_rows[2:]
            return headers, units, data_rows
        
        except Exception as e: 
            QMessageBox.warning(self,"Invalid Clipboard Data", f"Could not parse data from clipboard. \n {e}")
            return [],[],[]
            


            




