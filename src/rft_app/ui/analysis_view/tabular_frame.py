from PyQt6.QtWidgets import QFrame, QTableWidget, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities import create_table_view_frame
class TabularFrame(QFrame):
    def __init__(self,
                parent:QWidget|None = None,
                project:ProjectDataManager|None= None,
                analysis: AnalysisObject|None = None, 
                view:AnalysisView|None= None,
                )->None:
        super().__init__(parent)
        
        #Pass on the working variables
        self.project = project
        self.analysis = analysis

        self.view = view
        if analysis:
            self.dataset= analysis.analysis_dataset

        #Build the sidebar
        self._build_ui()
    #--------Public API--------
    def update_column_spec(self):
        for col in range(self.table.columnCount()):
            combo_widget = self.table.getWidget


    #--------Private UI--------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.table_frame= create_table_view_frame(
                                            self.view.df,
                                            self.dataset.column_specs, 
                                            self, 
                                            self.project )
        main_layout.addWidget(self.table_frame)
        self.table = self.table_frame.table
        