from PyQt6.QtWidgets import QFrame, QVBoxLayout,QWidget
from qtpy.QtWidgets import QTabWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.widgets import AnalysisViewWidget


class AnalysisWorkspace(QFrame):
    def __init__(self, 
                project:ProjectDataManager|None,
                parent = None) -> None:
        super().__init__(parent)
        self.project = project
        self._build_ui()
        self._connect_signals()

    #--------Public API--------
    def set_project (self, project:ProjectDataManager)->None:
        self.project = project
    
    def clear(self)->None:
        """Clear all existing tabs"""
        while self.analyses_tabs.count()>0:
            widget = self.analyses_tabs.widget(0)
            self.analyses_tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()

    def add_analysis_tab(self, analysis:AnalysisObject)->QTabWidget:
        """Add a new outer (analysis) tab, representin a single AnalysisObject. 
        Return a single inner(view) tab container (QTabWidget)"""
        
        page = QWidget(self.analyses_tabs)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)

        inner_tabs = QTabWidget(page)
        layout.addWidget(inner_tabs)

        idx = self.analyses_tabs.addTab(page, analysis.name)
        self.analyses_tabs.setCurrentIndex(idx)

        #Remember to which AnalysisObject this outer tab belongs to (for close and visibility handling)
        page.setProperty("analysis_object", analysis)

        return inner_tabs
    
    def add_view_tab(self,
                    analysis_tab:QTabWidget,
                    analysis:AnalysisObject,
                    view:AnalysisView
                    )->None:
        """Add on AnalysisViewWidget tab"""
        
        view.is_visible = True
        view.analysis_object = analysis

        widget = AnalysisViewWidget(
                    parent = analysis_tab,
                    project=self.project,
                    analysis=analysis,
                    analysis_view_object=view
        )

        idx = analysis_tab.addTab(widget,view.name)
        analysis_tab.setCurrentIndex(idx)

        self.project.mark_modified()

    def refresh_tabs_from_project(self)->None:
        """Rebuild tabs from project.analyses based on is_visible flag"""
        self.clear()
        for analysis in self.project.analyses:
            if not analysis.is_visible:
                continue
            inner_tabs = self.add_analysis_tab(analysis)
            for view in analysis.analysis_views:
                if view.is_visible:
                    self.add_view_tab(inner_tabs, analysis, view)
    #--------Private UI--------
    
    def _build_ui(self)->None:
        layout= QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.analyses_tabs = QTabWidget(self)
        self.analyses_tabs.setTabShape(QTabWidget.TabShape.Triangular)
        self.analyses_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.analyses_tabs.setTabsClosable(True)
        self.analyses_tabs.setMovable(True)

        layout.addWidget(self.analyses_tabs)
 
    def _connect_signals(self)->None:
        self.analyses_tabs.tabCloseRequested.connect(self._on_tab_close_requested)

    def _on_tab_close_requested(self, index:int)->None:
        page = self.analyses_tabs.widget(index)
        analysis = page.property("analysis_object") if page is not None else None

        if analysis is not None:
            for view in analysis.analysis_views:
                view.is_visible = False
        
        self.analyses_tabs.removeTab(index)
        if page is not None:
            page.deleteLater()

        self.project.mark_modified()