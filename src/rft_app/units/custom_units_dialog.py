from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import  (QDialog, QDialogButtonBox, QFrame,  QGridLayout, QLineEdit, QComboBox, 
                            QLabel, QPushButton, QHBoxLayout, QMessageBox, QVBoxLayout)

from project import ProjectDataManager
from units.units_manager import BUILT_IN_UNIT_SYSTEMS, UnitSystem
from ui.widgets.table_widgets import UnitsComboBox
from units import STANDARD_QUANTITIES
from utilities import clear_layout_items, unique_name
from ui import app_icon


class CustomUnitsDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = parent.project
        self.main_window: QObject = parent

        # Set module variables
        self.quantity_unit_pair_dictionary: dict[str, str] = {}

        # Initialisation methods
        self._build_ui()
        self._connect_signals()
        self.exec()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setWindowTitle("Custom Units Manager")

        #Existing User Defined Unit System
        self.manager_frame = QFrame(self)
        self.main_layout.addWidget(self.manager_frame)

        self.manager_layout = QHBoxLayout()
        self.manager_frame.setLayout(self.manager_layout)

        self.defined_systems_label = QLabel("User Defined Unit Systems: ")
        self.user_units_combo = QComboBox(self)
        self.manager_layout.addWidget(self.defined_systems_label)
        self.manager_layout.addWidget(self.user_units_combo)

        # Edit Custom User Unit System
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(app_icon("msc.edit"))
        self.edit_btn.setToolTip("Edit the user unit system")
        self.manager_layout.addWidget(self.edit_btn)

        # Delete Custom User Unit System
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(app_icon("mdi.delete-variant"))
        self.delete_btn.setToolTip("Delete the user unit system")
        self.manager_layout.addWidget(self.delete_btn)

        # Create New Unit System
        self.create_new_btn = QPushButton()
        self.create_new_btn.setIcon(app_icon("msc.repo-create"))
        self.create_new_btn.setToolTip("Create new unit system")
        self.manager_layout.addWidget(self.create_new_btn)

        # Set visibility of buttons and items of combo box
        self._manage_buttons_and_units_system_combo_box()

        # Manager layout
        self.editor_layout = QVBoxLayout()
        self.main_layout.addLayout(self.editor_layout)

        # Button Box
        self.button_box_layout = QHBoxLayout()
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        self.ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_btn.setText("Apply")
        self.ok_btn.setVisible(False)
        self.button_box_layout.addStretch()
        self.button_box_layout.addWidget(self.button_box)
        self.main_layout.addLayout(self.button_box_layout)

    def _connect_signals(self) -> None:
        self.create_new_btn.clicked.connect(self._create_new_or_edit_existing_custom_units_system)
        self.edit_btn.clicked.connect(self._create_new_or_edit_existing_custom_units_system)
        self.delete_btn.clicked.connect(self._delete_existing_custom_units_system)

        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        self.rejected.connect(self._on_rejected)

    def _create_new_or_edit_existing_custom_units_system(self) -> None:
        if self.sender() is self.edit_btn:
            self.editor_mode = "Edit Existing"
        elif self.sender() is self.create_new_btn:
            self.editor_mode = "Create New"

        self.manager_frame.hide()
        frame = self._new_or_edit_units_system_frame()
        self.editor_layout.addWidget(frame)
        self.ok_btn.setVisible(True)

    def _create_quantity_types_and_unit_frame(self, quantity_list: list) -> QFrame:
        self.quantity_unit_frame = QFrame(self)
        self.quantity_unit_frame_layout = QGridLayout()
        self.quantity_unit_frame.setLayout(self.quantity_unit_frame_layout)

        self._update_quantity_types_and_unit_frame(quantity_list)

        return self.quantity_unit_frame

    def _delete_existing_custom_units_system(self) -> None:
        system_to_delete = self.user_units_combo.currentData()
        if system_to_delete is None:
            return

        #Confirmation Message to delete
        result = QMessageBox.question(
                        self,
                        "Delete Custom Unit System",
                        f"""Are you sure you want to delete the unit system {system_to_delete.label}
                        \n This action is not reversible.""",
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.Cancel)
        if result != QMessageBox.StandardButton.Yes:
            return

        self.project.user_unit_systems.remove(system_to_delete)

        if self.project.current_unit_system.key == system_to_delete.key:
            self.project.current_unit_system = BUILT_IN_UNIT_SYSTEMS[2] #default to Field

        self.main_window.reset_units_combo()
        # Refresh the user defined unit systems in the unit manager window
        self._manage_buttons_and_units_system_combo_box()

        self.project.mark_modified()

    def _filter_quantity_types(self, text: str) -> None:
        #Ensure to capture any changes to the units combos before the filtering happened
        self.quantity_unit_pair_dictionary = self._update_units_by_quantity_dictionary()

        filtered_quantities = self._filtered_available_quantity_types(text)
        self._update_quantity_types_and_unit_frame(filtered_quantities)

    def _filtered_available_quantity_types(self, text: str = "") -> list:
        all_quantities = [(key, value)
                            for key, value in STANDARD_QUANTITIES.items()
                            if value.is_numeric]
        needle = self.search_line_edit.text().strip().casefold()
        if needle:
            filtered_quantities = [(key, value)
                                for key, value in all_quantities
                                if needle in value.label.strip().casefold()]
        else:
            filtered_quantities = all_quantities

        return filtered_quantities

    def _manage_buttons_and_units_system_combo_box(self) -> None:
        # Clear existing inputs
        self.user_units_combo.clear()

        # Update combo box and add buttons
        if len(self.project.user_unit_systems) == 0:
            self.user_units_combo.addItem("None")
            self.edit_btn.setVisible(False)
            self.delete_btn.setVisible(False)
        else:
            for unit in self.project.user_unit_systems:
                self.user_units_combo.addItem(unit.label, unit)
                self.edit_btn.setVisible(True)
                self.delete_btn.setVisible(True)

    def _new_or_edit_units_system_frame(self) -> QFrame:
        frame = QFrame(self)
        self.frame_layout = QGridLayout()
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(self.frame_layout)

        # Name input
        self.new_name_line_edit = QLineEdit(frame)

        if self.editor_mode == "Create New":
            self.new_name_line_edit.setPlaceholderText("New Unit System Name")
        elif self.editor_mode == "Edit Existing":
            current_name = self.user_units_combo.currentText()
            self.new_name_line_edit.setText(current_name)
        self.frame_layout.addWidget(self.new_name_line_edit)

        #Pre-populate New Unit System
        pre_populate_label = QLabel("Pre-populate from: ")
        self.all_systems_combo = QComboBox(self)
        for system in self.project.available_unit_systems:
            self.all_systems_combo.addItem(system.label, system)

        # Pre-populate default
        if self.editor_mode == "Create New":
            self.all_systems_combo.setCurrentText(self.project.current_unit_system.label)
        elif self.editor_mode == "Edit Existing":
            self.all_systems_combo.setCurrentText(self.user_units_combo.currentText())
        self.all_systems_combo.currentTextChanged.connect(self._update_default_units_in_combos)

        self.frame_layout.addWidget(pre_populate_label, 1, 0)
        self.frame_layout.addWidget(self.all_systems_combo, 1, 1)

        #List all available quantity types with default unit selection
        all_quantities = [(key, value)
                            for key, value in STANDARD_QUANTITIES.items()
                            if value.is_numeric]

        #Extract default quantity-unit pairs for all quantities
        self.options_frame = self._create_quantity_types_and_unit_frame(all_quantities)
        self._update_default_units_in_combos()
        self.quantity_unit_pair_dictionary = self._update_units_by_quantity_dictionary()
        self.frame_layout.addWidget(self.options_frame, 3, 0, 1, 2)

        #Quantity filter
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Quantity Type: ")
        self.search_line_edit.textChanged.connect(self._filter_quantity_types)
        self.frame_layout.addWidget(self.search_line_edit, 2, 0)

        return frame

    def _on_accept(self) -> None:
        # Ensure all changes have been captured
        self.quantity_unit_pair_dictionary = self._update_units_by_quantity_dictionary()

        # If editing, remove the system being edited
        if self.editor_mode == "Edit Existing":
            existing_system = self.user_units_combo.currentData()
            self.project.user_unit_systems.remove(existing_system)

        # Extract the label and key for the new unit system
        label_text = self.new_name_line_edit.text().strip()
        user_selected_name = label_text if label_text else "user_unit_system"
        existing_names = [system.label for system in self.project.available_unit_systems]
        new_name = unique_name(user_selected_name, existing_names)

        # Create and save the new unit system
        new_system = UnitSystem(new_name, new_name, self.quantity_unit_pair_dictionary)
        self.project.user_unit_systems.append(new_system)

        # Reset the project unit system to the new one
        self.project.current_unit_system = new_system

        self.main_window.reset_units_combo()

        self.project.mark_modified()

        self.accept()

    def _on_rejected(self) -> None:
        self.main_window.reset_units_combo()

    def _update_default_units_in_combos(self) -> None:
        layout = self.quantity_unit_frame_layout
        selected_system = self.all_systems_combo.currentData()
        if selected_system is None:
            return

        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if not isinstance(widget, UnitsComboBox):
                continue
            else:
                quantity = widget.quantity_key
                unit = selected_system.units_by_quantity.get(quantity, "")
                if unit:
                    widget.setCurrentText(unit)
                    self.quantity_unit_pair_dictionary[quantity] = unit

    def _update_quantity_types_and_unit_frame(self, quantity_list: list | None = None) -> None:
        if quantity_list is None:
            return

        clear_layout_items(self.quantity_unit_frame_layout)
        for i in range(len(quantity_list)):
            key, value = quantity_list[i]
            new_label = QLabel(value.label)
            units_combo = UnitsComboBox(key, self.project)
            # Restore draft unit selection (not only project current system)
            saved = self.quantity_unit_pair_dictionary.get(key)
            if saved:
                units_combo.setCurrentText(saved)

            self.quantity_unit_frame_layout.addWidget(new_label, i, 0)
            self.quantity_unit_frame_layout.addWidget(units_combo, i, 1)

    def _update_units_by_quantity_dictionary(self) -> dict[str, str] | None:
        layout = self.options_frame.layout()
        if layout.count() == 0:
            return self.quantity_unit_pair_dictionary

        if not self.quantity_unit_pair_dictionary:
            dictionary = {'ignore': "", 'text': "", 'well': ""}
        else:
            dictionary = self.quantity_unit_pair_dictionary

        for row in range(layout.rowCount()):
            item = layout.itemAtPosition(row, 0)
            if item is None:
                continue
            label = layout.itemAtPosition(row, 0).widget()
            if label is None:
                continue
            quantity_label = label.text()
            quantity_key = next(
                                (key for key, value in STANDARD_QUANTITIES.items()
                                if value.label == quantity_label), None)
            combo = layout.itemAtPosition(row, 1).widget()
            unit = combo.currentText()
            dictionary[quantity_key] = unit

        return dictionary

    #--------Public API--------
