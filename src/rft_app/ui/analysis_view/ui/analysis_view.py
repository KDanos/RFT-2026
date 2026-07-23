

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter,  QVBoxLayout, QWidget,QHBoxLayout, QFrame 

from project import AnalysisObject, AnalysisView, ColumnSpec,  ProjectDataManager
from utilities import print_current_location_function
from .view_sidebar import ViewSidebar
from .tabular_frame import TabularFrame
from .graphical_frame import GraphicalFrame
from ..services.analysis_view_data_manager import build_view_df_and_col_specs_from_column_selection, on_column_unit_change, refresh_view_object_from_column_tree_selection



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
        self._connect_signals()
        
    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_vertical_splitter = QSplitter()

        self.sidebar_frame = ViewSidebar(self,self.project, self.analysis, self.view)
        
        main_frame = QFrame(self)
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        main_frame_layout.addWidget(main_frame_splitter)

        self.tabular_frame = TabularFrame(main_frame_splitter,self.project,self.analysis, self.view)
        
        graphical_frame = GraphicalFrame(main_frame_splitter)
        
        main_frame_splitter.addWidget(graphical_frame)
        main_frame_splitter.addWidget(self.tabular_frame)

        main_vertical_splitter.addWidget(self.sidebar_frame)
        main_vertical_splitter.addWidget(main_frame)
        main_vertical_splitter.setSizes([1000,5000])
        main_layout.addWidget(main_vertical_splitter)

    def _connect_signals(self):
        self.sidebar_frame.view_df_changed.connect(self.on_view_df_change)#to be deleted, linked to the old QTableWidget
        # self.sidebar_frame.view_df_changed.connect(self.on_view_df_change)
        self.tabular_frame.column_unit_change.connect(self._on_column_unit_change)

    def _on_column_unit_change(self, col: int, header: str, unit: str) -> None:
        on_column_unit_change(self.view, col, header, unit)
        self.project.mark_modified()

    def on_view_df_change(self):
        print_current_location_function(self)
        selected_columns = self.sidebar_frame.get_selected_columns_names()
        
        refresh_view_object_from_column_tree_selection(self.view, self.analysis, self.project, selected_columns)
        
        self.tabular_frame.update_table()#replace shortly with the new filterable table widget
        self.project.mark_modified()
