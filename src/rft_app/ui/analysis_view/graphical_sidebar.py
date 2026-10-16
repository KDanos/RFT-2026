from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QSizePolicy, QSpacerItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.fluid_model import Fluid
from project.models import AnalysisObject, ViewWidgetSidebar
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from utilities.global_functions import limit_decimals
from units import convert_from_normalised_to_user_units
from units.units_combo_box import UnitsComboBox
from utilities import print_current_location_function
from ui.analysis_view.analysis_view_data_manager import build_scatter_series
from units.units_normalisation import convert_array_to_user_units


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.analysis_view import AnalysisViewWidget


class GraphicalSidebar(QFrame):
    reference_fluid_changed = pyqtSignal(object) #object instead of Fluid | None

    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager,
            col_specs: list[ColumnSpec],
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.parent:AnalysisViewWidget = parent
        self.project: ProjectDataManager = project
        self.col_specs: list[ColumnSpec] = col_specs
        self.analysis: AnalysisObject = self.parent.analysis
        self.view: AnalysisView = self.parent.view
        self.sidebar_summary: ViewWidgetSidebar = self.view.sidebar

        # Set module variables
        self.ref_fluid: Fluid | None = None
        self.active_fluid: Fluid | None = None
        self.pressure_unit:str = ""
        self.depth_unit:str = ""

        # Initialisation methods
        self._extract_current_table_depth_and_pressure_units()
        self._build_ui()
        self._populate_all_fluid_combos()
        self._populate_visible_fluids_tree()
        self._populate_widgets_from_persisted_data()
        self._connect_signals()
        self._refresh_depth_gradient_plots()

    #--------Private UI--------

    def _build_ui(self) -> None:
        # Scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True) # required, otherwise the scroll_area takes only a small space and does not expand to fill the layout
        self.scroll_area.setStyleSheet("QScrollArea { border: None }") # remove the visible border
        self.scroll_area_layout = QVBoxLayout()
        self.scroll_area_layout.setContentsMargins(0,0,0,0)
        self.scroll_area_layout.addWidget(self.scroll_area)
        
        # Set the main Layout 
        self.setLayout(self.scroll_area_layout)

        # Main Container-effectively self, if no scroll area was required
        self.main_container = QFrame (self)
        self.scroll_area.setWidget(self.main_container)
        self.main_container.setAutoFillBackground(False) # required to avoid the main_container setting its background to grey
        self.main_container.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
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
        self.grid_layout.addWidget(self.primary_identifier_label, 1,0)
        self.grid_layout.addWidget(self.primary_identifier_combo, 1,1)
        self.grid_layout.addWidget(self.secondary_identifier_label, 2,0)
        self.grid_layout.addWidget(self.secondary_identifier_combo, 2,1)
        self._populate_identifier_combo(self.primary_identifier_combo)
        self._populate_identifier_combo(self.secondary_identifier_combo)

        # Active Fluid Selection
        self.grid_layout.setRowMinimumHeight(3,20)
        self.active_fluid_h_layout = QHBoxLayout()
        self.grid_layout.addLayout(self.active_fluid_h_layout,4,0,1,2)
        self.active_fluid_grid = QGridLayout()
        self.active_fluid_h_layout.addLayout(self.active_fluid_grid)
        self.active_fluid_h_layout.addStretch()
        self.active_fluid_label = QLabel("Active Fluid")
        self.active_fluid_combo = QComboBox(self)
        self.active_fluid_grid.addWidget(self.active_fluid_label, 0, 0)
        self.active_fluid_grid.addWidget(self.active_fluid_combo, 0, 1)
        
        # Active Fluid Plotting depth
        self.active_fluid_plotting_depth_label = QLabel("Plotting Depth: ")
        self.active_fluid_grid.addWidget(self.active_fluid_plotting_depth_label, 1,0)
        # Min
        self.active_fluid_min_plotting_depth_label = QLabel("Min:")
        self.active_fluid_min_plotting_depth_value = QLineEdit(self)
        self.active_fluid_min_plotting_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_min_plotting_depth_unit = UnitsComboBox("length", self.project)
        self.active_fluid_grid.addWidget(self.active_fluid_min_plotting_depth_label, 2,0)
        self.active_fluid_grid.addWidget(self.active_fluid_min_plotting_depth_value, 2,1)
        self.active_fluid_grid.addWidget(self.active_fluid_min_plotting_depth_unit, 2,2)
        # Max
        self.active_fluid_max_plotting_depth_label = QLabel("Max:")
        self.active_fluid_max_plotting_depth_value = QLineEdit(self)
        self.active_fluid_max_plotting_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_max_plotting_depth_unit = UnitsComboBox("length", self.project)
        self.active_fluid_grid.addWidget(self.active_fluid_max_plotting_depth_label, 3,0)
        self.active_fluid_grid.addWidget(self.active_fluid_max_plotting_depth_value, 3,1)
        self.active_fluid_grid.addWidget(self.active_fluid_max_plotting_depth_unit, 3,2)

        # Active Fluid Details
        self.active_fluid_definition_label = QLabel("Definition:")
        self.active_fluid_grid.addWidget(self.active_fluid_definition_label, 4,0)
        # Gradient
        self.active_fluid_gradient_label = QLabel("Gradient: ")
        self.active_fluid_gradient_value = QLineEdit(self)
        self.active_fluid_gradient_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_gradient_unit = UnitsComboBox("pressure_gradient", self.project)
        self.active_fluid_grid.addWidget(self.active_fluid_gradient_label, 5,0)
        self.active_fluid_grid.addWidget(self.active_fluid_gradient_value, 5,1)
        self.active_fluid_grid.addWidget(self.active_fluid_gradient_unit,5,2)
        # Zero Pressure Depth
        self.active_fluid_zero_pressure_depth_label = QLabel("Zero Pressure Depth: ")
        self.active_fluid_zero_pressure_depth_value = QLineEdit(self)
        self.active_fluid_zero_pressure_depth_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_fluid_zero_pressure_depth_unit = UnitsComboBox("length", self.project)
        self.active_fluid_grid.addWidget(self.active_fluid_zero_pressure_depth_label, 6,0,1,2)
        self.active_fluid_grid.addWidget(self.active_fluid_zero_pressure_depth_value, 6,1)
        self.active_fluid_grid.addWidget(self.active_fluid_zero_pressure_depth_unit,6,2)
        # Underlying Fluid:
        self.active_fluid_contact_label = QLabel("Underlying Contact:")
        self.active_fluid_contact_combo = QComboBox()
        self.active_fluid_grid.addWidget(self.active_fluid_contact_label,7,0)
        self.active_fluid_grid.addWidget(self.active_fluid_contact_combo,7,1)

        # Visible Fluids
        self.grid_layout.setRowMinimumHeight(5,20)
        self.visible_fluids_label = QLabel("Select Fluids to View")
        self.grid_layout.addWidget(self.visible_fluids_label, 6,0,1,2)
        self.visible_fluids_tree=QTreeWidget(self)
        self.grid_layout.addWidget(self.visible_fluids_tree,7,0,1,3)

        # Create empty space below the Visible Tree Widget
        self.grid_layout.setRowMinimumHeight(8,100)

    def _connect_signals(self) -> None:
        # Reference Fluid
        self.ref_fluid_combo.currentIndexChanged.connect(lambda _idx: self._on_ref_fluid_combo_changed())
        
        # Series Identifier
        for combo in [self.primary_identifier_combo, self.secondary_identifier_combo]:
            combo.currentIndexChanged.connect(lambda _idx, sender = combo: self._update_identifier_combo(sender))
            combo.currentIndexChanged.connect(lambda _idx: self.define_scatters_for_plotting())
  
        # Active Fluid
        self.active_fluid_combo.currentIndexChanged.connect(lambda _idx: self._on_active_fluid_combo_changed())

        # Visible fluids
        self.visible_fluids_tree.itemChanged.connect(self._on_visible_fluids_changed)

    def _extract_current_table_depth_and_pressure_units(self)->None:
        table_unit = self.parent.tabular_frame.units_table       
        self.pressure_unit =table_unit.cellWidget(0,1).currentText()
        self.depth_unit = table_unit.cellWidget(0,0).currentText()

    def _on_active_fluid_combo_changed(self) -> None:
        self.active_fluid = self.active_fluid_combo.currentData()
        self.sidebar_summary.active_fluid = self.active_fluid
        self._update_active_fluid_widgets()
        self.project.mark_modified()

    def _on_ref_fluid_combo_changed(self) -> None:
        self.ref_fluid = self.ref_fluid_combo.currentData()
        self.sidebar_summary.ref_fluid = self.ref_fluid
        self.project.mark_modified()
        self.reference_fluid_changed.emit(self.ref_fluid)

    def _on_visible_fluids_changed(self, item:QTreeWidgetItem, column:int)-> None:
        tree = self.visible_fluids_tree
        self.parent.visible_fluids.clear()
       
        for i in range(tree.topLevelItemCount()):
            top_item = tree.topLevelItem(i)
            if top_item.checkState(0)==Qt.CheckState.Checked:
                fluid = top_item.data(0,Qt.ItemDataRole.UserRole)
                if fluid is not None:
                    self.parent.visible_fluids.append(fluid)


        self.sidebar_summary.visible_fluids = list(self.parent.visible_fluids)

        # to do: Notify the graph to plot the visible fluids

        self.project.mark_modified()

    def _populate_all_fluid_combos(self) -> None:
        if len(self.analysis.fluids) == 0:
            print("There are no fluids in the analysis")
            return
        combos = [self.ref_fluid_combo, self.active_fluid_combo]
        for combo in combos:
            combo.clear()
            combo.addItem("None", None)
            for fluid in self.analysis.fluids:
                    combo.addItem(fluid.name, fluid)

    def _populate_active_fluid_contact_combo(self)->None:
        self.active_fluid_contact_combo.clear()
        self.active_fluid_contact_combo.addItem("None", None)
        for fluid in self.analysis.fluids: 
            if fluid.name != self.active_fluid_combo.currentText():
               self.active_fluid_contact_combo.addItem(fluid.name, fluid)
            
    def _populate_identifier_combo(self, sender_combo:QComboBox)->None:     
                
        headers = self.view.df.columns
        options = ["None"] + [
            header for header in headers 
            if  (header != CANONICAL_EXCESS_PRESSURE
                and header != CANONICAL_FORMATION_PRESSURE
                and header != CANONICAL_VERTICAL_DEPTH 
            )
        ]
        for option in options:
            sender_combo.addItem(option)

    def _populate_primary_identifier_combo(self)->None:
        self.primary_identifier_combo.clear()
        headers = self.view.df.columns
        options = ["None"] + [header for header in headers 
            if  (
            header != CANONICAL_EXCESS_PRESSURE
            and header != CANONICAL_FORMATION_PRESSURE
            and header != CANONICAL_VERTICAL_DEPTH
            )
            ]
        for option in options: 
            self.primary_identifier_combo.addItem(option)

    def _populate_secondary_identifier_combo (self)->None:
        self.secondary_identifier_combo.clear()
        headers = self.view.df.columns
        options = ["None"] + [header for header in headers
            if (
                header !=self.primary_identifier_combo.currentText()
                and header != CANONICAL_EXCESS_PRESSURE
                and header != CANONICAL_FORMATION_PRESSURE
                and header != CANONICAL_VERTICAL_DEPTH
            )]
        for option in options: 
            self.secondary_identifier_combo.addItem(option)

    def _populate_visible_fluids_tree(self)->None:
        tree = self.visible_fluids_tree
        tree.clear()
        tree.setHeaderHidden(True)
        tree.setIndentation(0)

        tree.clear()
        for fluid in self.analysis.fluids:
            fluid_item = QTreeWidgetItem([fluid.name])
            fluid_item.setData(0,Qt.ItemDataRole.UserRole, fluid)
            fluid_item.setCheckState(0, Qt.CheckState.Unchecked)
            tree.addTopLevelItem(fluid_item)
        
        height = (
            tree.frameWidth() * 2
            + tree.header().height()
            + sum(tree.sizeHintForRow(i) for i in range(tree.topLevelItemCount()))
            )
        tree.setMinimumHeight(height)
        tree.setFrameShape(QFrame.Shape.NoFrame)
        tree.header().setFrameShape(QFrame.Shape.NoFrame)

    def _populate_widgets_from_persisted_data(self)->None:
        saved_state = self.sidebar_summary
        # Reference fluid combo, color and series combos
        with QSignalBlocker(self):
            self.ref_fluid_combo.setCurrentText(saved_state.ref_fluid.name if saved_state.ref_fluid is not None else "None")
            self.ref_fluid = self.ref_fluid_combo.currentData(Qt.ItemDataRole.UserRole)
            
            self.primary_identifier_combo.setCurrentText(saved_state.primary_series_identifier)
            self.secondary_identifier_combo.setCurrentText(saved_state.secondary_series_identifier)
            
            # Active fluid selection
            active_fluid = saved_state.active_fluid
            if active_fluid is not None:
                idx = self.active_fluid_combo.findText(active_fluid.name)
                if idx >= 0:
                    self.active_fluid_combo.setCurrentIndex(idx)
                    self.active_fluid = self.active_fluid_combo.currentData()

        # Active fluid combo
        self._update_active_fluid_widgets()
        # self.active_fluid_combo.setCurrentText(saved_state.active_fluid.name if saved_state.active_fluid is not None else "None")
        # self._update_active_fluid_widgets()
        # self._populate_active_fluid_contact_combo()


        # Visible fluid tree
        saved_visible = list([fluid.name for fluid in saved_state.visible_fluids])
        with QSignalBlocker(self.visible_fluids_tree):
            for i in range(self.visible_fluids_tree.topLevelItemCount()):
                fluid = self.visible_fluids_tree.topLevelItem(i).text(0)
                if fluid in saved_visible:
                    self.visible_fluids_tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Checked)
                             

            # self.active_fluid_combo.setCurrentText(saved.active_fluid.name if saved.active_fluid is not None else "None")

    def _refresh_depth_gradient_plots(self)->None:
        for chart in [
            self.parent.graphical_frame.pressure_chart,
            self.parent.graphical_frame.xs_pressure_chart]:
            chart.refresh_self()

    def _update_identifier_combo(self,sender_combo:QComboBox)->None:        
        #Update the sender persistence attributre: 
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
            options = ["None"] + [header for header in headers 
                    if (
                        header != sender_combo.currentText()
                        and header != CANONICAL_EXCESS_PRESSURE
                        and header != CANONICAL_FORMATION_PRESSURE
                        and header != CANONICAL_VERTICAL_DEPTH
                    ) ]

            for option in options:
                other_combo.addItem(option)
            
            # Restore the original value if available
            idx = other_combo.findText(initial_selection)
            if idx>=0:
                other_combo.setCurrentText(initial_selection)
            
        self.project.mark_modified()

    def _update_active_fluid_widgets(self)-> None:
        
        # Ensure that if a fluid has been selected in the contact combo, it has updated the widgets active fluid
        self.active_fluid = self.active_fluid_combo.currentData(Qt.ItemDataRole.UserRole)
        
        # Active fluid
        if self.active_fluid is None:
            self.active_fluid_gradient_value.setText("")
            self.active_fluid_zero_pressure_depth_value.setText("")
            self.active_fluid_min_plotting_depth_value.setText("")
            self.active_fluid_max_plotting_depth_value.setText("")
            self.active_fluid_contact_combo.setCurrentText("None")
        else: 
            gradient_si = self.active_fluid.gradient_si
            gradient_unit = self.active_fluid_gradient_unit.currentText()
            gradient = convert_from_normalised_to_user_units(
                gradient_unit, 
                "pressure_gradient",
                gradient_si
            )
            self.active_fluid_gradient_value.setText(limit_decimals(gradient))

            zero_pressure_depth_si = self.active_fluid.zero_pressure_depth_si
            zero_pressure_depth_unit = self.active_fluid_zero_pressure_depth_unit.currentText()
            zero_pressure_depth = convert_from_normalised_to_user_units(
                zero_pressure_depth_unit, 
                "length",
                zero_pressure_depth_si
            )
            self.active_fluid_zero_pressure_depth_value.setText(limit_decimals(zero_pressure_depth))
        
            # Plotting depths
            unit = self.active_fluid_min_plotting_depth_unit.currentText()
            value_si = self.active_fluid.plotting_depth_min_si
            value = convert_from_normalised_to_user_units(unit, "length", value_si)
            self.active_fluid_min_plotting_depth_value.setText(limit_decimals(value))

            unit = self.active_fluid_max_plotting_depth_unit.currentText()
            value_si = self.active_fluid.plotting_depth_max_si
            value = convert_from_normalised_to_user_units(unit, "length", value_si)
            self.active_fluid_max_plotting_depth_value.setText(limit_decimals(value))
            
            # Active fluid contact
            self._populate_active_fluid_contact_combo()       
            contact_fluid = self.active_fluid.bottom_contact.bottom_fluid
            idx = self.active_fluid_contact_combo.findData(contact_fluid)
            if idx>=0:
                self.active_fluid_contact_combo.setCurrentIndex(idx)


    #--------Public API--------

    def define_scatters_for_plotting(self)->None:
        
        #Access the proxy model which filters the view.df with the filterable table active filters
        proxy_model = self.parent.tabular_frame.table.proxy_model
        df = self.parent.extract_visible_df_from_proxy(proxy_model)

        primary_identifier = self.primary_identifier_combo.currentText()
        secondary_identifier = self.secondary_identifier_combo.currentText()

        scatter_item_list = build_scatter_series(
            df,
            primary_identifier, 
            secondary_identifier
        )

        # Pass the list of scatter items to the 2 plots and recreate all scatter_plot_items
        for chart in [
            self.parent.graphical_frame.pressure_chart,
            self.parent.graphical_frame.xs_pressure_chart
            ]:
            chart.create_all_scatter_plot_items(scatter_item_list)
            chart.refresh_self()

    def refresh_self(self)->None:
        self._populate_all_fluid_combos()
        self._populate_active_fluid_contact_combo()
        self._populate_visible_fluids_tree()

        
        self._update_active_fluid_widgets()