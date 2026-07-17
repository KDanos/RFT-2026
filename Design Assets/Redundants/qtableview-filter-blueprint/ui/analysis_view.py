

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter,  QVBoxLayout, QWidget,QHBoxLayout, QFrame 

from project import AnalysisObject, AnalysisView, ColumnSpec,  ProjectDataManager
from .view_sidebar import ViewSidebar
from .tabular_frame import TabularFrame
from .graphical_frame import GraphicalFrame
from ..model.analysis_view_data_manager import (
    apply_column_filter,
    build_view_df_and_col_specs_from_column_selection,
    clear_column_filter,
    on_column_unit_change,
    on_row_filter_change,
    prune_row_filters_for_columns,
)
from ..model.filter_spec import FilterSpec
from ..model.view_display_controller import ViewDisplayController



class AnalysisViewWidget(QWidget):
    def __init__(self,
                 parent:QWidget|None = None,
                 project:ProjectDataManager|None = None,
                 analysis:AnalysisObject|None = None,
                 analysis_view_object:AnalysisView|None = None,
                 )->None:
        super().__init__(parent)

        self.analysis = analysis
        self.view =analysis_view_object
        self.project = project
        
        self._build_ui()
        self._init_display_controller()
        self._connect_signals()
        
    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_vertical_splitter = QSplitter()

        self.sidebar_frame = ViewSidebar(self,self.project, self.analysis, self.view)
        
        main_frame = QFrame(self)
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        main_frame_layout.addWidget(main_frame_splitter)

        self.tabular_frame = TabularFrame(
            main_frame_splitter,
            self.project,
            self.analysis, 
            self.view)
        
        self.graphical_frame = GraphicalFrame(
            main_frame_splitter,
            self.project,
            self.analysis,
            self.view
            )
        
        main_frame_splitter.addWidget(self.graphical_frame)
        main_frame_splitter.addWidget(self.tabular_frame)

        main_vertical_splitter.addWidget(self.sidebar_frame)
        main_vertical_splitter.addWidget(main_frame)
        main_vertical_splitter.setSizes([1000,5000])
        main_layout.addWidget(main_vertical_splitter)

    def _connect_signals(self):
        self.sidebar_frame.view_df_changed.connect(self.on_view_df_change)
        self.tabular_frame.column_unit_change.connect(self._on_column_unit_change)
        self.tabular_frame.row_filter_applied.connect(self._on_row_filter_applied)
        self.tabular_frame.row_filter_cleared.connect(self._on_row_filter_cleared)

    def _init_display_controller(self) -> None:
        self.display_controller = ViewDisplayController(self.project, self)
        self.tabular_frame.bind_display_controller(self.display_controller)
        self.tabular_frame.set_view_data(self.view.df, self.view.column_specs)
        self.tabular_frame.refresh_filter_header()

    def _on_column_unit_change(self, col: int, header: str, unit: str) -> None:
        on_column_unit_change(self.view, col, header, unit)
        self.display_controller.refresh_formatting(self.view.column_specs)
        self.project.mark_modified()

    def _on_row_filter_applied(self, _section: int, filter_spec: FilterSpec) -> None:
        updated = apply_column_filter(self.view, filter_spec)
        on_row_filter_change(self.view, updated)
        self.tabular_frame.refresh_filter_header()
        self.project.mark_modified()

    def _on_row_filter_cleared(self, column_name: str) -> None:
        updated = clear_column_filter(self.view, column_name)
        on_row_filter_change(self.view, updated)
        self.tabular_frame.refresh_filter_header()
        self.project.mark_modified()

    def on_view_df_change(self):
        selected_columns = self.sidebar_frame.get_selected_columns_names()
        
        units_by_name = {s.name:s.unit for s in self.view.column_specs}

        new_df, new_col_specs = build_view_df_and_col_specs_from_column_selection(
            self.analysis.analysis_dataset.dataframe,
            self.analysis.analysis_dataset.column_specs,
            selected_columns,
            self.project,
        )

        merged_specs = [
            ColumnSpec(s.name, s.quantity_key, units_by_name.get(s.name, s.unit))
            for s in new_col_specs
        ]
        self.view.df = new_df
        self.view.column_specs = merged_specs
        active_names = {spec.name for spec in merged_specs}
        on_row_filter_change(
            self.view,
            prune_row_filters_for_columns(self.view, active_names),
        )

        self.tabular_frame.set_view_data(new_df, merged_specs)
        self.project.mark_modified()
