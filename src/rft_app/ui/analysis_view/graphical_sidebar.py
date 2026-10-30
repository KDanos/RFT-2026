from operator import attrgetter
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMenu, QScrollArea, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,)

from model.canonical_names import (
    CANONICAL_EXCESS_PRESSURE,
    CANONICAL_FORMATION_PRESSURE,
    CANONICAL_VERTICAL_DEPTH,
    )
from model.data_models import AnalysisObject
from model.fluid_model import STANDARD_FLUIDS, Fluid
from model.view_state import ViewWidgetSidebar
from project import AnalysisView, ColumnSpec, ProjectDataManager
from ui.analysis_view.analysis_view_data_manager import build_scatter_series
from ui.analysis_view.fluid_actions import confirm_delete_fluid
from ui.main_window.project_signals import ProjectSignals
from units import convert_from_normalised_to_user_units, normalise_from_user_units
from units.units_combo_box import UnitsComboBox
from utilities.global_functions import limit_decimals_float, limit_decimals_str

if TYPE_CHECKING:
    from ui.analysis_view import AnalysisViewWidget


class GraphicalSidebar(QFrame):
    reference_fluid_changed = pyqtSignal(object)  # object instead of Fluid | None

    # Inherited variables

    # Project
    # None

    # Module
    # None

    # Initialisation Methods
    # None

    def __init__(
        self,
        parent: QWidget,
        project: ProjectDataManager,
        col_specs: list[ColumnSpec],
        signals: ProjectSignals,
        ) -> None:
        super().__init__(parent)

        # Set project variables
        self.parent: AnalysisViewWidget = parent
        self.project: ProjectDataManager = project
        self.col_specs: list[ColumnSpec] = col_specs
        self.analysis: AnalysisObject = self.parent.analysis
        self.view: AnalysisView = self.parent.view
        self.sidebar_summary: ViewWidgetSidebar = self.view.sidebar
        self.signals: ProjectSignals = signals

        # Set module variables
        self.ref_fluid: Fluid | None = None
        self.active_fluid: Fluid | None = None
        self.pressure_unit: str = ""
        self.depth_unit: str = ""
        self.unit_combo_value_pairs: dict[QComboBox, tuple[QDoubleSpinBox | QLabel, str, str]] = {}

        # Initialisation methods
        self._extract_current_table_depth_and_pressure_units()
        self._build_ui()
        self._populate_all_fluid_combos()
        self._create_visible_fluids_tree()
        self._populate_widgets_from_persisted_data()
        self._define_unit_combo_value_pairs()
        self._connect_signals()
        self._refresh_depth_gradient_plots()

    #--------Private UI--------

    def _build_ui(self) -> None:
        # Scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)  # required, otherwise the scroll_area takes only a small space and does not expand to fill the layout
        self.scroll_area.setStyleSheet("QScrollArea { border: None }")  # remove the visible border
        self.scroll_area_layout = QVBoxLayout()
        self.scroll_area_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_layout.addWidget(self.scroll_area)

        # Set the main Layout
        self.setLayout(self.scroll_area_layout)

        # Main Container-effectively self, if no scroll area was required
        self.main_container = QFrame(self)
        self.scroll_area.setWidget(self.main_container)
        self.main_container.setAutoFillBackground(False)  # required to avoid the main_container setting its background to grey
        self.main_container.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontal_layout = QHBoxLayout()
        self.main_layout.addLayout(self.horizontal_layout)

        self.grid_layout = QGridLayout()
        self.horizontal_layout.addLayout(self.grid_layout)
        self.horizontal_layout.addStretch()
        self.main_layout.addStretch()
        
        # self.setLayout(self.main_layout)
        self.main_container.setLayout(self.main_layout)

        # Reference fluid selection
        self.ref_fluid_label = QLabel("Reference Fluid")
        self.ref_fluid_combo = QComboBox(self)
        self.grid_layout.addWidget(self.ref_fluid_label, 0, 0)
        self.grid_layout.addWidget(self.ref_fluid_combo, 0, 1)

        # Scatter Series Definition
        self.primary_identifier_label = QLabel("Color Series Identifier")
        self.secondary_identifier_label = QLabel("Symbol Series Identifier")
        self.primary_identifier_combo = QComboBox(self)
        self.secondary_identifier_combo = QComboBox(self)
        self.grid_layout.addWidget(self.primary_identifier_label, 1, 0)
        self.grid_layout.addWidget(self.primary_identifier_combo, 1, 1)
        self.grid_layout.addWidget(self.secondary_identifier_label, 2, 0)
        self.grid_layout.addWidget(self.secondary_identifier_combo, 2, 1)
        self._populate_identifier_combo(self.primary_identifier_combo)
        self._populate_identifier_combo(self.secondary_identifier_combo)

        # Active Fluid Selection
        self.grid_layout.setRowMinimumHeight(3, 20)
        self.active_fluid_h_layout = QHBoxLayout()
        self.grid_layout.addLayout(self.active_fluid_h_layout, 4, 0, 1, 2)
        self.active_fluid_grid = QGridLayout()
        self.active_fluid_h_layout.addLayout(self.active_fluid_grid)
        self.active_fluid_h_layout.addStretch()
        self.active_fluid_label = QLabel("Active Fluid")
        self.active_fluid_combo = QComboBox(self)
        self.active_fluid_grid.addWidget(self.active_fluid_label, 0, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_combo, 0, 1)

        # Active Fluid Plotting depth
        self.active_fluid_plotting_depth_label = QLabel("Plotting Depth: ")
        self.active_fluid_grid.addWidget(self.active_fluid_plotting_depth_label, 1, 0)
        # Min
        self.active_fluid_min_plotting_depth_label = QLabel("Min:")
        self.active_fluid_min_plotting_depth_value = QDoubleSpinBox(self)
        self.active_fluid_min_plotting_depth_value.setRange(-1000000,1000000)
        self.active_fluid_min_plotting_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_min_plotting_depth_unit = UnitsComboBox("length", self.project.current_unit_system)
        self.active_fluid_grid.addWidget(self.active_fluid_min_plotting_depth_label, 2, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_min_plotting_depth_value, 2, 1)
        self.active_fluid_grid.addWidget(self.active_fluid_min_plotting_depth_unit, 2, 2)
        # Max
        self.active_fluid_max_plotting_depth_label = QLabel("Max:")
        self.active_fluid_max_plotting_depth_value = QDoubleSpinBox(self)
        self.active_fluid_max_plotting_depth_value.setRange(-1000000,1000000)
        self.active_fluid_max_plotting_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_max_plotting_depth_unit = UnitsComboBox("length", self.project.current_unit_system)
        self.active_fluid_grid.addWidget(self.active_fluid_max_plotting_depth_label, 3, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_max_plotting_depth_value, 3, 1)
        self.active_fluid_grid.addWidget(self.active_fluid_max_plotting_depth_unit, 3, 2)

        # Active Fluid Details
        self.active_fluid_definition_label = QLabel("Definition:")
        self.active_fluid_grid.addWidget(self.active_fluid_definition_label, 4, 0)
        # Type
        self.active_fluid_type_label = QLabel("Type:")
        self.active_fluid_type_combo = QComboBox()
        self.active_fluid_grid.addWidget(self.active_fluid_type_label, 5, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_type_combo, 5, 1)

        # Gradient
        self.active_fluid_gradient_label = QLabel("Gradient: ")
        self.active_fluid_gradient_value = QDoubleSpinBox(self)
        self.active_fluid_gradient_value.setRange(-1000000,1000000)
        self.active_fluid_gradient_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_gradient_unit = UnitsComboBox("pressure_gradient", self.project.current_unit_system)
        self.active_fluid_grid.addWidget(self.active_fluid_gradient_label, 6, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_gradient_value, 6, 1)
        self.active_fluid_grid.addWidget(self.active_fluid_gradient_unit, 6, 2)
        # Zero Pressure Depth
        self.active_fluid_zpd_label = QLabel("Zero Pressure Depth: ")
        self.active_fluid_zpd_value = QDoubleSpinBox(self)
        self.active_fluid_zpd_value.setRange(-1000000,1000000)
        self.active_fluid_zpd_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_zpd_unit = UnitsComboBox("length", self.project.current_unit_system)
        self.active_fluid_grid.addWidget(self.active_fluid_zpd_label, 7, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_zpd_value, 7, 1)
        self.active_fluid_grid.addWidget(self.active_fluid_zpd_unit, 7, 2)

        # Contact Fluid:
        self.active_fluid_contact_label = QLabel("Bottom Contact:")
        self.contact_fluid_combo = QComboBox()
        self.active_fluid_grid.addWidget(self.active_fluid_contact_label, 8, 0)
        self.active_fluid_grid.addWidget(self.contact_fluid_combo, 8, 1)

        self.contact_type_label = QLabel("Type:")
        self.contact_type_value = QLabel("")
        self.contact_type_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_grid.addWidget(self.contact_type_label, 9, 0)
        self.active_fluid_grid.addWidget(self.contact_type_value, 9, 1)

        self.contact_depth_label = QLabel("Contact Depth:")
        self.contact_depth_value = QLabel()
        self.contact_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_depth_unit = UnitsComboBox("length", self.project.current_unit_system)
        self.active_fluid_grid.addWidget(self.contact_depth_label, 10, 0)
        self.active_fluid_grid.addWidget(self.contact_depth_value, 10, 1)
        self.active_fluid_grid.addWidget(self.contact_depth_unit, 10, 2)

        self.contact_pressure_label = QLabel("Contact Pressure:")
        self.contact_pressure_value = QLabel()
        self.contact_pressure_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_pressure_unit = UnitsComboBox("pressure", self.project.current_unit_system)
        self.active_fluid_grid.addWidget(self.contact_pressure_label, 11, 0)
        self.active_fluid_grid.addWidget(self.contact_pressure_value, 11, 1)
        self.active_fluid_grid.addWidget(self.contact_pressure_unit, 11, 2)

        # Visible Fluids
        self.grid_layout.setRowMinimumHeight(5, 20)
        self.visible_fluids_label = QLabel("Analysis Fluids")
        self.grid_layout.addWidget(self.visible_fluids_label, 6, 0, 1, 2)
        self.visible_fluids_tree = QTreeWidget(self)
        self.grid_layout.addWidget(self.visible_fluids_tree, 7, 0, 1, 3)

        # Create empty space below the Visible Tree Widget
        self.grid_layout.setRowMinimumHeight(8, 100)

    def _connect_signals(self) -> None:
        # Reference Fluid
        self.ref_fluid_combo.currentIndexChanged.connect(
            lambda _idx: self._on_ref_fluid_combo_changed()
            )

        # Series Identifier
        for combo in [self.primary_identifier_combo, self.secondary_identifier_combo]:
            combo.currentIndexChanged.connect(
                lambda _idx, sender=combo: self._update_identifier_combo(sender)
                )
            combo.currentIndexChanged.connect(
                lambda _idx: self.define_scatters_for_plotting()
                )

        # Active Fluid
        self.active_fluid_combo.currentIndexChanged.connect(
            lambda _idx: self._on_active_fluid_combo_changed()
            )
        self.contact_fluid_combo.currentIndexChanged.connect(
            lambda _idx: self._on_bottom_contact_fluid_combo_changed()
            )
        self.active_fluid_type_combo.currentIndexChanged.connect(
            lambda idx: self._on_active_fluid_type_combo_changed()
            )
        self.active_fluid_min_plotting_depth_value.editingFinished.connect(self._on_active_fluid_min_depth_changed)
        self.active_fluid_max_plotting_depth_value.editingFinished.connect(self._on_active_fluid_max_depth_changed)
        self.active_fluid_gradient_value.editingFinished.connect(self._on_active_fluid_gradient_changed)
        self.active_fluid_zpd_value.editingFinished.connect(self._on_active_fluid_zpd_changed)
        
        # Visible fluids
        self.visible_fluids_tree.itemChanged.connect(self._on_fluid_visibility_tree_item_change)
        self.visible_fluids_tree.customContextMenuRequested.connect(self._on_visible_fluid_context_menu_request)

        # Unit combos  
        for combo in self.unit_combo_value_pairs:
            combo.currentIndexChanged.connect(
                lambda _idx, combo=combo: self._update_single_value_on_units_change(combo)
                )

    def _create_visible_fluids_tree(self) -> None:
        tree = self.visible_fluids_tree
        tree.setHeaderLabels(["Name", "Visible", "Editable"])

        with QSignalBlocker(tree):
            tree.clear()
            # Ensure 1st column is left alligned
            tree.setIndentation(0)
            # Create a right click drop down menu option
            tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

            tree.clear()
            for fluid in self.analysis.fluids:
                fluid_item = QTreeWidgetItem([fluid.name, "", ""])
                fluid_item.setData(0, Qt.ItemDataRole.UserRole, fluid)
                fluid_item.setCheckState(1, Qt.CheckState.Unchecked)
                fluid_item.setFlags(fluid_item.flags() | Qt.ItemFlag.ItemIsEditable)
                tree.addTopLevelItem(fluid_item)

            # Provide a minimum height to the tree widget, to ensure the whole tree is visible in the sidebar
            height = (
                tree.frameWidth() * 2
                + tree.header().height()
                + sum(tree.sizeHintForRow(i) for i in range(tree.topLevelItemCount()))
                )
            tree.setMinimumHeight(height)

            # Reduce the width of the last 2 columns to the minimum
            tree.resizeColumnToContents(1)
            tree.resizeColumnToContents(2)

            # Remove the frame line around the tree
            tree.setFrameShape(QFrame.Shape.NoFrame)
            tree.header().setFrameShape(QFrame.Shape.NoFrame)

    def _define_unit_combo_value_pairs(self) -> None:
        self.unit_combo_value_pairs = {
            self.active_fluid_min_plotting_depth_unit:
            (self.active_fluid_min_plotting_depth_value, "length", "plotting_depth_min_si"),

            self.active_fluid_max_plotting_depth_unit:
            (self.active_fluid_max_plotting_depth_value, "length", "plotting_depth_max_si"),

            self.active_fluid_gradient_unit:
            (self.active_fluid_gradient_value, "pressure_gradient", "gradient_si"),

            self.active_fluid_zpd_unit:
            (self.active_fluid_zpd_value, "length", "zero_pressure_depth_si"),

            self.contact_depth_unit:
            (self.contact_depth_value, "length", "bottom_contact.depth"),

            self.contact_pressure_unit:
            (self.contact_pressure_value, "pressure", "bottom_contact.pressure"),
            }

    def _extract_current_table_depth_and_pressure_units(self) -> None:
        table_unit = self.parent.tabular_frame.units_table
        self.pressure_unit = table_unit.cellWidget(0, 1).currentText()
        self.depth_unit = table_unit.cellWidget(0, 0).currentText()

    def _on_active_fluid_combo_changed(self) -> None:
        self.active_fluid = self.active_fluid_combo.currentData()
        self.sidebar_summary.active_fluid = self.active_fluid
        self.update_active_fluid_widgets()
        self.project.mark_modified()

    def _on_active_fluid_gradient_changed(self) -> None:
        if self.active_fluid is None:
            return
        mid_depth = (
            self.active_fluid.plotting_depth_min_si
            + self.active_fluid.plotting_depth_max_si
            ) / 2
        mid_pressure = self.active_fluid.gradient_si * (
            mid_depth - self.active_fluid.zero_pressure_depth_si
            )
        
        value = self.active_fluid_gradient_value.value()
        unit = self.active_fluid_gradient_unit.currentText()
        value_si = normalise_from_user_units(unit, "pressure_gradient", value)
        self.active_fluid.gradient_si = value_si
        # Update the zpd to rotate the line about its mid point
        self.active_fluid.update_zpd_on_gradient_change(mid_depth, mid_pressure)
        with QSignalBlocker(self.active_fluid_zpd_value):
            unit = self.active_fluid_zpd_unit.currentText()
            value = self.active_fluid.zero_pressure_depth_si
            zpd = convert_from_normalised_to_user_units(unit, "length", value)
            self.active_fluid_zpd_value.setValue(zpd)
        self.active_fluid.refresh_contacts_for_self()
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _on_active_fluid_max_depth_changed(self) -> None:
        if self.active_fluid is None:
            return
        value = self.active_fluid_max_plotting_depth_value.value()
        unit = self.active_fluid_max_plotting_depth_unit.currentText()
        value_si = normalise_from_user_units(unit, "length", value)
        self.active_fluid.plotting_depth_max_si = value_si
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _on_active_fluid_min_depth_changed(self) -> None:
        if self.active_fluid is None:
            return
        value = self.active_fluid_min_plotting_depth_value.value()
        unit = self.active_fluid_min_plotting_depth_unit.currentText()
        value_si = normalise_from_user_units(unit, "length", value)
        self.active_fluid.plotting_depth_min_si = value_si
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _on_active_fluid_type_combo_changed(self) -> None:
        if self.active_fluid is None:
            return
        fluid_type = self.active_fluid_type_combo.currentText()
        self.active_fluid.type = fluid_type
        self.active_fluid.refresh_contacts_for_self()
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _on_active_fluid_zpd_changed(self) -> None:
        if self.active_fluid is None:
            return
        value = self.active_fluid_zpd_value.value()
        unit = self.active_fluid_zpd_unit.currentText()
        value_si = normalise_from_user_units(unit, "length", value)
        self.active_fluid.zero_pressure_depth_si = value_si
        self.active_fluid.refresh_contacts_for_self()
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _on_bottom_contact_fluid_combo_changed(self) -> None:
        if self.active_fluid is None:
            return
        contact = self.active_fluid.bottom_contact
        contact.bottom_fluid = self.contact_fluid_combo.currentData(Qt.ItemDataRole.UserRole)
        contact.set_contact_data()
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _on_fluid_visibility_tree_item_change(
        self,
        item: QTreeWidgetItem,
        column: int,
        ) -> None:
        tree = self.visible_fluids_tree
        fluid = item.data(0, Qt.ItemDataRole.UserRole)
        if fluid is None:
            return
        analysis = fluid.analysis_object

        # Gate to enter fluid rename
        if column == 0:
            new_name = item.text(0).strip()
            analysis.rename_fluid(fluid, new_name)
            self.signals.fluids_changed.emit()

        # Gate to adjust the fluid visibility selection
        elif column == 1:
            with QSignalBlocker(tree):
                if item.checkState(1) == Qt.CheckState.Checked:
                    item.setCheckState(2, Qt.CheckState.Unchecked)
                else:
                    item.setData(2, Qt.ItemDataRole.CheckStateRole, None)
                    if fluid is not None:
                        fluid.is_editable = False

            # Repopulate the visible fluids list of the analysis view widget
            self.parent.visible_fluids.clear()
            for i in range(tree.topLevelItemCount()):
                top_item = tree.topLevelItem(i)
                if top_item.checkState(1) == Qt.CheckState.Checked:
                    f = top_item.data(0, Qt.ItemDataRole.UserRole)
                    if f is not None:
                        self.parent.visible_fluids.append(f)
            # Inform the rest of the application of the changes
            self.sidebar_summary.visible_fluids = list(self.parent.visible_fluids)
            self._refresh_depth_gradient_plots()

        # Gate to adjust the fluid editability
        elif column == 2:
            if fluid is not None:
                fluid.is_editable = item.checkState(2) == Qt.CheckState.Checked
                # Update the pressure chart to editability of the line
                for line in self.parent.graphical_frame.pressure_chart.all_visible_fluids:
                    if line.fluid is fluid:
                        line.toggle_editable()
            if fluid is self.active_fluid:
                self._toggle_active_fluid_widgets_editability()

        self.project.mark_modified()

    def _on_ref_fluid_combo_changed(self) -> None:
        self.ref_fluid = self.ref_fluid_combo.currentData()
        self.sidebar_summary.ref_fluid = self.ref_fluid
        self.project.mark_modified()
        self.reference_fluid_changed.emit(self.ref_fluid)

    def _on_visible_fluid_context_menu_request(self, position: QPoint) -> None:
        tree = self.visible_fluids_tree
        item = tree.itemAt(position)
        if item is None or item.parent() is not None:
            return

        menu = QMenu(tree)
        fluid = item.data(0, Qt.ItemDataRole.UserRole)

        # Rename, Duplicate, Delete
        self.actionRenameFluid = QAction("Rename")
        menu.addAction(self.actionRenameFluid)
        self.actionRenameFluid.triggered.connect(
            lambda _checked=False, item=item: self._start_rename_fluid(item)
            )
        
        # Duplicate
        self.actionDuplicateFluid = QAction("Duplicate")
        menu.addAction(self.actionDuplicateFluid)
        self.actionDuplicateFluid.triggered.connect(
            lambda _checked=False, fluid=fluid: self.duplicate_fluid(fluid)
            )
        
        # Delete
        self.actionDeleteFluid = QAction("Delete")
        menu.addAction(self.actionDeleteFluid)
        self.actionDeleteFluid.triggered.connect(
            lambda _checked=False, fluid=fluid: self.delete_fluid(fluid)
            )

        menu.exec(tree.viewport().mapToGlobal(position))

    def _populate_active_fluid_contact_combo(self) -> None:
        with QSignalBlocker(self.contact_fluid_combo):
            self.contact_fluid_combo.clear()
            self.contact_fluid_combo.addItem("None", None)
            for fluid in self.analysis.fluids:
                if fluid.name != self.active_fluid_combo.currentText():
                    self.contact_fluid_combo.addItem(fluid.name, fluid)

    def _populate_active_fluid_type_combo(self) -> None:
        with QSignalBlocker(self.active_fluid_type_combo):
            self.active_fluid_type_combo.clear()
            if self.active_fluid is None:
                return
            for fluid_type in STANDARD_FLUIDS.values():
                self.active_fluid_type_combo.addItem(fluid_type.label, fluid_type)
            idx = self.active_fluid_type_combo.findText(self.active_fluid.type)
            if idx >= 0:
                self.active_fluid_type_combo.setCurrentIndex(idx)

    def _populate_all_fluid_combos(self) -> None:
        if len(self.analysis.fluids) == 0:
            return
        combos = [self.ref_fluid_combo, self.active_fluid_combo]

        for combo in combos:
            with QSignalBlocker(combo):
                combo.clear()
                combo.addItem("None", None)
                for fluid in self.analysis.fluids:
                    combo.addItem(fluid.name, fluid)

    def _populate_identifier_combo(self, sender_combo: QComboBox) -> None:
        headers = self.view.df.columns
        options = ["None"] + [
            header for header in headers
            if (
                header != CANONICAL_EXCESS_PRESSURE
                and header != CANONICAL_FORMATION_PRESSURE
                and header != CANONICAL_VERTICAL_DEPTH
                )
            ]
        for option in options:
            sender_combo.addItem(option)

    def _populate_primary_identifier_combo(self) -> None:
        self.primary_identifier_combo.clear()
        headers = self.view.df.columns
        options = ["None"] + [
            header for header in headers
            if (
                header != CANONICAL_EXCESS_PRESSURE
                and header != CANONICAL_FORMATION_PRESSURE
                and header != CANONICAL_VERTICAL_DEPTH
                )
            ]
        for option in options:
            self.primary_identifier_combo.addItem(option)

    def _populate_secondary_identifier_combo(self) -> None:
        self.secondary_identifier_combo.clear()
        headers = self.view.df.columns
        options = ["None"] + [
            header for header in headers
            if (
                header != self.primary_identifier_combo.currentText()
                and header != CANONICAL_EXCESS_PRESSURE
                and header != CANONICAL_FORMATION_PRESSURE
                and header != CANONICAL_VERTICAL_DEPTH
                )
            ]
        for option in options:
            self.secondary_identifier_combo.addItem(option)

    def _populate_widgets_from_persisted_data(self) -> None:
        saved_state = self.sidebar_summary
        # Reference fluid combo, color and series combos
        with QSignalBlocker(self.ref_fluid_combo), \
                QSignalBlocker(self.primary_identifier_combo), \
                QSignalBlocker(self.secondary_identifier_combo), \
                QSignalBlocker(self.active_fluid_combo):

            self.ref_fluid_combo.setCurrentText(
                saved_state.ref_fluid.name if saved_state.ref_fluid is not None else "None"
                )
            self.ref_fluid = self.ref_fluid_combo.currentData(Qt.ItemDataRole.UserRole)

            self.primary_identifier_combo.setCurrentText(saved_state.primary_series_identifier)
            self.secondary_identifier_combo.setCurrentText(saved_state.secondary_series_identifier)

            # Active fluid selection
            active_fluid = saved_state.active_fluid
            if active_fluid is None:
                self.active_fluid_combo.setCurrentText("None")
            else:
                idx = self.active_fluid_combo.findText(active_fluid.name)
                if idx >= 0:
                    self.active_fluid_combo.setCurrentIndex(idx)
                    self.active_fluid = self.active_fluid_combo.currentData()
                else:
                    self.active_fluid_combo.setCurrentText("None")
            self.active_fluid = self.active_fluid_combo.currentData()

        # Active fluid combo
        self.update_active_fluid_widgets()

        # Visible fluid tree
        with QSignalBlocker(self.visible_fluids_tree):
            for i in range(self.visible_fluids_tree.topLevelItemCount()):
                item = self.visible_fluids_tree.topLevelItem(i)
                fluid = item.data(0, Qt.ItemDataRole.UserRole)
                if fluid in saved_state.visible_fluids:
                    item.setCheckState(1, Qt.CheckState.Checked)
                    if fluid.is_editable:
                        item.setCheckState(2, Qt.CheckState.Checked)
                    else:
                        item.setCheckState(2, Qt.CheckState.Unchecked)

    def _refresh_depth_gradient_plots(self) -> None:
        for chart in [
            self.parent.graphical_frame.pressure_chart,
            self.parent.graphical_frame.xs_pressure_chart,
            ]:
            chart.refresh_self()

    def _start_rename_fluid(self, item: QTreeWidgetItem) -> None:
        tree = self.visible_fluids_tree
        fluid = item.data(0, Qt.ItemDataRole.UserRole)

        if fluid is None or not isinstance(fluid, Fluid):
            return

        tree.setCurrentItem(item, 0)  # focus on the row, column 0
        tree.editItem(item, 0)  # same as pressing F2

    def _toggle_active_fluid_widgets_editability(self) -> None:
        editability = (
            self.active_fluid is not None
            and self.active_fluid.is_editable
            )

        for w in (
            self.active_fluid_min_plotting_depth_value,
            self.active_fluid_max_plotting_depth_value,
            self.active_fluid_type_combo,
            self.active_fluid_gradient_value,
            self.active_fluid_zpd_value,
            self.contact_fluid_combo,
            ):
            w.setEnabled(editability)

    def _update_contact_value_widgets(self) -> None:
        contact_fluid = self.contact_fluid_combo.currentData(Qt.ItemDataRole.UserRole)
        if contact_fluid is None:
            self.contact_depth_value.setText("")
            self.contact_pressure_value.setText("")
            self.contact_type_value.setText("")
        else:
            contact = self.active_fluid.bottom_contact
            self.contact_type_value.setText(contact.type or "")

            depth_si = contact.depth
            pressure_si = contact.pressure
            depth_unit = self.contact_depth_unit.currentText()
            pressure_unit = self.contact_pressure_unit.currentText()

            if depth_si is None:
                self.contact_depth_value.setText("")
                self.contact_pressure_value.setText("")
            else:
                depth = convert_from_normalised_to_user_units(depth_unit, "length", depth_si)
                pressure = convert_from_normalised_to_user_units(
                    pressure_unit, "pressure", pressure_si
                    )
                self.contact_depth_value.setText(limit_decimals_str(depth))
                self.contact_pressure_value.setText(limit_decimals_str(pressure))

    def _update_identifier_combo(self, sender_combo: QComboBox) -> None:
        # Update the sender persistence attributre:
        if sender_combo is self.primary_identifier_combo:
            self.sidebar_summary.primary_series_identifier = sender_combo.currentText()
            other_combo = self.secondary_identifier_combo
        else:
            self.sidebar_summary.secondary_series_identifier = sender_combo.currentText()
            other_combo = self.primary_identifier_combo

        # Capture the current value of the other combo
        initial_selection = other_combo.currentText()

        with QSignalBlocker(other_combo):
            # Re-populate the other combo excluding the selection of the sender combo
            other_combo.clear()
            headers = self.view.df.columns
            options = ["None"] + [
                header for header in headers
                if (
                    header != sender_combo.currentText()
                    and header != CANONICAL_EXCESS_PRESSURE
                    and header != CANONICAL_FORMATION_PRESSURE
                    and header != CANONICAL_VERTICAL_DEPTH
                    )
                ]

            for option in options:
                other_combo.addItem(option)

            # Restore the original value if available
            idx = other_combo.findText(initial_selection)
            if idx >= 0:
                other_combo.setCurrentText(initial_selection)

        self.project.mark_modified()

    def _update_single_value_on_units_change(self, combo: QComboBox) -> None:
        combination = self.unit_combo_value_pairs[combo]
        user_unit = combo.currentText()
        widget = combination[0]
        quantity_key = combination[1]
        attribute_name = combination[2]
        if self.active_fluid is None:
            return

        value_si = attrgetter(attribute_name)(self.active_fluid)
        if value_si is None:
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(0.0)
            else:
                widget.setText("")
            return
        else:
            value = convert_from_normalised_to_user_units(user_unit, quantity_key, value_si)
            if isinstance(widget, QDoubleSpinBox):
                result = limit_decimals_float(value)
                assert result is not None,(
                    f"limit_decimals_float returned None for {attribute_name} = {value!r}"
                )
                widget.setDecimals(result.decimals)
                widget.setValue(result.value)
            else: 
                widget.setText(limit_decimals_str(value))

    #--------Public API--------

    def define_scatters_for_plotting(self) -> None:
        # Access the proxy model which filters the view.df with the filterable table active filters
        proxy_model = self.parent.tabular_frame.table.proxy_model
        df = self.parent.extract_visible_df_from_proxy(proxy_model)

        primary_identifier = self.primary_identifier_combo.currentText()
        secondary_identifier = self.secondary_identifier_combo.currentText()

        scatter_item_list = build_scatter_series(
            df,
            primary_identifier,
            secondary_identifier,
            )

        # Pass the list of scatter items to the 2 plots and recreate all scatter_plot_items
        for chart in [
            self.parent.graphical_frame.pressure_chart,
            self.parent.graphical_frame.xs_pressure_chart,
            ]:
            chart.create_all_scatter_plot_items(scatter_item_list)
            chart.refresh_self()

    def delete_fluid(self, fluid: Fluid) -> None:
        if not confirm_delete_fluid(self, self.analysis, fluid):
            return
        self.analysis.delete_fluid(fluid)
        self.project.mark_modified()
        self.signals.fluids_changed.emit()

    def duplicate_fluid(self, fluid: Fluid) -> None:
        new_fluid = self.analysis.duplicate_fluid(fluid,100)
        self.view.sidebar.visible_fluids.append(new_fluid)
        self.project.mark_modified()
        self.signals.fluids_changed.emit()

    def refresh_self(self) -> None:
        self._populate_all_fluid_combos()
        self._create_visible_fluids_tree()
        self._populate_widgets_from_persisted_data()
        self.parent.visible_fluids = list(self.sidebar_summary.visible_fluids) #pass any update on visible fluids (e.g. from "Fluid Deleted") view_widget sidebar

    def update_active_fluid_widgets(self) -> None:
        # Ensure that if a fluid has been selected in the contact combo, it has updated the widgets active fluid
        self.active_fluid = self.active_fluid_combo.currentData(Qt.ItemDataRole.UserRole)
        self._populate_active_fluid_type_combo()

        # Active fluid
        if self.active_fluid is None:
            self.active_fluid_gradient_value.setValue(0.0)
            self.active_fluid_zpd_value.setValue(0.0)
            self.active_fluid_min_plotting_depth_value.setValue(0.0)
            self.active_fluid_max_plotting_depth_value.setValue(0.0)

            with QSignalBlocker(self.contact_fluid_combo):
                self.contact_fluid_combo.setCurrentText("None")
            self.contact_depth_value.setText("")
            self.contact_pressure_value.setText("")
            self.contact_type_value.setText("")
        else:
            #Gradient
            gradient_si = self.active_fluid.gradient_si
            gradient_unit = self.active_fluid_gradient_unit.currentText()
            gradient = convert_from_normalised_to_user_units(
                gradient_unit,
                "pressure_gradient",
                gradient_si,
                )
            result = limit_decimals_float(gradient)
            assert result is not None,(
                f"limit_decimals_float has returned None for active_fluid_gradient = {gradient!r}"
                )
            self.active_fluid_gradient_value.setDecimals(result.decimals)
            self.active_fluid_gradient_value.setValue(result.value)
            #Zero pressure depth
            zpd_si = self.active_fluid.zero_pressure_depth_si
            zpd_unit = self.active_fluid_zpd_unit.currentText()
            zpd = convert_from_normalised_to_user_units(
                zpd_unit,
                "length",
                zpd_si,
                )
            result = limit_decimals_float(zpd)
            assert result is not None,(
                f"limit_decimals_float has returned None for active_fluid_zpd = {zpd!r}"
                )
            self.active_fluid_zpd_value.setDecimals(result.decimals)
            self.active_fluid_zpd_value.setValue(result.value)

            # Plotting depths
            unit = self.active_fluid_min_plotting_depth_unit.currentText()
            value_si = self.active_fluid.plotting_depth_min_si
            value = convert_from_normalised_to_user_units(unit, "length", value_si)
            result = limit_decimals_float(value)
            assert result is not None, (
                f"limit_decimals_float returned None for plotting_depth_min_si = {value!r}"
                )
            self.active_fluid_min_plotting_depth_value.setDecimals(result.decimals)
            self.active_fluid_min_plotting_depth_value.setValue(result.value)
                
            unit = self.active_fluid_max_plotting_depth_unit.currentText()
            value_si = self.active_fluid.plotting_depth_max_si
            value = convert_from_normalised_to_user_units(unit, "length", value_si)
            result = limit_decimals_float(value)
            assert result is not None,(
                f"limit_decimals_float returned None for plotting_depth_max_si = {value!r}"
                )
            self.active_fluid_max_plotting_depth_value.setDecimals(result.decimals)
            self.active_fluid_max_plotting_depth_value.setValue(result.value)

            # Active fluid contact
            self._populate_active_fluid_contact_combo()
            contact_fluid = self.active_fluid.bottom_contact.bottom_fluid
            idx = self.contact_fluid_combo.findData(contact_fluid)
            if idx >= 0:
                with QSignalBlocker(self.contact_fluid_combo):
                    self.contact_fluid_combo.setCurrentIndex(idx)
            self._update_contact_value_widgets()

        # Check if the details of the fluid should be editable
        self._toggle_active_fluid_widgets_editability()
