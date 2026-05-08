"""
Main window for the RFT Plotter desktop app.

Hand-written replacement for the auto-generated `Ui_MainWindow` in
`main_window.py` (produced by pyuic6). Built as a `QMainWindow` subclass,
with the same public attribute names the rest of the app already consumes
(`mainSplitter`, `actionLoadData`, `analysisTabWidget`, ...), so swapping
this in only needs a one-line import change in `main.py`.

Layout summary:

    main_splitter  (Horizontal)
        ├── project_panel    (left:  project tree + placeholder buttons)
        └── analysis_panel   (right: tabbed analyses)
                  └── analysis_tab
                            ├── graph_pane   (chart on top, aux below)
                            └── table_pane   (data tables side by side)

    Menus:    File  Data  Edit  Analysis  Settings  Help
    Toolbar:  New / Open / Save / Save As / Load Data / Units / About / Contact
"""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QMainWindow, QPushButton, QSizePolicy, QSplitter,
    QStatusBar, QTabWidget, QToolBar, QToolButton, QTreeWidget, QVBoxLayout,
    QWidget,
)


class BobsMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("CyPRES RFT Plotter")
        self.build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Top-level UI orchestrator
    # ------------------------------------------------------------------
    def build_ui(self):
        self._build_central_widget()
        self._build_menubar()
        self._build_toolbar()
        self._build_statusbar()

        # Initial split between project panel (left) and analysis panel (right)
        self.mainSplitter.setSizes([1000, 5000])

        # Default to the populated analysis tab rather than the "+" tab
        self.analysisTabWidget.setCurrentIndex(1)

    # ==================================================================
    # Central widget
    # ==================================================================
    def _build_central_widget(self):
        central = QWidget(self)
        outer_layout = QHBoxLayout(central)

        self.mainSplitter = QSplitter(Qt.Orientation.Horizontal, central)
        outer_layout.addWidget(self.mainSplitter)

        self.mainSplitter.addWidget(self._build_project_panel())
        self.mainSplitter.addWidget(self._build_analysis_panel())

        self.setCentralWidget(central)

    # Left: project panel ---------------------------------------------------
    def _build_project_panel(self) -> QFrame:
        self.projectPanelFrame = QFrame()
        self.projectPanelFrame.setMinimumSize(QSize(220, 0))
        self.projectPanelFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.projectPanelFrame.setFrameShadow(QFrame.Shadow.Raised)

        layout = QVBoxLayout(self.projectPanelFrame)

        self.projectTree = QTreeWidget()
        self.projectTree.headerItem().setText(0, "Project")
        layout.addWidget(self.projectTree)

        # TODO: replace these placeholders with real project-level controls
        self.placeholder_btn = QPushButton("Placeholder Button")
        self.placeholder_tool_btn = QToolButton()
        self.placeholder_tool_btn.setText("Placeholder Tool Button")
        layout.addWidget(self.placeholder_btn)
        layout.addWidget(self.placeholder_tool_btn)

        return self.projectPanelFrame

    # Right: analysis panel (tabs) ------------------------------------------
    def _build_analysis_panel(self) -> QFrame:
        self.analysisPanelFrame = QFrame()
        size_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.analysisPanelFrame.setSizePolicy(size_policy)
        self.analysisPanelFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.analysisPanelFrame.setFrameShadow(QFrame.Shadow.Raised)

        layout = QVBoxLayout(self.analysisPanelFrame)

        self.analysisTabWidget = QTabWidget()
        self.analysisTabWidget.setTabShape(QTabWidget.TabShape.Triangular)
        self.analysisTabWidget.setTabsClosable(True)
        self.analysisTabWidget.setMovable(True)
        layout.addWidget(self.analysisTabWidget)

        # Tab 0: "+" placeholder (will trigger creation of a new analysis tab)
        self.newAnalysisTab = QWidget()
        self.analysisTabWidget.addTab(self.newAnalysisTab, "+")

        # Tab 1: default analysis content
        self.analysisTabWidget.addTab(self._build_analysis_tab(), "Analysis 1")

        return self.analysisPanelFrame

    # Single analysis tab: graph (top) + tables (bottom) --------------------
    def _build_analysis_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.analysisSplitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.analysisSplitter)

        self.analysisSplitter.addWidget(self._build_graph_pane())
        self.analysisSplitter.addWidget(self._build_table_pane())

        return tab

    # Graph pane: chart on top, auxiliary widgets below ---------------------
    def _build_graph_pane(self) -> QFrame:
        self.graphFrame = QFrame()
        self.graphFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.graphFrame.setFrameShadow(QFrame.Shadow.Raised)

        outer = QVBoxLayout(self.graphFrame)
        self.graphSplitter = QSplitter(Qt.Orientation.Vertical)
        outer.addWidget(self.graphSplitter)

        self.chartWidgetFrame = QFrame()
        self.chartWidgetFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.chartWidgetFrame.setFrameShadow(QFrame.Shadow.Raised)

        self.graphWidgetFrame = QFrame()
        self.graphWidgetFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.graphWidgetFrame.setFrameShadow(QFrame.Shadow.Raised)

        self.graphSplitter.addWidget(self.chartWidgetFrame)
        self.graphSplitter.addWidget(self.graphWidgetFrame)

        return self.graphFrame

    # Table pane: data tables side by side ----------------------------------
    def _build_table_pane(self) -> QFrame:
        self.tableFrame = QFrame()
        self.tableFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.tableFrame.setFrameShadow(QFrame.Shadow.Raised)

        outer = QHBoxLayout(self.tableFrame)
        self.tableSplitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(self.tableSplitter)

        self.tableWidgetFrame = QFrame()
        self.tableWidgetFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.tableWidgetFrame.setFrameShadow(QFrame.Shadow.Raised)

        self.tableDataFrame = QFrame()
        self.tableDataFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.tableDataFrame.setFrameShadow(QFrame.Shadow.Raised)

        self.tableSplitter.addWidget(self.tableWidgetFrame)
        self.tableSplitter.addWidget(self.tableDataFrame)

        return self.tableFrame

    # ==================================================================
    # Menubar and actions
    # ==================================================================
    def _build_menubar(self):
        self._build_actions()

        menubar = self.menuBar()

        # File
        self.menu_file = menubar.addMenu("File")
        self.menu_file.addAction(self.actionNewProject)
        self.menu_file.addAction(self.actionOpenProject)
        self.menu_file.addAction(self.actionSaveProject)
        self.menu_file.addAction(self.actionSaveAs)

        # Data
        self.menu_data = menubar.addMenu("Data")
        self.menu_data.addAction(self.actionLoadData)

        # Edit (placeholder, no actions yet)
        self.menu_edit = menubar.addMenu("Edit")

        # Analysis (placeholder, no actions yet)
        self.menu_analysis = menubar.addMenu("Analysis")

        # Settings
        self.menu_settings = menubar.addMenu("Settings")
        self.menu_settings.addAction(self.actionChangeProjecUnits)

        # Help
        self.menu_help = menubar.addMenu("Help")
        self.menu_help.addAction(self.actionAbout)
        self.menu_help.addAction(self.actionContact_Us)

    def _build_actions(self):
        # File actions
        self.actionNewProject = QAction("New Project", self)
        self.actionOpenProject = QAction("Open Project", self)
        self.actionSaveProject = QAction("Save", self)
        self.actionSaveAs = QAction("Save As", self)

        # Data actions
        self.actionLoadData = QAction("Load Data", self)

        # Settings actions (kept original spelling for API compatibility)
        self.actionChangeProjecUnits = QAction("Change Project Units", self)

        # Help actions
        self.actionAbout = QAction("About", self)
        self.actionContact_Us = QAction("Contact Us", self)

        # Prevent macOS from re-homing these items into the app menu
        for action in (
            self.actionNewProject,
            self.actionOpenProject,
            self.actionSaveProject,
            self.actionSaveAs,
            self.actionLoadData,
            self.actionChangeProjecUnits,
            self.actionAbout,
            self.actionContact_Us,
        ):
            action.setMenuRole(QAction.MenuRole.NoRole)

    # ==================================================================
    # Toolbar
    # ==================================================================
    def _build_toolbar(self):
        self.toolBar = QToolBar(self)
        self.toolBar.setIconSize(QSize(32, 32))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolBar.setWindowTitle("toolBar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        for action in (
            self.actionNewProject,
            self.actionOpenProject,
            self.actionSaveProject,
            self.actionSaveAs,
            self.actionLoadData,
            self.actionChangeProjecUnits,
            self.actionAbout,
            self.actionContact_Us,
        ):
            self.toolBar.addAction(action)

    # ==================================================================
    # Status bar
    # ==================================================================
    def _build_statusbar(self):
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

    # ==================================================================
    # Signals
    # ==================================================================
    def _connect_signals(self):
        # Application-level wiring (e.g. actionLoadData -> loadData) lives in
        # main.py, since the handlers are defined on the consumer class.
        pass


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = BobsMainWindow()
    window.showMaximized()
    sys.exit(app.exec())
