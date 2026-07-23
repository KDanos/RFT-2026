from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout,QHBoxLayout
from PyQt6.QtCore import QObject


from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities import print_current_location_function
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        #Create the widgets frame on top
        widgets_frame = QFrame(self)
        main_layout.addWidget(widgets_frame)
        
        widgets_layout = QHBoxLayout(widgets_frame)
        temp_label = QLabel("This is a placeholder")
        widgets_layout.addWidget(temp_label)
        
        #Create the table frame at the bottom
        table_frame= QFrame(self)
        main_layout.addWidget(table_frame)
        
        
        self.table = CustomTableView(self, self.project, self.analysis, self.view)
        table_layout = QVBoxLayout(table_frame)
        table_layout.addWidget(self.table)
    
    def update_filterable_table(self):
        pass
        
        self._create_table()
    #--------Private UI--------
    def load_from_view(self)->None:
        print_current_location_function(self)
        self.table.load_from_view()


