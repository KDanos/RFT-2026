
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QRadioButton, QVBoxLayout, QHBoxLayout

from ui.filterable_table.filter_specs import FilterSpecNumber
from ui.filterable_table.filter_combos import NumberFilterCombo

class FilteringWindow(QDialog):
    def __init__(
            self, 
            parent = None, 
            column_name:str ="", 
            filter_name = ""
            )->None:
        super().__init__(parent)

        self.column_name=column_name
        self.filter_name = filter_name
        self.setWindowTitle("Number Filter")
        self.setWindowIcon(QIcon('resources/images/CY_LOGO_RGB.jpg'))
        
        self.__build_ui()

    def __build_ui(self)->None:
        main_layout = QVBoxLayout(self)
        # Create the button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent = self
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Apply Filter")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        #Define the top label
        column_label = QLabel(self.column_name)
        label_layout = QHBoxLayout()
        label_layout.addWidget(column_label)
        label_layout.addStretch()
        main_layout.addLayout(label_layout)

        #First Filter row
        self.first_combo=NumberFilterCombo(self)
        if self.filter_name !="":
            print(f"The filter name is {self.filter_name}")
            self.first_combo.setCurrentText(self.filter_name)
        self.value1_line_edit = QLineEdit()
        value1_layout = QHBoxLayout()
        value1_layout.addWidget(self.first_combo)
        value1_layout.addWidget(self.value1_line_edit)
        main_layout.addLayout(value1_layout)

        #And/Or operator options
        radio_layout = QHBoxLayout()
        and_radio_btn = QRadioButton("And")
        or_radio_btn = QRadioButton("Or")
        and_radio_btn.setChecked(True)
        radio_layout.addWidget(and_radio_btn)
        radio_layout.addWidget(or_radio_btn)
        radio_layout.addStretch()
        main_layout.addLayout(radio_layout)

        #Second Filter row
        second_combo=NumberFilterCombo(self)
        value2_line_edit = QLineEdit()
        value2_layout = QHBoxLayout()
        value2_layout.addWidget(second_combo)
        value2_layout.addWidget(value2_line_edit)
        main_layout.addLayout(value2_layout)
      
        #Add the button box
        main_layout.addStretch() #ensure to push the button to the bottom
        main_layout. addWidget(button_box)

    def _on_accept(self)->None:
        print("You have accepted the window")
        value = self.value1_line_edit.text()
        symbol = self.first_combo.currentData().symbol
        print(f"I want to filter values that are {symbol} than {value}")
        #Create a new filter spec and assign it to the dictionary of filter specs
        try:
            value = float(value)
        except ValueError:
            print ("A numeric value is required as input")
            return #stay open
        
        self.result_spec = FilterSpecNumber(value, symbol)
        self.accept()

