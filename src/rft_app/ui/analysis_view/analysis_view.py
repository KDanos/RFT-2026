

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QTreeWidget, QVBoxLayout, QWidget,QHBoxLayout, QFrame, QPushButton
from qtpy.QtWidgets import QTreeWidgetItem

from project import AnalysisObject, AnalysisView, ProjectDataManager
from .view_sidebar import ViewSidebar
from .tabular_frame import TabularFrame
from .graphical_frame import GraphicalFrame



class AnalysisViewWidget(QWidget):
    def __init__(self,
                 parent:QWidget|None = None,
                 project:ProjectDataManager|None = None,
                 analysis:AnalysisObject|None = None,
                 analysis_view_object:AnalysisView|None = None,
                 )->None:
        super().__init__(parent)

        self.analysis = analysis
        self.analysis_view_obj =analysis_view_object
        self.project = project
        
        #Initialise with empty objects
        self.analysis_data_tree = None
        self._build_ui()
        
    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_vertical_splitter = QSplitter()

        #Widget Frame
        self.widget_frame = ViewSidebar(self,self.project, self.analysis, self.analysis_view_obj)
        
        #Main Frame
        main_frame = QFrame(self)
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        main_frame_layout.addWidget(main_frame_splitter)

        #Tabular Frame
        tabular_frame = TabularFrame(main_frame_splitter)
        
        #Graphical Frame
        graphical_frame = GraphicalFrame(main_frame_splitter)
        
        #Add frames to the main panel layout
        main_frame_splitter.addWidget(graphical_frame)
        main_frame_splitter.addWidget(tabular_frame)

        #Add the frames to main splitter
        main_vertical_splitter.addWidget(self.widget_frame)
        main_vertical_splitter.addWidget(main_frame)
        main_vertical_splitter.setSizes([1000,5000])
        main_layout.addWidget(main_vertical_splitter)

    def _build_data_tree(self):
        df = self.analysis.analysis_dataset.dataframe
        column_specs = self.analysis.analysis_dataset.column_specs
        self.analysis_data_tree = QTreeWidget(self.widget_frame)
        top_level = QTreeWidgetItem(self.analysis.analysis_dataset.name)
        self.analysis_data_tree.addTopLevelItem(top_level)
        for c in df.headers:
            text = c
            column_node = QTreeWidgetItem([text])
            top_level.addChild(column_node)

