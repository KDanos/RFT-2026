from PyQt6.QtWidgets import QFrame
from qtpy.QtWidgets import QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager


class GraphicalFrame(QFrame):
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

        #Build the sidebar
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self):
        pass