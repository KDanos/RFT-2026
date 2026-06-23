from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QFrame, QVBoxLayout,QWidget
from qtpy.QtWidgets import QTabWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.analysis_view import AnalysisViewWidget


class AnalysisWorkspace(QFrame):
    def __init__(self, 
                project:ProjectDataManager|None,
                parent = None) -> None:
        super().__init__(parent)
        self.project = project
        self._current_analysis: AnalysisObject | None = None
        self._current_view: AnalysisView | None = None
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

    def add_analysis_tab(self, 
                        analysis:AnalysisObject,
                        *,
                        select:bool = True)->QTabWidget:
        """Add a new outer (analysis) tab, representin a single AnalysisObject. 
        Return a single inner(view) tab container (QTabWidget)"""
        
        page = QWidget(self.analyses_tabs)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)

        inner_tabs = QTabWidget(page)
        inner_tabs.setTabsClosable(True)
        inner_tabs.setMovable(True)
        
        inner_tabs.tabCloseRequested.connect(
            lambda idx, tabs=inner_tabs, analysis=analysis: 
            self._on_view_tab_close_requested(tabs, analysis, idx))
        
        inner_tabs.currentChanged.connect(
            lambda _idx, analysis = analysis, tabs = inner_tabs:
            self._on_inner_tab_changed(analysis, tabs)
        )
        layout.addWidget(inner_tabs)
        idx = self.analyses_tabs.addTab(page, analysis.name)

        #Remember to which AnalysisObject this outer tab belongs to (for close and visibility handling)
        page.setProperty("analysis_object", analysis)

        if select:
            self.analyses_tabs.setCurrentIndex(idx)
            self._current_analysis = analysis
            self._current_view = None
        
        return inner_tabs
    
    def add_view_tab(self,
                    analysis_tab:QTabWidget,
                    analysis:AnalysisObject,
                    view:AnalysisView,
                    *,
                    select:bool = True
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

        idx = analysis_tab.addTab(widget, view.name)

        #Remember to which ViewObject this inner tab belongs to (for close and visibility handling)
        widget.setProperty("view_object", view)

        if select:
            analysis_tab.setCurrentIndex(idx)
            self._current_analysis = analysis
            self._current_view = view

    def refresh_tabs_from_project(self)->None:
        """Rebuild tabs from project.analyses based on is_visible flag"""
        current_analysis, current_view = self._capture_selection()
        
        self.clear()
        for analysis in self.project.analyses:
            if not analysis.is_visible:
                continue
            inner_tabs = self.add_analysis_tab(analysis,select = False)
            for view in analysis.analysis_views:
                if view.is_visible:
                    self.add_view_tab(inner_tabs, analysis, view, select = False)

        self._restore_selection(current_analysis, current_view)
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
        self.analyses_tabs.tabCloseRequested.connect(self._on_analysis_tab_close_requested)
        self.analyses_tabs.currentChanged.connect(self._on_outer_tab_changed)
    
    def _on_analysis_tab_close_requested(self, index:int)->None:
        page = self.analyses_tabs.widget(index)
        analysis = page.property("analysis_object") if page is not None else None

        if analysis is not None:
            for view in analysis.analysis_views:
                view.is_visible = False
        
        self.analyses_tabs.removeTab(index)
        if page is not None:
            page.deleteLater()

        self.project.mark_modified()

    def _on_view_tab_close_requested(
        self,
        tabs:QTabWidget, 
        analysis:AnalysisObject, 
        idx:int
        )->None:
        
        view_tab= tabs.widget(idx)
        if view_tab is None:
            return
        
        view_object = view_tab.property("view_object")
        if view_object is None:
            view_object = getattr(view_tab, "analysis_view_obj",None)
        if view_object is not None: 
            view_object.is_visible = False
        
        tabs.removeTab(idx)
        view_tab.deleteLater()
        
        # Remove outer tab if no inner tabs are visible
        if tabs.count()==0:
            for i in range(self.analyses_tabs.count()):
                page = self.analyses_tabs.widget(i)
                if page is not None and page.property("analysis_object") is analysis:
                    self._on_analysis_tab_close_requested(i)
                    break
        
        self.project.mark_modified()

    def _capture_selection(self)->tuple[AnalysisObject|None, AnalysisView|None]:
        """Read the currently selected analysis/view before a rebuild"""
        page = self.analyses_tabs.currentWidget()
        if page is None:
            return self._current_analysis, self._current_view

        analysis = page.property("analysis_object")
        inner_tabs = page.findChild(QTabWidget)
        if inner_tabs is None: 
            return analysis, None

        view_widget = inner_tabs.currentWidget()
        view = view_widget.property("view_object") if view_widget else None
        return analysis, view

    def _restore_selection(self, 
                        analysis:AnalysisObject|None, 
                        view: AnalysisView|None, 
                        )->None:
        """Restore the outer/inner tab selection after rebuild."""
        if analysis is None or not analysis.is_visible:
            if self.analyses_tabs.count()>0:
                with QSignalBlocker(self.analyses_tabs):
                    self.analyses_tabs.setCurrentIndex(0)
                self._on_outer_tab_changed(self.analyses_tabs.currentIndex())
            return

        for i in range(self.analyses_tabs.count()):
            page = self.analyses_tabs.widget(i)
            if page is None or page.property("analysis_object") is not analysis:
                continue
                
            with QSignalBlocker(self.analyses_tabs):
                self.analyses_tabs.setCurrentIndex(i)

            inner_tabs = page.findChild(QTabWidget)
            if inner_tabs is None: 
                self._current_analysis = analysis
                self._current_view = None
                return

            if view is not None and view.is_visible:
                for j in range(inner_tabs.count()):
                    widget = inner_tabs.widget(j)
                    if widget is not None and widget.property("view_object") is view:
                        with QSignalBlocker(inner_tabs):
                            inner_tabs.setCurrentIndex(j)
                        self._current_analysis = analysis
                        self._current_view = view
                        return

            if inner_tabs.count()>0:
                with QSignalBlocker(inner_tabs):
                    inner_tabs.setCurrentIndex(0)
                self._current_analysis = analysis
                self._current_view = (
                    inner_tabs.currentWidget().property("view_object")
                    if inner_tabs.currentWidget() is not None
                    else None
                )
                return

    def _on_outer_tab_changed(self, index:int)->None:
        if index<0:
            self._current_analysis = None
            self._current_view = None
            return

        page = self.analyses_tabs.widget(index)
        if page is None:
            return

        analysis = page.property("analysis_object")
        self._current_analysis = analysis

        inner_tabs = page.findChild(QTabWidget)
        if inner_tabs is None: 
            self._current_view = None
            return
        
        widget = inner_tabs.currentWidget()
        self._current_view = widget.property("view_object") if widget else None

    def _on_inner_tab_changed(
        self,
        analysis: AnalysisObject,
        inner_tabs: QTabWidget,
        ) -> None:
        self._current_analysis = analysis
        widget = inner_tabs.currentWidget()
        self._current_view = widget.property("view_object") if widget else None