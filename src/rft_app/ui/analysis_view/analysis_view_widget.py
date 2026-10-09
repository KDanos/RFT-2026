from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from project.canonical_names import (
    CANONICAL_EXCESS_PRESSURE,
    CANONICAL_FORMATION_PRESSURE,
    CANONICAL_VERTICAL_DEPTH,
)
from project.fluid_model import Fluid
from ui.filterable_table.proxy_model import ProxyFilterModel
from ui.main_window.signal_collection_protocol import SignalCoordinator
from ui.analysis_view.new_fluid_dialog import NewFluidDialog
from ui.filterable_table.filterable_table import FilterableTable
from .analysis_view_data_manager import calculate_excess_pressure_column, refresh_view_object_from_column_tree_selection
from .graphical_frame import GraphicalFrame
from .graphical_sidebar import GraphicalSidebar
from .tabular_sidebar import TabularSidebar
import pandas as pd


class AnalysisViewWidget(QWidget):
    def __init__(
            self,
            parent: QWidget,
            project: ProjectDataManager,
            analysis: AnalysisObject,
            analysis_view_object: AnalysisView,
            signal_coordinator:SignalCoordinator,           
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project: ProjectDataManager = project
        self.analysis: AnalysisObject = analysis
        self.view: AnalysisView = analysis_view_object
        self.signal_coordinator:SignalCoordinator = signal_coordinator

        # Set module variables
        self.new_fluid_dialog: NewFluidDialog | None = None

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        self.tabular_sidebar = TabularSidebar(self, self.project, self.analysis, self.view)

        self._load_filterable_table()
        self.proxy = self.tabular_frame.table.proxy_model

        self.graphical_frame = GraphicalFrame(
            parent=self,
            project=self.project,
            col_specs=self.view.column_specs,
            view=self.view,
            signal_coordinator=self.signal_coordinator
            )

        self.graphical_sidebar = GraphicalSidebar(
            self,
            self.project,
            self.view.column_specs,
            )

        self.graphical_row_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.graphical_row_splitter.addWidget(self.graphical_sidebar)
        self.graphical_row_splitter.addWidget(self.graphical_frame)
        self.graphical_row_splitter.setSizes([1000, 5000])

        self.tabular_row_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tabular_row_splitter.addWidget(self.tabular_sidebar)
        self.tabular_row_splitter.addWidget(self.tabular_frame)
        self.tabular_row_splitter.setSizes([1000, 5000])

        self.main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_frame_splitter.addWidget(self.graphical_row_splitter)
        self.main_frame_splitter.addWidget(self.tabular_row_splitter)
        self.main_frame_splitter.setSizes([5000, 5000])
        self.main_frame_splitter.setStretchFactor(0, 1)
        self.main_frame_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.main_frame_splitter)
        
        # Check if the excess pressure column should be calculated. 
        ref_fluid = self.graphical_sidebar.ref_fluid_combo.currentData()
        print (ref_fluid)
        if ref_fluid is not None:
            self._on_reference_fluid_change(ref_fluid)

        self._pass_df_to_plots()
        #Ensure the series are plotted on load
        self.graphical_sidebar.define_scatters_for_plotting()

    def _connect_signals(self) -> None:
        self.tabular_sidebar.view_df_changed.connect(self._on_view_df_change)
        self.tabular_frame.column_unit_change.connect(self._on_column_unit_change)
        self.proxy.filters_changed.connect(self._pass_df_to_plots)
        self.graphical_sidebar.reference_fluid_changed.connect(self._on_reference_fluid_change)

    def _load_filterable_table(self) -> None:
        selected_columns = self.tabular_sidebar.get_selected_columns_names()
        refresh_view_object_from_column_tree_selection(
            self.view, self.analysis, self.project, selected_columns
        )
        self.tabular_frame = FilterableTable(
            self, self.project, self.view.df, self.view.column_specs
        )
        self.tabular_frame.load_data(
            self.view.df, self.view.column_specs, self.view.column_filters
        )

    def _on_column_unit_change(self, col: int, header: str, unit: str) -> None:
        chart_headers = {
            CANONICAL_VERTICAL_DEPTH,
            CANONICAL_FORMATION_PRESSURE,
            CANONICAL_EXCESS_PRESSURE,
        }
        if header in chart_headers:
            self._pass_df_to_plots()

        self.project.mark_modified()

    def _on_reference_fluid_change(self, reference_fluid:Fluid| None) -> None:
        calculate_excess_pressure_column(self.view.df, reference_fluid)

        # Make the excess pressure chart visible
        show_xs = reference_fluid is not None
        self.graphical_frame.xs_pressure_frame.setVisible(show_xs)
        self.graphical_frame.xs_pressure_chart.setVisible(show_xs)

        #
       

        # Update the table 
        self.tabular_frame.load_data(
                self.view.df, 
                self.view.column_specs, 
                self.view.column_filters
            )
        
        #Ensure that all plots are refreshed (cheating, we only need to refresh the xs-pressure plot)
        self._pass_df_to_plots()
        
        self.graphical_sidebar.define_scatters_for_plotting()
        
        self.project.mark_modified()
    
    def _on_view_df_change(self) -> None:
        
        # Extract the names of the columns selected from the tree
        selected_columns = self.tabular_sidebar.get_selected_columns_names()
        
        # Rebuild the persisted view object (df and column specs)
        refresh_view_object_from_column_tree_selection(
            self.view, self.analysis, self.project, selected_columns
        )
        
        # Recalculate the excess pressure values
        calculate_excess_pressure_column(self.view.df, self.graphical_sidebar.ref_fluid)
        
        # Load the rebuild view into the filterable table
        self.tabular_frame.load_data(
            self.view.df, 
            self.view.column_specs, 
            self.view.column_filters
        )
        
        # Push the changes to the plots
        self._pass_df_to_plots()
        self.project.mark_modified()

    def _pass_df_to_plots(self) -> None:
        df = self.extract_visible_df_from_proxy()
        for plot in [
            self.graphical_frame.pressure_chart, 
            self.graphical_frame.xs_pressure_chart]:
            
            #Pass on the updated df from the proxy model
            plot.df = df
            #Update all items
            plot.refresh_self()
        
    #--------Public API--------

    def on_project_units_changed(self)->None:
        if self.new_fluid_dialog is not None:
            self.new_fluid_dialog.on_project_units_changed()
    
    def extract_visible_df_from_proxy(self, proxy:ProxyFilterModel| None=None) -> pd.DataFrame:
        # Default to avoid finding the proxy when this method is called from other modules
        if proxy is None:
            proxy = self.proxy

        source = proxy.sourceModel()
        rows = [
            proxy.mapToSource(proxy.index(r, 0)).row()
            for r in range(proxy.rowCount())
        ]
        return source.df.iloc[rows]
