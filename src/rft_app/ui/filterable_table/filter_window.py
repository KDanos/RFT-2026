from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QShowEvent
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QLineEdit, QRadioButton, QVBoxLayout, 
                            QHBoxLayout)
from qtpy.QtWidgets import QMessageBox

from units import normalise_from_user_units
from utilities import print_current_location_function
from ui.filterable_table.filter_specs import FilterSpecNumber, NumberClause
from ui.filterable_table.filter_combos import NumberFilterCombo

class FilteringWindow(QDialog):
    between_selected = pyqtSignal()

    def __init__(
            self, 
            parent = None, 
            column_name:str ="", 
            filter_name = ""
            )->None:
        super().__init__(parent)

        self.column_name = parent.column_name
        self.filter_name = filter_name
        self.column_units = parent.column_units
        self.column_quantity_key = parent.column_quantity_key

        self.setWindowTitle("Number Filter")
        self.setWindowIcon(QIcon('resources/images/CY_LOGO_RGB.jpg'))
        self.__build_ui()

    def __build_ui(self)->None:
        self.main_layout = QVBoxLayout(self)
        
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
        self.main_layout.addLayout(label_layout)

        #First filter row
        self._build_first_filter_row()

        #And/Or operator options
        self.radio_layout = QHBoxLayout()
        self.and_radio_btn = QRadioButton("And")
        self.or_radio_btn = QRadioButton("Or")
        self.and_radio_btn.setChecked(True)
        self.radio_layout.addWidget(self.and_radio_btn)
        self.radio_layout.addWidget(self.or_radio_btn)
        self.radio_layout.addStretch()
        self.main_layout.addLayout(self.radio_layout)
        
        # Second filter row
        self._build_second_filter_row()
      
        #Add the button box
        self.main_layout.addStretch() #ensure to push the button to the bottom
        self.main_layout. addWidget(button_box)

        #Check if the first row requires a second input widget
        self._on_between_toggled(self.first_combo)

    def _on_accept(self)->None:

        #Create the compalsory first number_clause
        number_clause_1 = self._create_number_clause(self.first_combo, self.value1_line_edit, self.value_1b_line_edit)

        #Make sure this window stays open if the error message is shown (numeric value required)
        if number_clause_1 is None: 
            return

        #Create the optional second clause only if there is an input in the second row
        number_clause_2 = None
        if self.value2_line_edit.text():
            number_clause_2 = self._create_number_clause(self.second_combo, self.value2_line_edit, self.value_2b_line_edit)
        
            #Make sure this window stays open if the error message is shown (numeric value required)
            if number_clause_2 is None: 
                return

        # Extract the selected connector
        self.connector = None if not number_clause_2 else ("and" if self.and_radio_btn.isChecked() else "or")
        self.result_spec = FilterSpecNumber(number_clause_1, self.connector, number_clause_2)
        self.accept()

    def showEvent(self, event:QShowEvent)->None:
        """Make a specific line edit the focus when the window (self) is shown"""
        super().showEvent(event)
        self.value1_line_edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def _build_first_filter_row(self):
        self.first_combo=NumberFilterCombo(self)
        
        if self.filter_name !="":
            self.first_combo.setCurrentText(self.filter_name)
        self.first_combo.currentTextChanged.connect(lambda _text: self._on_between_toggled(self.first_combo))
        self.value1_line_edit = QLineEdit()
        self.value1_layout = QHBoxLayout()
        
        # Add the initialy hidden b value widgets
        # They become visible only if between is selected as an operator on that row
        self.label_1 = QLabel("and")
        self.value_1b_line_edit = QLineEdit(self)
        
        self.value1_layout.addWidget(self.first_combo)
        self.value1_layout.addWidget(self.value1_line_edit)
        self.value1_layout.addWidget(self.label_1)
        self.value1_layout.addWidget(self.value_1b_line_edit)
        self.main_layout.addLayout(self.value1_layout)

        # Hide the between combos
        self.label_1.hide()
        self.value_1b_line_edit.hide()

    def _build_second_filter_row(self):
        self.second_combo=NumberFilterCombo(self)
        self.second_combo.currentTextChanged.connect(lambda _text: self._on_between_toggled(self.second_combo))
        self.value2_line_edit = QLineEdit()
        self.value2_layout = QHBoxLayout()
        
        # Add the initialy hidden  b value widgets
        # They become visible only if between is selected as an operator on that row
        self.label_2 = QLabel("and")
        self.value_2b_line_edit = QLineEdit(self)
        
        self.value2_layout.addWidget(self.second_combo)
        self.value2_layout.addWidget(self.value2_line_edit)
        self.value2_layout.addWidget(self.label_2)
        self.value2_layout.addWidget(self.value_2b_line_edit)
        self.main_layout.addLayout(self.value2_layout)
        
        # Hide the between combos
        self.label_2.hide()
        self.value_2b_line_edit.hide()

    def _on_between_toggled(self, combo:None)->None:
        print_current_location_function(self)
    
        sender = sender = combo if combo is not None else self.sender()
        
        if not isinstance(sender, NumberFilterCombo):
            return

        #Create a boolean for use in the .setVisible method
        between_selected = sender.currentText()=="Between"
        
        if sender is self.first_combo:
            self.value_1b_line_edit.setVisible(between_selected)
            self.label_1.setVisible(between_selected)
            if not between_selected:
                self.value_1b_line_edit.clear()
            
        elif sender is self.second_combo:
            self.value_2b_line_edit.setVisible(between_selected)
            self.label_2.setVisible(between_selected)
            if not between_selected:
                self.value_2b_line_edit.clear()
        return

    def _create_number_clause(
            self,
            combo_box: NumberFilterCombo,
            value_line_edit: QLineEdit,
            b_value_line_edit: QLineEdit,
            ) -> NumberClause | None:

        symbol = combo_box.currentData().symbol

        try:
            value = float(value_line_edit.text().strip())
        except ValueError:
            QMessageBox.warning(
                self,
                f"{combo_box.currentText()} Filter Error",
                "A numeric value is required",
            )
            return None

        value = normalise_from_user_units(
            self.column_units, self.column_quantity_key, value
        )

        value_b = None
        if combo_box.currentText() == "Between":
            try:
                value_b = float(b_value_line_edit.text().strip())
            except ValueError:
                QMessageBox.warning(
                    self,
                    f"{combo_box.currentText()} Filter Error",
                    "Two numeric values are required",
                )
                return None

            value_b = normalise_from_user_units(
                self.column_units, self.column_quantity_key, value_b
            )

        return NumberClause(symbol, value, value_b)