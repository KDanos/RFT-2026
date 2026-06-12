from PyQt6.QtCore import QPoint, QSignalBlocker, Qt
from PyQt6.QtWidgets import QTreeWidget, QWidget, QTreeWidgetItem



from project import AnalysisObject, ProjectDataManager
from ui.widgets.tree_analyses_functions import on_all_analyses_tree_context_menu


class AnalysesTree(QTreeWidget):
    def __init__(self,
                parent:QWidget| None = None,
                project:ProjectDataManager=None
                )->QTreeWidget:
        super().__init__(parent)

        self.parent = parent
        self.project = project
        self.setHeaderLabel("Analyses")
        self._connect_signals()
        
    def _connect_signals(self)->None:
        self.customContextMenuRequested.connect(
            lambda position: on_all_analyses_tree_context_menu(self, position))
    
    def _build_tree(self)->None:

        # Create the drop down menu option son right click of the menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        for analysis in self.project.analyses:
            #Add the top level item
            top_level = QTreeWidgetItem([analysis.name])
            top_level.setExpanded(True)
            self.addTopLevelItem(top_level)

            # Add the second level items
            #Source Data
            source_node = QTreeWidgetItem(["Source Datasets:"])
            top_level.addChild(source_node)
            for name in analysis.source_datasets:
                source_node.addChild (QTreeWidgetItem([name]))

            #Depth reference 
            text = f"Depth Column: {analysis.vert_depth_src_col}"
            top_level.addChild(QTreeWidgetItem([text]))
            
            # Pressure reference
            text = f"Pressure Column: {analysis.formation_pres_src_col}"
            top_level.addChild(QTreeWidgetItem([text]))

            #Displayed dataframe
            #hold, not sure what this represents yet
            
            #Analysis frame
            view_node = QTreeWidgetItem(["Analysis Views:"])
            top_level.addChild(view_node)
            for view in analysis.analysis_views:
                view_node.addChild(QTreeWidgetItem([view.name]))

    def reload_from_project(self)->None:
        with QSignalBlocker(self):
            self.clear()
            self._build_tree()