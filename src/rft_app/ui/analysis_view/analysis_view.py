
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget, QHBoxLayout, QFrame

from project import AnalysisObject, AnalysisView, ProjectDataManager
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from ui.filterable_table.filterable_table import FilterableTable
from .view_sidebar import ViewSidebar
from .graphical_frame import GraphicalFrame
from .analysis_view_data_manager import refresh_view_object_from_column_tree_selection
import pandas as pd

class AnalysisViewWidget(QWidget):
    def __init__(
            self,
            parent: QWidget | None = None,
            project: ProjectDataManager | None = None,
            analysis: AnalysisObject | None = None,
            analysis_view_object: AnalysisView | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project
        self.analysis = analysis
        self.view = analysis_view_object

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_vertical_splitter = QSplitter()

        self.sidebar_frame = ViewSidebar(self, self.project, self.analysis, self.view)

        main_frame = QFrame(self)
        main_frame_layout = QVBoxLayout(main_frame)
        self.main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        main_frame_layout.addWidget(self.main_frame_splitter)

        # Create the Filterable Table
        self._load_filterable_table()
        # Extract the proxy model from created via the function above
        self.proxy = self.tabular_frame.table.proxy_model

        # Create the graphs
        self.graphical_frame = GraphicalFrame(
            parent = self.main_frame_splitter, 
            col_specs = self.view.column_specs
            )

        self.main_frame_splitter.addWidget(self.graphical_frame)
        self.main_frame_splitter.addWidget(self.tabular_frame)
        self.main_frame_splitter.setSizes([5000, 5000])
        self.main_frame_splitter.setStretchFactor(0, 1)
        self.main_frame_splitter.setStretchFactor(1, 1)

        main_vertical_splitter.addWidget(self.sidebar_frame)
        main_vertical_splitter.addWidget(main_frame)
        main_vertical_splitter.setSizes([1000, 5000])
        main_layout.addWidget(main_vertical_splitter)

        self._refresh_plots()

    def _connect_signals(self) -> None:
        self.sidebar_frame.view_df_changed.connect(self._on_view_df_change)
        self.tabular_frame.column_unit_change.connect(self._on_column_unit_change)
        self.proxy.filters_changed.connect(self._refresh_plots)
    
    def _load_filterable_table(self) -> None:
        selected_columns = self.sidebar_frame.get_selected_columns_names()
        refresh_view_object_from_column_tree_selection(
            self.view, self.analysis, self.project, selected_columns
        )
        self.tabular_frame = FilterableTable(self, self.project, self.view.df, self.view.column_specs)
        
        self.tabular_frame.load_data(self.view.df, self.view.column_specs, self.view.column_filters)
    
    def _on_column_unit_change(self, col: int, header: str, unit: str) -> None:
        # FilterableTable already updates view.column_specs itself; just track the edit
        
        # Gate to ensure that the charts are not re-plot when not necessary
        chart_headers = {
            CANONICAL_VERTICAL_DEPTH,
            CANONICAL_FORMATION_PRESSURE,
            CANONICAL_EXCESS_PRESSURE
        }
        if header in chart_headers:
            self._refresh_plots()
        
        self.project.mark_modified()

    def _on_view_df_change(self) -> None:
        selected_columns = self.sidebar_frame.get_selected_columns_names()
        refresh_view_object_from_column_tree_selection(
            self.view, self.analysis, self.project, selected_columns
        )
        self.tabular_frame.load_data(self.view.df, self.view.column_specs, self.view.column_filters)
        self._refresh_plots()

        self.project.mark_modified()

    def _refresh_plots(self)->None:
        df = self.visible_df_from_proxy(self.tabular_frame.table.proxy_model)
        self.graphical_frame.pressure_chart.set_data(df)

    #--------Public API--------
    def visible_df_from_proxy(self,proxy)->pd.DataFrame:
        source = proxy.sourceModel()
        rows = [
            proxy.mapToSource(proxy.index(r,0)).row()
        for r in range(proxy.rowCount())
        ]
        return source.df.iloc[rows]
