
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QSpacerItem, QSplitter, QToolBar, QTreeWidget, QVBoxLayout, QWidget
from qtpy.QtWidgets import QTabWidget, QToolButton
from project import ProjectDataManager, save_project_as, load_project
from ui.widgets.data_frame_tree import DataFrameTree
from ui.widgets.data_loader import DataLoaderDialog
from ui.widgets.analysis_widget import AnalysisWidget
from ui.icons import app_icon, load_qss


class MainWindowKD(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("CyPRES RFT Plotter")
        self.action_list = []
        self.project = ProjectDataManager()
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
        self.analysis_frame_layout = QVBoxLayout()
        self.analysis_frame.setLayout(self.analysis_frame_layout)

        self.analysis_tabs = QTabWidget(self.analysis_frame)
        self.analysis_frame_layout.addWidget(self.analysis_tabs)

        self.analysis_tabs.setTabShape(QTabWidget.TabShape.Triangular)
        self.analysis_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.analysis_tabs.setTabsClosable(True)
        self.analysis_tabs.setMovable(True)

        self.new_tab_btn = QToolButton(self.analysis_tabs)
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setAutoRaise(True)
        self.analysis_tabs.setCornerWidget(self.new_tab_btn,Qt.Corner.TopRightCorner)

        self.starting_tab = QWidget(self.analysis_tabs)
        
        staring_tab_layout = QVBoxLayout(self.starting_tab)
        self.analysis_tabs.addTab(self.starting_tab, "Analysis 1")


        
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
    
        #Create the units combo
        units_frame = QFrame()
        units_layout = QVBoxLayout()
        units_frame.setLayout(units_layout)
        units_label = QLabel("Project Units")
        self.units_combo = QComboBox(self)

        for system in self.project.available_unit_systems:
            self.units_combo.addItem(system.label,system) #text + payload
        
        idx = self.units_combo.findData(self.project.current_unit_system)
        if idx >=0: 
            self.units_combo.setCurrentIndex(idx)
        
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
        
        #Open Project
        self.actionOpenProject = QAction("Open Project", self)
        self.actionOpenProject.setIcon(app_icon("fa5.folder-open"))
        
        #Save Action
        self.actionSaveProject = QAction("Save", self)
        self.actionSaveProject.setIcon(app_icon("fa5.save"))
        
        #Save As action
        self.actionSaveAs = QAction("Save As", self)
        self.actionSaveAs.setIcon(app_icon("msc.save-as"))

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
        
        self.project_data_frame= QFrame(self)
        self.data_tree_layout = QVBoxLayout()
        self.project_data_frame.setLayout(self.data_tree_layout)

        btn_1 = QPushButton("Placeholder Button")
        btn_2 = QPushButton("Second placeholder Button")
        vbox.addWidget(self.project_data_frame)
        vbox.addWidget(btn_1)
        vbox.addWidget(btn_2)
        return my_frame

    def _connect_signals(self)-> None:
        self.actionLoadData.triggered.connect(self.import_new_data)
        self.actionSaveAs.triggered.connect(self._save_project_as)
        self.actionOpenProject.triggered.connect(self._open_project)
        
        self.units_combo.currentIndexChanged.connect(self._on_project_units_changed)

        self.new_tab_btn.clicked.connect(self._add_analysis_tab)

    def import_new_data(self)-> None:
        dlg = DataLoaderDialog(parent = self, project = self.project)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.imported_df is not None:
            df = dlg.imported_df
            specs = dlg.imported_column_specs
            dataset_name = self.project.add_loaded_dataset(df, specs)
            self._update_project_data(dataset_name)

    def _on_project_units_changed(self, _index:int)-> None:

        selected_system = self.units_combo.currentData()
        if selected_system is not None:
            self.project.current_unit_system = selected_system

    def _update_project_data(self,dataset_name):
        dataset = self.project._get_loaded_dataset(dataset_name)
        new_tree = DataFrameTree(self, dataset)
        self.data_tree_layout.addWidget(new_tree)
    
    def _save_project_as (self): 
        save_project_as(self.project)

    def _open_project (self):
        self.project = load_project()
        self._refresh_project_tree()

    def _refresh_project_tree(self):
        #Clear the existing project tree
        while self.data_tree_layout.count():
            item = self.data_tree_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        #Repopulate the project tree
        for dataset in self.project.loaded_datasets:
            new_tree = DataFrameTree(self,dataset)
            self.data_tree_layout.addWidget(new_tree)

    def _add_analysis_tab(self)->QWidget:
        idx = self.analysis_tabs.count()-1   
        
        page = self.analysis_tabs.widget(idx)
        new_widget = AnalysisWidget()
        layout = page.layout()
        layout.addWidget(new_widget)

    def _close_analysis_tab(self,idx:int)->None:
        self.analysis_tabs.removeTab(idx)
        self.Widget.deleteLater()

        