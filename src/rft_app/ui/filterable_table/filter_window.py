from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QShowEvent
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
)
from qtpy.QtWidgets import QMessageBox

from ui.filterable_table.filter_combos import NumberFilterCombo, TextFilterCombo
from ui.filterable_table.filter_specs import FilterSpecNumber, FilterSpecText, NumberClause, TextClause
from units import STANDARD_QUANTITIES, normalise_from_user_units


class FilteringWindow(QDialog):

    def __init__(
            self,
            parent=None,
            column_name: str = "",
            filter_name: str = "",
            ) -> None:
        super().__init__(parent)

        # Set project variables
        # (none)

        # Set module variables
        self.column_name = parent.column_name
        self.filter_name = filter_name
        self.column_units = parent.column_units
        self.column_quantity_key = parent.column_quantity_key
        self.column_is_numeric = STANDARD_QUANTITIES[self.column_quantity_key].is_numeric

        # Initialisation methods
        self._build_ui()

    #--------Private UI--------

    def _build_first_number_filter_row(self) -> None:
        self.first_combo = NumberFilterCombo(self)

        if self.filter_name != "":
            self.first_combo.setCurrentText(self.filter_name)
        self.first_combo.currentTextChanged.connect(
            lambda _text: self._on_between_toggled(self.first_combo)
        )
        self.value1_line_edit = QLineEdit()
        self.value1_layout = QHBoxLayout()

        self.label_1 = QLabel("and")
        self.value_1b_line_edit = QLineEdit(self)

        self.value1_layout.addWidget(self.first_combo)
        self.value1_layout.addWidget(self.value1_line_edit)
        self.value1_layout.addWidget(self.label_1)
        self.value1_layout.addWidget(self.value_1b_line_edit)
        self.main_layout.addLayout(self.value1_layout)

        self.label_1.hide()
        self.value_1b_line_edit.hide()

    def _build_first_text_filter_row(self) -> None:
        self.first_combo = TextFilterCombo(self)
        if self.filter_name != "":
            self.first_combo.setCurrentText(self.filter_name)
        self.value1_line_edit = QLineEdit()
        self.value1_layout = QHBoxLayout()

        self.value1_layout.addWidget(self.first_combo)
        self.value1_layout.addWidget(self.value1_line_edit)
        self.main_layout.addLayout(self.value1_layout)

    def _build_second_number_filter_row(self) -> None:
        self.second_combo = NumberFilterCombo(self)
        self.second_combo.currentTextChanged.connect(
            lambda _text: self._on_between_toggled(self.second_combo)
        )
        self.value2_line_edit = QLineEdit()
        self.value2_layout = QHBoxLayout()

        self.label_2 = QLabel("and")
        self.value_2b_line_edit = QLineEdit(self)

        self.value2_layout.addWidget(self.second_combo)
        self.value2_layout.addWidget(self.value2_line_edit)
        self.value2_layout.addWidget(self.label_2)
        self.value2_layout.addWidget(self.value_2b_line_edit)
        self.main_layout.addLayout(self.value2_layout)

        self.label_2.hide()
        self.value_2b_line_edit.hide()

    def _build_second_text_filter_row(self) -> None:
        self.second_combo = TextFilterCombo(self)
        self.value2_line_edit = QLineEdit()
        self.value2_layout = QHBoxLayout()

        self.value2_layout.addWidget(self.second_combo)
        self.value2_layout.addWidget(self.value2_line_edit)
        self.main_layout.addLayout(self.value2_layout)

    def _build_ui(self) -> None:
        window_title = "Number Filter" if self.column_is_numeric else "Text Filter"
        self.setWindowTitle(window_title)
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))

        self.main_layout = QVBoxLayout(self)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Apply Filter")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        column_label = QLabel(self.column_name)
        label_layout = QHBoxLayout()
        label_layout.addWidget(column_label)
        label_layout.addStretch()
        self.main_layout.addLayout(label_layout)

        if self.column_is_numeric:
            self._build_first_number_filter_row()
        else:
            self._build_first_text_filter_row()

        self.radio_layout = QHBoxLayout()
        self.and_radio_btn = QRadioButton("And")
        self.or_radio_btn = QRadioButton("Or")
        self.and_radio_btn.setChecked(True)
        self.radio_layout.addWidget(self.and_radio_btn)
        self.radio_layout.addWidget(self.or_radio_btn)
        self.radio_layout.addStretch()
        self.main_layout.addLayout(self.radio_layout)

        if self.column_is_numeric:
            self._build_second_number_filter_row()
        else:
            self._build_second_text_filter_row()

        self.main_layout.addStretch()
        self.main_layout.addWidget(button_box)

        self._on_between_toggled(self.first_combo)

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
            if value > value_b:
                QMessageBox.warning(
                    self,
                    f"{combo_box.currentText()} Filter Error",
                    "The lower bound must be less than then upper bound",
                )
                return None

        return NumberClause(symbol, value, value_b)

    def _create_text_clause(
            self,
            combo: TextFilterCombo,
            line_edit: QLineEdit,
            ) -> TextClause | None:
        if not line_edit.text().strip():
            QMessageBox.warning(
                self,
                f"{combo.currentText()} Filter Error",
                "No text has been entered",
            )
            return None

        label = combo.currentData().label
        text = line_edit.text().strip()

        return TextClause(label, text)

    def _on_accept(self) -> None:
        if self.column_is_numeric:
            clause_1 = self._create_number_clause(
                self.first_combo, self.value1_line_edit, self.value_1b_line_edit
            )
        else:
            clause_1 = self._create_text_clause(self.first_combo, self.value1_line_edit)

        if clause_1 is None:
            return

        clause_2 = None
        if self.value2_line_edit.text().strip():
            if self.column_is_numeric:
                clause_2 = self._create_number_clause(
                    self.second_combo, self.value2_line_edit, self.value_2b_line_edit
                )
                if clause_2 is None:
                    return
            else:
                clause_2 = self._create_text_clause(self.second_combo, self.value2_line_edit)

        self.connector = None if not clause_2 else ("and" if self.and_radio_btn.isChecked() else "or")
        if self.column_is_numeric:
            self.result_spec = FilterSpecNumber(clause_1, self.connector, clause_2)
        else:
            self.result_spec = FilterSpecText(clause_1, self.connector, clause_2)
        self.accept()

    def _on_between_toggled(self, combo: NumberFilterCombo | None = None) -> None:
        sender = combo if combo is not None else self.sender()

        if not isinstance(sender, NumberFilterCombo):
            return

        between_selected = sender.currentText() == "Between"

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

    #--------Public API--------

    def showEvent(self, event: QShowEvent) -> None:
        """Make a specific line edit the focus when the window (self) is shown"""
        super().showEvent(event)
        self.value1_line_edit.setFocus(Qt.FocusReason.OtherFocusReason)
