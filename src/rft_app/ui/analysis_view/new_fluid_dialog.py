from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QSignalBlocker, pyqtSignal
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
from project.fluids_model import STANDARD_FLUIDS, Fluid, guess_fluid_type_from_psi_ft
from units import convert_from_normalised_to_user_units
from ui.widgets import UnitsComboBox
from utilities import unique_name

if TYPE_CHECKING:
    from ui.depth_gradient_chart.straight_line import StraightLine


class NewFluidDialog(QDialog):
    # Class Signals
    fluid_created = pyqtSignal()

    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager,
            view: AnalysisView,
            pressure_gradient: float | None = None,
            gradient_in_SI: bool = False,
            base_line: StraightLine | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = project
        self.view: AnalysisView = view
        self.analysis: AnalysisObject = self.view.analysis_object

        # Set module variables
        self.pressure_gradient: float | None = pressure_gradient
        self.gradient_in_SI: bool = gradient_in_SI
        self.base_line: StraightLine | None = base_line

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.setWindowTitle("New Fluid")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addStretch()

        # Name
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setPlaceholderText("New Fluid Name")
        self.grid_layout.addWidget(self.name_line_edit, 0, 0, 1, 2)

        # Gradient
        self.gradient_label = QLabel("Gradient")
        if self.base_line:
            self.gradient_value = QLabel()
        else:
            self.gradient_value = QLineEdit(self)
        self.gradient_units_combo = UnitsComboBox("pressure_gradient", self.project)
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
            if self.pressure_gradient:
                psi_ft = convert_from_normalised_to_user_units(
                    "psi/ft",
                    "pressure_gradient",
                    self.pressure_gradient,
                )
                self.fluid_spec = guess_fluid_type_from_psi_ft(psi_ft)
                self.fluid_type_combo.setCurrentText(self.fluid_spec.label)

        # Contact fluid
        self.contact_label = QLabel("Bottom Contact Fluid")
        self.contact_fluid_combo = QComboBox(self)
        self.contact_fluid_combo.addItem("None", None)
        if self.analysis.fluids:
            for fluid in self.analysis.fluids:
                self.contact_fluid_combo.addItem(fluid.name, fluid)
        self.grid_layout.addWidget(self.contact_label, 3, 0)
        self.grid_layout.addWidget(self.contact_fluid_combo)

        # Test label
        self.test_label = QLabel(self)
        self.test_label.setText("Waiting to hear signal from line")
        self.grid_layout.addWidget(self.test_label, 4, 0, 1, 3)

        # Button box
        self.button_box_layout = QHBoxLayout()
        self.button_box_layout.addStretch()
        self.main_layout.addLayout(self.button_box_layout)
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Create New Fluid"
        )
        self.button_box_layout.addWidget(self.button_box)

    def _check_name_uniqueness(self) -> None:
        name = self.name_line_edit.text()
        if not name and self.fluid_type_combo.currentIndex() > 0:
            name = self.fluid_type_combo.currentData().label
        all_names = [fluid.name for fluid in self.analysis.fluids]
        name = unique_name(name, all_names)
        self.name_line_edit.setText(name)

    def _connect_signals(self) -> None:
        self.name_line_edit.editingFinished.connect(self._check_name_uniqueness)
        self.gradient_units_combo.currentTextChanged.connect(self._update_fluid_gradient_display)
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._on_accept)
        self.finished.connect(self._on_finished)
        if self.base_line:
            self.base_line.sigRegionChanged.connect(self._update_fluid_info_from_base_line)

    def _on_accept(self) -> None:
        self._check_name_uniqueness()
        name = self.name_line_edit.text().strip()
        fluid_type = self.fluid_type_combo.currentData()
        new_fluid = Fluid(
            name=name,
            type=fluid_type.label,
            gradient_si=self.pressure_gradient,
            contact_fluid=self.contact_fluid_combo.currentData(),
        )
        self.analysis.fluids.append(new_fluid)
        self.project.mark_modified()
        self.fluid_created.emit()
        self.accept()

    def _on_finished(self) -> None:
        if self.base_line is None:
            return
        try:
            self.base_line.sigRegionChanged.disconnect(self._update_fluid_info_from_base_line)
        except TypeError:
            pass

    def _update_fluid_gradient_display(self) -> None:
        if self.pressure_gradient is None:
            return
        current_unit = self.gradient_units_combo.currentText()
        value = convert_from_normalised_to_user_units(
            current_unit,
            "pressure_gradient",
            self.pressure_gradient,
        )
        self.gradient_value.setText(f"{value:.3}")

    def _update_fluid_info_from_base_line(self) -> None:
        self.pressure_gradient = self.base_line.calculate_line_gradient()
        self._update_fluid_gradient_display()

    #--------Public API--------
