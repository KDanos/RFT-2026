from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QSpinBox, QVBoxLayout, QWidget,)

from project import ProjectDataManager
from units.units_combo_box import UnitsComboBox
from units.units_manager import STANDARD_QUANTITIES
from units.units_normalisation import convert_from_user_unit_to_user_unit
from utilities.global_functions import limit_decimals_str


class UnitConversionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = ProjectDataManager()

        # Set module variables
        self.from_unit_combo: UnitsComboBox | None = None
        self.to_unit_combo: UnitsComboBox | None = None

        # Initialisation methods
        self._build_ui()
        self._create_unit_combo_boxes()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.setWindowTitle("Unit Converter")
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))

        # Layouts
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)
        self.h_layout = QHBoxLayout()
        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addStretch()

        self.main_layout = QGridLayout()
        self.h_layout.addLayout(self.main_layout)
        self.h_layout.addStretch()

        # Quantity selection
        self.quantity_label = QLabel("Quantity")
        self.quantity_combo = QComboBox()
        self.main_layout.addWidget(self.quantity_label, 0, 0)
        self.main_layout.addWidget(self.quantity_combo, 0, 1)
        for quantity in STANDARD_QUANTITIES.values():
            self.quantity_combo.addItem(quantity.label, quantity)

        # Decimal point
        self.decimals_label = QLabel("Significant Figures:")
        self.decimals_spin = QSpinBox()
        self.decimals_spin.setRange(0, 10)
        self.decimals_spin.setValue(3)
        self.decimals_spin.setFixedWidth(100)
        self.decimals_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.decimals_label, 1, 0)
        self.main_layout.addWidget(self.decimals_spin, 1, 1)

        # To and From labels
        self.from_label = QLabel("From: ")
        self.from_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.to_label = QLabel("To: ")
        self.to_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.from_label, 2, 0)
        self.main_layout.addWidget(self.to_label, 2, 2)

        # Input and results widgets
        self.input_value = QLineEdit(self)
        self.input_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.input_value, 3, 1)

        self.result_value = QLineEdit()
        self.result_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_value.setReadOnly(True)
        self.main_layout.addWidget(self.result_value, 3, 3)

        # Toolbox
        self.buttonbox = QDialogButtonBox(self)
        self.buttonbox.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        self.buttonbox_layout = QHBoxLayout()
        self.buttonbox_layout.addStretch()
        self.buttonbox_layout.addWidget(self.buttonbox)
        self.v_layout.addLayout(self.buttonbox_layout)

    def _connect_signals(self) -> None:
        self.quantity_combo.currentIndexChanged.connect(self._on_quantity_selection_change)

        self.from_unit_combo.currentIndexChanged.connect(self._make_conversion)
        self.to_unit_combo.currentIndexChanged.connect(self._make_conversion)
        self.input_value.textChanged.connect(self._make_conversion)
        self.decimals_spin.valueChanged.connect(self._make_conversion)

        self.buttonbox.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.close)

    def _create_unit_combo_boxes(self) -> None:
        quantity_key = self.quantity_combo.currentData().key
        self.from_unit_combo = UnitsComboBox(quantity_key, self.project.current_unit_system)
        self.to_unit_combo = UnitsComboBox(quantity_key, self.project.current_unit_system)
        self.main_layout.addWidget(self.from_unit_combo, 3, 0)
        self.main_layout.addWidget(self.to_unit_combo, 3, 2)

    def _make_conversion(self) -> None:
        input_unit = self.from_unit_combo.currentText()
        output_unit = self.to_unit_combo.currentText()
        value_input = self.input_value.text()

        decimals = self.decimals_spin.value()
        if not value_input:
            return

        if float(value_input):
            value = float(value_input)
            result = convert_from_user_unit_to_user_unit(input_unit, output_unit, value)
            self.result_value.setText(limit_decimals_str(result, decimals))
        else:
            QMessageBox.critical(
                self,
                "Conversion Error",
                "A purely numeric value is required to achieve a conversion",
                )
            self.result_value.setText("")

    def _on_quantity_selection_change(self) -> None:
        quantity_key = self.quantity_combo.currentData().key
        for combo in [self.from_unit_combo, self.to_unit_combo]:
            if combo is None:
                continue
            with QSignalBlocker(combo):
                combo.update_units_list(quantity_key)

    #--------Public API--------
    # (none)
