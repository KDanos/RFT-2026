

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QSpacerItem, QSplitter, QToolBar, QTreeWidget, QVBoxLayout, QWidget

from ui.widgets.data_loader import DataLoaderDialog
from ui.icons import app_icon, load_qss

import units.units_manager as um




class MainWindowKD(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("CyPRES RFT Plotter")
        self.action_list = []
        self.build_ui()


    def build_ui(self):
        self._build_actions()
        self._build_central_widget()
        # self._build_menubar()
        # self._build_statusbar()
        self._connect_signals()

    def _build_central_widget(self):
        central_widget = QWidget(self)
        hbox = QHBoxLayout(central_widget)
        self.mainSplitter = QSplitter()
        
        #Toolbar
        self._build_toolbar()

        #Analysis Tabs
        self.analysis_frame = QFrame(self)
        #Status Bar
        
        #Manage the main splitter
        self.mainSplitter.addWidget(self._build_project_controls_frame())
        self.mainSplitter.addWidget(self.analysis_frame)
        hbox.addWidget(self.mainSplitter)
        self.mainSplitter.setSizes([1000,5000])
        self.setCentralWidget(central_widget)

    def _build_menubar(self):
        menubar = self.menuBar()
        
                # File
        self.menu_file = menubar.addMenu("File")
        # self.menu_file.addAction(self.actionNewProject)
        # self.menu_file.addAction(self.actionOpenProject)
        # self.menu_file.addAction(self.actionSaveProject)
        # self.menu_file.addAction(self.actionSaveAs)

        # Data
        self.menu_data = menubar.addMenu("Data")
        # self.menu_data.addAction(self.actionLoadData)

        # Edit (placeholder, no actions yet)
        self.menu_edit = menubar.addMenu("Edit")

        # Analysis (placeholder, no actions yet)
        self.menu_analysis = menubar.addMenu("Analysis")

        # Settings
        self.menu_settings = menubar.addMenu("Settings")
        # self.menu_settings.addAction(self.actionChangeProjecUnits)

        # Help
        self.menu_help = menubar.addMenu("Help")
        # self.menu_help.addAction(self.actionAbout)
        # self.menu_help.addAction(self.actionContact_Us)
    
    def _build_toolbar(self):
        self.toolBar= QToolBar(self)
        self.toolBar.setIconSize(QSize(32,32))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolBar.setWindowTitle("ToolBar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea,self.toolBar)
        
        #Add the stylesheet
        self.toolBar.setStyleSheet(load_qss("toolbar.qss"))

        #Add actions (and hence buttons) to the toolbar
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
    
        units_frame = QFrame()
        units_layout = QVBoxLayout()
        units_frame.setLayout(units_layout)
        units_label = QLabel("Project Units")
        self.units_combo = QComboBox(self)
        self.units_combo.addItems(u.label for u in um.BUILT_IN_UNIT_SYSTEMS)
        units_layout.addWidget(units_label)
        units_layout.addWidget(self.units_combo)
        
        #Create empty space between the buttons and the units drop down
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolBar.addWidget(spacer)
        self.toolBar.addWidget(units_frame)
    
    def _build_actions(self):
        # File actions
        self.actionNewProject = QAction("New Project", self)
        self.actionOpenProject = QAction("Open Project", self)
        self.actionSaveProject = QAction("Save", self)
        self.actionSaveAs = QAction("Save As", self)

        # Data actions
        self.actionLoadData = QAction("Load Data", self)
        self.actionLoadData.setIcon (app_icon("ph.upload-simple-fill"))

        # Settings actions (kept original spelling for API compatibility)
        self.actionChangeProjecUnits = QAction("Change Project Units", self)

        # Help actions
        self.actionAbout = QAction("About", self)
        self.actionContact_Us = QAction("Contact Us", self)
    
    def _build_statusbar(self):
        pass

    def _build_project_controls_frame(self)->QFrame:
        my_frame=QFrame()
        vbox = QVBoxLayout()
        my_frame.setLayout(vbox)
        
        project_tree = QTreeWidget()
        btn_1 = QPushButton("Placeholder Button")
        btn_2 = QPushButton("Second placeholder Button")
        vbox.addWidget(project_tree)
        vbox.addWidget(btn_1)
        vbox.addWidget(btn_2)
        return my_frame

    def _connect_signals(self)-> None:
        self.actionLoadData.triggered.connect(self.load_data)

    def load_data(self)-> None:
        dlg = DataLoaderDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.imported_df is not None:
            df = dlg.imported_df
            specs = dlg.imported_column_specs