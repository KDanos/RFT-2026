from PyQt6.QtCore import QEvent, QSignalBlocker, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

import pyqtgraph as pg
import pandas as pd
import numpy as np

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.fluid_model import Fluid
from project.models import AnalysisObject, ViewWidgetSidebar
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from project import persistence
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
        if getattr(self.view, "sidebar", None) is None:
            self.view.sidebar = ViewWidgetSidebar()
        self.sidebar_summary: ViewWidgetSidebar = self.view.sidebar


        self.sidebar_summary:ViewWidgetSidebar = self.view.sidebar

        # Set module variables
        self.ref_fluid: Fluid | None = None
        self.active_fluid: Fluid | None = None
        self.pressure_unit:str = ""
        self.depth_unit:str = ""
        

        # Initialisation methods
        self._extract_current_table_depth_and_pressure_units()
        self._build_ui()
        self._populate_widgets_from_persisted_data()
        self._connect_signals()
        self._refresh_depth_gradient_plots()

    #--------Private UI--------

    def _build_ui(self) -> None:
        
        # Layout arrangement
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addStretch()

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
        self.active_fluid_label = QLabel("Active Fluid")
        self.active_fluid_combo = QComboBox(self)
        self.grid_layout.addWidget(self.active_fluid_label, 3, 0)
        self.grid_layout.addWidget(self.active_fluid_combo, 3, 1)
        self._populate_ref_or_active_fluid_combo()

    def _connect_signals(self) -> None:
        # Reference Fluid
        self.ref_fluid_combo.currentIndexChanged.connect(lambda _idx: self._on_ref_fluid_combo_changed())
        
        # Series Identifier
        for combo in [self.primary_identifier_combo, self.secondary_identifier_combo]:
            combo.currentIndexChanged.connect(lambda _idx, sender = combo: self._update_identifier_combo(sender))
            combo.currentIndexChanged.connect(lambda _idx: self.define_scatters_for_plotting())
  
        # Active Fluid
        self.active_fluid_combo.currentIndexChanged.connect(lambda _idx: self._on_active_fluid_combo_changed())
    
    def _extract_current_table_depth_and_pressure_units(self)->None:
        table_unit = self.parent.tabular_frame.units_table       
        self.pressure_unit =table_unit.cellWidget(0,1).currentText()
        self.depth_unit = table_unit.cellWidget(0,0).currentText()

    def _on_active_fluid_combo_changed(self) -> None:
        self.active_fluid = self.active_fluid_combo.currentData()
        self.sidebar_summary.active_fluid = self.active_fluid
        self.project.mark_modified()

    def _on_ref_fluid_combo_changed(self) -> None:
        self.ref_fluid = self.ref_fluid_combo.currentData()
        self.sidebar_summary.ref_fluid = self.ref_fluid
        self.project.mark_modified()
        self.reference_fluid_changed.emit(self.ref_fluid)

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

    def _populate_ref_or_active_fluid_combo(self) -> None:
        if len(self.analysis.fluids) == 0:
            return
        combos = [self.ref_fluid_combo, self.active_fluid_combo]
        for combo in combos:
            combo.addItem("None", None)
            for fluid in self.analysis.fluids:
                combo.addItem(fluid.name, fluid)

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
            
    def _populate_widgets_from_persisted_data(self)->None:
        saved = self.sidebar_summary
        with QSignalBlocker(self):
            self.ref_fluid_combo.setCurrentText(saved.ref_fluid.name if saved.ref_fluid is not None else "None")
            self.primary_identifier_combo.setCurrentText(saved.primary_series_identifier)
            self.secondary_identifier_combo.setCurrentText(saved.secondary_series_identifier)
            self.active_fluid_combo.setCurrentText(saved.active_fluid.name if saved.active_fluid is not None else "None")

    def _refresh_depth_gradient_plots(self)->None:
        for chart in [
            self.parent.graphical_frame.pressure_chart,
            self.parent.graphical_frame.xs_pressure_chart]:
            chart.refresh_self()
    
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
        
    