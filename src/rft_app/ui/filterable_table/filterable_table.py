from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout,QHBoxLayout
from PyQt6.QtCore import QObject


from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.filterable_table.custom_table_view import CustomTableView


class FilterableTable(QFrame):
    def __init__(
            self, 
            parent:QObject,
            project:ProjectDataManager, 
            analysis:AnalysisObject, 
            view:AnalysisView
            )->None:
        super().__init__(parent)
        
        parent=parent
        self.project = project
        self.analysis = analysis
        self.view = view
        self._build_ui()

    #--------Private UI--------
    def _build_ui(self)->None:
        main_frame = QFrame(self)
        main_layout = QVBoxLayout(main_frame)
        widgets_frame = QFrame(main_frame)
        main_layout.addWidget(widgets_frame)
        
        widgets_layout = QHBoxLayout(widgets_frame)
        temp_label = QLabel("This is a placeholder")
        widgets_layout.addWidget(temp_label)
        
        table_frame= QFrame(main_frame)
        main_layout.addWidget(table_frame)
        
        
        table = CustomTableView(self, self.project, self.analysis, self.view)
        table_layout = QVBoxLayout(table_frame)
        table_layout.addWidget(table)
    
    


