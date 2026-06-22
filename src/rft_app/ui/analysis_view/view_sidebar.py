from PyQt6.QtWidgets import QFrame, QPushButton
from qtpy.QtWidgets import QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.widgets import DataframeTree



class ViewSidebar(QFrame):
    def __init__(self,
                parent: QWidget|None = None,
                project: ProjectDataManager|None =None,
                analysis: AnalysisObject|None = None,
                view: AnalysisView|None = None ):
        super().__init__(parent)

        #Pass on the working variables
        self.project = project
        self.analysis = analysis
        self.view = view

        #Build the sidebar
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        btn1 = QPushButton("placeholder 11")
        btn2 = QPushButton("placeholder 12")
        self.main_layout.addWidget(btn1)
        self.main_layout.addWidget(btn2)
        # Build the data tree
        analysis_dataset = self.analysis.analysis_dataset
        self.data_tree = DataframeTree(self,analysis_dataset,"Data")
        self.main_layout.addWidget(self.data_tree)


