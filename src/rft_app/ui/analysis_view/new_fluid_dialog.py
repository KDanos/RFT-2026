from __future__ import annotations

from typing import TYPE_CHECKING


from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from project import AnalysisObject, AnalysisView, ProjectDataManager
from project.fluid_model import STANDARD_FLUIDS, Fluid, FluidContact, guess_fluid_type_from_psi_ft
from ui.main_window.signal_collection_protocol import SignalCoordinator
from units import convert_from_normalised_to_user_units
from ui.widgets import UnitsComboBox
from utilities import unique_name

if TYPE_CHECKING:
    from ui.depth_gradient_chart.straight_line import StraightLine


class NewFluidDialog(QDialog):
    # Class Signals
    new_fluid_created = pyqtSignal()

    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager,
            view: AnalysisView,
            signal_coordinator:SignalCoordinator,
            pressure_gradient_si: float | None = None,
            zero_pressure_depth_si:float | None = None, 
            base_line: StraightLine | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = project
        self.view: AnalysisView = view
        self.analysis: AnalysisObject = self.view.analysis_object

        # Signal Coordinator
        self.signal_coordinator:SignalCoordinator =signal_coordinator

        # Set module variables
        self.pressure_gradient_si: float | None = pressure_gradient_si
        self.zero_pressure_depth_si:float |None  = zero_pressure_depth_si
        self.base_line: StraightLine | None = base_line
        self.list_of_unit_combos:list[UnitsComboBox]=[]
        self.fluid_single_point:tuple[float,float] |None = (
            self.base_line.starting_point if self.base_line is not None else None)
        self.temp_contact:FluidContact=FluidContact()
        

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.setWindowTitle("New Fluid")
        
        # Create the layout
        self.vertical_layout = QVBoxLayout()
        self.setLayout(self.vertical_layout)
        self.horizontal_layout = QHBoxLayout()    
        self.grid_layout = QGridLayout()
        self.horizontal_layout.addLayout(self.grid_layout)
        self.horizontal_layout.addStretch()
        self.vertical_layout.addLayout(self.horizontal_layout)
        self.vertical_layout.addStretch()

        # Name
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setPlaceholderText("New Fluid Name")
        self.grid_layout.addWidget(self.name_line_edit, 0, 0, 1, 2)

        # Gradient
        self.gradient_label = QLabel("Gradient")
        if self.base_line:
            self.gradient_value = QLabel()
            self.gradient_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.gradient_value = QLineEdit(self)
        self.gradient_units_combo = UnitsComboBox("pressure_gradient", self.project)
        self.list_of_unit_combos.append(self.gradient_units_combo)
        self._update_fluid_gradient_display()
        self.grid_layout.addWidget(self.gradient_label, 1, 0)
        self.grid_layout.addWidget(self.gradient_value, 1, 1)
        self.grid_layout.addWidget(self.gradient_units_combo, 1, 2)

        # Type
        self.fluid_type_label = QLabel("Type")
        self.fluid_type_combo = QComboBox(self)
        self.grid_layout.addWidget(self.fluid_type_label, 2, 0)
        self.grid_layout.addWidget(self.fluid_type_combo, 2, 1)
        with QSignalBlocker(self.fluid_type_combo):
            for fluid_type in STANDARD_FLUIDS.values():
                self.fluid_type_combo.addItem(fluid_type.label, fluid_type)
            if self.pressure_gradient_si:
                psi_ft = convert_from_normalised_to_user_units(
                    "psi/ft",
                    "pressure_gradient",
                    self.pressure_gradient_si,
                )
                self.fluid_spec = guess_fluid_type_from_psi_ft(psi_ft)
                self.fluid_type_combo.setCurrentText(self.fluid_spec.label)

        # Zero Pressure Depth
        self.zero_pressure_depth_label = QLabel("Depth of 0 hydrostatic pressure")
        if self.base_line:
            self.zero_pressure_depth_value = QLabel()
            self.zero_pressure_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        else: 
            self.zero_pressure_depth_value = QLineEdit()
        self.zero_pressure_depth_units_combo = UnitsComboBox("length", self.project)
        self.list_of_unit_combos.append(self.zero_pressure_depth_units_combo)
        self._update_zero_pressure_depth_display()
        self.grid_layout.addWidget(self.zero_pressure_depth_label, 3, 0)
        self.grid_layout.addWidget(self.zero_pressure_depth_value, 3, 1)
        self.grid_layout.addWidget(self.zero_pressure_depth_units_combo, 3, 2)  

        # Contact fluid
        self.contact_label = QLabel("Bottom Contact Fluid")
        self.contact_fluid_combo = QComboBox(self)
        self.contact_fluid_combo.addItem("None", None)
        if self.analysis.fluids:
            for fluid in self.analysis.fluids:
                self.contact_fluid_combo.addItem(fluid.name, fluid)
        self.grid_layout.addWidget(self.contact_label, 4, 0)
        self.grid_layout.addWidget(self.contact_fluid_combo)
        self._update_temp_fluid()
        self._calculate_fluid_contact()

        # Contact Type
        self.contact_type_label = QLabel("Contact Type:")
        self.contact_type_value = QLabel()
        self.grid_layout.addWidget(self.contact_type_label,5,0)
        self.grid_layout.addWidget(self.contact_type_value,5,1)

        # Contact Depth
        self.contact_depth_label = QLabel("Contact Depth")
        if self.base_line:
            self.contact_depth_value = QLabel()
            self.contact_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        else: 
            self.contact_depth_value = QLineEdit()
        self.contact_depth_units_combo = UnitsComboBox("length", self.project)
        self.list_of_unit_combos.append(self.contact_depth_units_combo)
        self.grid_layout.addWidget(self.contact_depth_label, 6, 0)
        self.grid_layout.addWidget(self.contact_depth_value, 6, 1)
        self.grid_layout.addWidget(self.contact_depth_units_combo, 6, 2)
        
        # Contact Pressure
        self.contact_pressure_label = QLabel("Contact Pressure")
        if self.base_line:
            self.contact_pressure_value = QLabel()
            self.contact_pressure_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        else: 
            self.contact_pressure_value = QLineEdit()
        self.contact_pressure_units_combo = UnitsComboBox("pressure", self.project)
        self.list_of_unit_combos.append(self.contact_pressure_units_combo)
        self._update_contact_data_display()
        self.grid_layout.addWidget(self.contact_pressure_label, 7, 0)
        self.grid_layout.addWidget(self.contact_pressure_value, 7, 1)
        self.grid_layout.addWidget(self.contact_pressure_units_combo, 7, 2)
        
        # Button box
        self.button_box_layout = QHBoxLayout()
        self.button_box_layout.addStretch()
        self.vertical_layout.addLayout(self.button_box_layout)
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Create New Fluid"
        )
        self.button_box_layout.addWidget(self.button_box)

    def _calculate_fluid_contact(self)->None:
        if self.contact_fluid_combo.currentData() is None:
            return

        self.temp_contact.bottom_fluid= self.contact_fluid_combo.currentData()

        # Extract contact type
        self.temp_contact.type = self.temp_contact.contact_type()   

        # Calculate contact data 
        self.temp_contact.set_contact_data()   

    def _check_name_uniqueness(self) -> None:
        name = self.name_line_edit.text()
        if not name and self.fluid_type_combo.currentIndex() > 0:
            name = self.fluid_type_combo.currentData().label
        all_names = [fluid.name for fluid in self.analysis.fluids]
        name = unique_name(name, all_names)
        self.name_line_edit.setText(name)
    
    def _connect_signals(self) -> None:
        
        self.name_line_edit.editingFinished.connect(self._check_name_uniqueness)
        
        # Connect all the units combo boxes
        self.gradient_units_combo.currentTextChanged.connect(self._update_fluid_gradient_display)
        self.zero_pressure_depth_units_combo.currentTextChanged.connect(self._update_zero_pressure_depth_display)
        self.contact_depth_units_combo.currentTextChanged.connect(self._update_contact_data_display)
        self.contact_pressure_units_combo.currentTextChanged.connect(self._update_contact_data_display)

        # Update contacts on contact fluid selection change
        self.contact_fluid_combo.currentTextChanged.connect(self._update_contact_data_display)


        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._on_accept)
        self.finished.connect(self._on_finished)
        if self.base_line:
            self.base_line.sigRegionChanged.connect(self._update_fluid_info_from_base_line)
            self.base_line.sigRegionChanged.connect(self._update_contact_data_display)

        # Pass the new fluid created signal to the main window
        self.new_fluid_created.connect(self.signal_coordinator.on_fluids_changed)

    def _on_accept(self) -> None:
        self._check_name_uniqueness()
        name = self.name_line_edit.text().strip()
        fluid_type = self.fluid_type_combo.currentData()
        
        bottom_contact = FluidContact(
             bottom_fluid = self.contact_fluid_combo.currentData()
        )
        
        new_fluid = Fluid(
            name=name,
            type=fluid_type.label,
            gradient_si=self.pressure_gradient_si,
            zero_pressure_depth_si=self.zero_pressure_depth_si,
            bottom_contact=bottom_contact
        )
        #Reset the contact top fluid (to the newly created one)
        bottom_contact.top_fluid = new_fluid
        bottom_contact.type = bottom_contact.contact_type()
        bottom_contact.set_contact_data()

        self.analysis.fluids.append(new_fluid)
        self.project.mark_modified()
        self.new_fluid_created.emit()
        self.accept()

    def _on_finished(self) -> None:
        if self.base_line is None:
            return
        try:
            self.base_line.sigRegionChanged.disconnect(self._update_fluid_info_from_base_line)
        except TypeError:
            pass

    def _update_contact_data_display(self) -> None: 
        self._update_temp_fluid()
        self.temp_contact.bottom_fluid = self.contact_fluid_combo.currentData()
        self.temp_contact.set_contact_data()

        if self.temp_contact.exists:
            print (f"temp_contact depth is: {self.temp_contact.depth}")

            contact_depth = convert_from_normalised_to_user_units(
                self.contact_depth_units_combo.currentText(),
                "length",
                self.temp_contact.depth
            )
            contact_pressure = convert_from_normalised_to_user_units(
                self.contact_pressure_units_combo.currentText(),
                "pressure", 
                self.temp_contact.pressure
            )

            self.contact_type_value.setText(self.temp_contact.type)
            self.contact_depth_value.setText(f"{contact_depth:.1f}")
            self.contact_pressure_value.setText(f"{contact_pressure:.1f}")

            
            self.contact_type_label.setVisible(True)
            self.contact_depth_label.setVisible(True)
            self.contact_depth_value.setVisible(True)
            self.contact_depth_units_combo.setVisible(True)
            self.contact_pressure_label.setVisible(True)
            self.contact_pressure_value.setVisible(True)
            self.contact_pressure_units_combo.setVisible(True)
        else: 
            self.contact_type_label.setVisible(False)
            self.contact_type_value.setText("No contact identified")
            self.contact_depth_label.setVisible(False)
            self.contact_depth_value.setVisible(False)
            self.contact_depth_units_combo.setVisible(False)
            self.contact_pressure_label.setVisible(False)
            self.contact_pressure_value.setVisible(False)
            self.contact_pressure_units_combo.setVisible(False)
    
    def _update_fluid_gradient_display(self) -> None:
        if self.pressure_gradient_si is None:
            return
        current_unit = self.gradient_units_combo.currentText()
        value = convert_from_normalised_to_user_units(
            current_unit,
            "pressure_gradient",
            self.pressure_gradient_si,
        )
        self.gradient_value.setText(f"{value:.3f}")

    def _update_temp_fluid(self)-> Fluid:
        self.temp_fluid = Fluid(
            name = "temp", 
            type= self.fluid_type_combo.currentText(),
            gradient_si = self.pressure_gradient_si, 
            zero_pressure_depth_si= self.zero_pressure_depth_si,
            bottom_contact= self.temp_contact
        )
        self.temp_contact.top_fluid = self.temp_fluid

    def _update_zero_pressure_depth_display(self)->None:
        if self.zero_pressure_depth_si is None:
            return
        current_unit = self.zero_pressure_depth_units_combo.currentText()
        value = convert_from_normalised_to_user_units(
            current_unit, 
            "length", 
            self.zero_pressure_depth_si,
        )
        self.zero_pressure_depth_value.setText(f"{value:.0f}")
    
    def _update_fluid_info_from_base_line(self) -> None:
        self.pressure_gradient_si = self.base_line.calculate_fluid_gradient_si()
        self.zero_pressure_depth_si = self.base_line.calculate_y_intercept_si()
        self._update_fluid_gradient_display()
        self._update_zero_pressure_depth_display()

    
    #--------Public API--------

    def on_project_units_changed(self)->None:
        for combo in self.list_of_unit_combos:
            combo.set_default_unit(self.project)
        self._update_fluid_gradient_display()
        self._update_zero_pressure_depth_display()