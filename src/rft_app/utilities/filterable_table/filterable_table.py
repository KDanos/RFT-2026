from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFrame, QLabel, QTableView, QVBoxLayout

from project import AnalysisObject, AnalysisView, ProjectDataManager


class FilterableTableView(QTableView):
    def __init__(self, 
                parent:QObject,
                project:ProjectDataManager,
                analysis:AnalysisObject,
                view:AnalysisView)->None:
        super().__init__(parent)
        self.parent = parent
        self.project = project
        self.analysis = analysis
        self.view = view

        self.build_ui()

    #--------Private UI--------

    def build_ui(self)->QFrame:
        self.frame = QFrame(self)
        main_layout = QVBoxLayout(self.frame)
        temp_label = QLabel("This is the Filterable Table View")
        main_layout.addWidget(temp_label)

