from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget, QHBoxLayout, QFrame

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.filterable_table import FilterableTable
from .view_sidebar import ViewSidebar
from .graphical_frame import GraphicalFrame
from ..services.analysis_view_data_manager import refresh_view_object_from_column_tree_selection


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
        main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        main_frame_layout.addWidget(main_frame_splitter)

        #Create the Filterable Table
        self._load_filterable_table()

        graphical_frame = GraphicalFrame(main_frame_splitter)

        main_frame_splitter.addWidget(graphical_frame)
        main_frame_splitter.addWidget(self.tabular_frame)

        main_vertical_splitter.addWidget(self.sidebar_frame)
        main_vertical_splitter.addWidget(main_frame)
        main_vertical_splitter.setSizes([1000, 5000])
        main_layout.addWidget(main_vertical_splitter)

    def _connect_signals(self) -> None:
        self.sidebar_frame.view_df_changed.connect(self._on_view_df_change)
        self.tabular_frame.column_unit_change.connect(self._on_column_unit_change)

    def _load_filterable_table(self) -> None:
        selected_columns = self.sidebar_frame.get_selected_columns_names()
        refresh_view_object_from_column_tree_selection(
            self.view, self.analysis, self.project, selected_columns
        )
        self.tabular_frame = FilterableTable(self, self.project, self.analysis, self.view)
        self.tabular_frame.load_from_view()

    def _on_column_unit_change(self, col: int, header: str, unit: str) -> None:
        #FilterableTable already updates view.column_specs itself; just track the edit
        self.project.mark_modified()

    def _on_view_df_change(self) -> None:
        selected_columns = self.sidebar_frame.get_selected_columns_names()
        refresh_view_object_from_column_tree_selection(
            self.view, self.analysis, self.project, selected_columns
        )
        self.tabular_frame.load_from_view()
        self.project.mark_modified()

    #--------Public API--------
