from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QSplitter,  QToolBar, QTreeWidget, QVBoxLayout, QWidget, QTabWidget, QToolButton, QMessageBox
from pathlib import Path

from project import ProjectDataManager, load_project, save_project, AnalysisObject
from utils import unique_name

from ui.widgets import DataLoaderDialogAnalysis, DataLoaderDialogProject, AnalysisWidget, AnalysisTree, AllDataSetsTree
from ui import app_icon, load_qss, save_project_as, open_project_dialog

class MainWindowKD(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("CyPRES RFT Plotter")
        self.action_list = []
        self.project = ProjectDataManager()
        self._project_path :Path|None = None
        self.build_ui()
        self._check_if_project_has_path()


    def build_ui(self):
        self._build_actions()
        self._build_central_widget()
        self._build_menubar()
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

        self._create_a_starting_analysis_tab()
        
        #Status Bar
        
        #Manage the main splitter
        self.mainSplitter.addWidget(self._build_project_controls_frame())
        self.mainSplitter.addWidget(self.analysis_frame)
        hbox.addWidget(self.mainSplitter)
        self.mainSplitter.setSizes([1000,5000])
        self.setCentralWidget(central_widget)

    def _create_a_starting_analysis_tab(self)->None:
        self.starting_tab = QWidget(self.analysis_tabs)
        self.staring_tab_layout = QVBoxLayout(self.starting_tab)
        self.analysis_tabs.addTab(self.starting_tab, "Analysis 1")

    def _build_menubar(self):
        menubar = self.menuBar()
        
        # File
        self.menu_file = menubar.addMenu("File")
        self.menu_file.addAction(self.actionOpenProject)
        self.menu_file.addAction(self.actionSaveProject)
        self.menu_file.addAction(self.actionSaveAs)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.actionCloseProject)
        self.menu_file.addAction(self.actionExitApplication)

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
            self.actionOpenProject,
            self.actionSaveProject,
            self.actionSaveAs,
            self.actionLoadData,
            self.actionNewAnalysis,
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
        #Open Project
        self.actionOpenProject = QAction("Open Project", self)
        self.actionOpenProject.setIcon(app_icon("fa5.folder-open"))
        #Save Action
        self.actionSaveProject = QAction("Save", self)
        self.actionSaveProject.setIcon(app_icon("fa5.save"))
        #Save As Action
        self.actionSaveAs = QAction("Save As", self)
        self.actionSaveAs.setIcon(app_icon("msc.save-as"))
        #Close Project Action
        self.actionCloseProject = QAction ("Close Project", self)
        self.actionCloseProject.setIcon(app_icon("mdi6.close-outline"))
        #Exit Application Action
        self.actionExitApplication = QAction("Exit the Application", self)
        self.actionExitApplication.setIcon(app_icon("mdi.exit-to-app"))
        
        # Data actions
        self.actionLoadData = QAction("Load Data", self)
        self.actionLoadData.setIcon (app_icon("ph.upload-simple-fill"))

        #Analysis actions
        self.actionNewAnalysis = QAction ("Start a new analysis", self)
        self.actionNewAnalysis.setIcon(app_icon("mdi6.chart-scatter-plot"))
        
        # Settings actions (kept original spelling for API compatibility)
        self.actionChangeProjecUnits = QAction("Change Project Units", self)

        # Help actions
        self.actionAbout = QAction("About", self)
        self.actionContact_Us = QAction("Contact Us", self)
    
    def _build_statusbar(self):
        pass

    def _build_project_controls_frame(self)->QFrame:
        self.project_controls_frame=QFrame()
        vbox = QVBoxLayout(self.project_controls_frame)
        
        #Build a tree for the loaded data
        self.project_data_frame= QFrame(self)
        self.data_tree_layout = QVBoxLayout(self.project_data_frame)

        #Build a tree for the analysis in the project
        self.project_analyses_frame = QFrame(self)
        self.analysis_tree_layout = QVBoxLayout(self.project_analyses_frame)
        
        self.btn_1 = QPushButton("Build Master Data Tree")
        self.btn_2 = QPushButton("Second placeholder Button")
        
        #Add the frames to the main layout
        vbox.addWidget(self.project_data_frame)
        vbox.addWidget(self.project_analyses_frame)
        vbox.addWidget(self.btn_1)
        vbox.addWidget(self.btn_2)
        return self.project_controls_frame

    def _connect_signals(self)-> None:
        self.actionLoadData.triggered.connect(self.import_new_data)
        self.actionSaveAs.triggered.connect(self._save_project_as)
        self.actionSaveProject.triggered.connect(self._save_project)
        self.actionOpenProject.triggered.connect(self._open_project)
        self.actionCloseProject.triggered.connect(self._close_project)
        self.actionExitApplication.triggered.connect(self._exit_application)
        
        self.actionNewAnalysis.triggered.connect(self._start_new_analysis)
        self.units_combo.currentIndexChanged.connect(self._on_project_units_changed)

        self.new_tab_btn.clicked.connect(self._add_analysis_tab)
        self.btn_1.clicked.connect (self._refresh_data_tree)

    def import_new_data(self)-> None:
        dlg = DataLoaderDialogProject(parent = self, project = self.project)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.imported_df is not None:
            df = dlg.imported_df
            column_specs = dlg.imported_column_specs
            dataframe_specs = dlg.dataframe_specs
            self.project.add_loaded_dataset(df, column_specs, dataframe_specs)
            
            #Raise a "need to save flag" prior to exiting the project
            self.project.mark_modified()
            self._refresh_data_tree()

    def _on_project_units_changed(self, _index:int)-> None:

        selected_system = self.units_combo.currentData()
        if selected_system is not None:
            self.project.current_unit_system = selected_system

            #Raise a "need to save flag" prior to exiting the project
            self.project.mark_modified()
    
    def _save_project_as (self)->None: 
        
        path = save_project_as(self, self.project, self._project_path)
        
        #Update the path of the current project
        if path is None:
            return #cancelled or save failed
        self._project_path = path
        self.setWindowTitle(f"CyPRES RFT Plotter - {path.name}")
        self._check_if_project_has_path()

    def _save_project(self)->None:
        if self._project_path is None: 
            self._save_project_as()
            return
        try:
            save_project(self.project, self._project_path)
            #Mark the project as clean and no save required
            self.project.mark_clean()
        except OSError as e: 
            QMessageBox.critical(self, "Save Project", f"Could not save project \n{e}")
    
    def _open_project (self):
        result = open_project_dialog(self, self._project_path)
        if result is None:
            return

        self.project, path = result
        self._project_path = path
        
        self.setWindowTitle (f"CyPRES RFT Plotter - {self._project_path.name}")
        self._refresh_data_tree()
        self._refresh_analyses_tree()
        self._check_if_project_has_path()   

    def _refresh_data_tree(self)-> None:
        #Clear the layout
        tree_layout = self.data_tree_layout
        while tree_layout.count():
            item = tree_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        self.project_data_tree = AllDataSetsTree(self.project_data_frame, self.project)
        
        #Add units next to the column names
        tree = self.project_data_tree
        for i in range(tree.topLevelItemCount()):
            dataset_name = tree.topLevelItem(i).text(0)
            columns_node = tree.topLevelItem(i).child(1)
            dataset = self.project._get_loaded_dataset(dataset_name)
            
            for k in range (columns_node.childCount()):
                col_item = columns_node.child(k)
                header = col_item.text(0)

                units = dataset.column_specs[k].unit
                text = f"{header} [{units}]"
                col_item.setText(0,text)
        
        tree_layout.insertWidget(0, self.project_data_tree)
 
    def _refresh_analyses_tree(self)->None:
        #Clear the existing analysese tree
        while self.analysis_tree_layout.count():
            item = self.analysis_tree_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        #Repopulate the analysis tree    
        for analysis in self.project.analyses:
            new_tree = AnalysisTree(self, analysis)
            self.analysis_tree_layout.addWidget(new_tree)

    def _add_analysis_tab(self)->None:
        new_analysis = self._create_new_analysis_object()
        page = QWidget(self.analysis_tabs)
        layout= QVBoxLayout(page)
        new_widget = AnalysisWidget(page)
        layout.addWidget(new_widget)
        idx = self.analysis_tabs.addTab(page, new_analysis.name)
        self.analysis_tabs.setCurrentIndex(idx)

    def _close_analysis_tab(self,idx:int)->None:
        self.analysis_tabs.removeTab(idx)
        self.Widget.deleteLater()

        #Raise a "need to save flag" prior to exiting the project
        self.project.mark_modified()

    def _create_new_analysis_object(self)->AnalysisObject: 
        new_analysis = AnalysisObject()
        existing_names = {analysis.name for analysis in self.project.analyses}
        new_analysis.name = unique_name("Analysis", existing_names)
        self.project.analyses.append(new_analysis)
        
        #Raise a "need to save flag" prior to exiting the project
        self.project.mark_modified()
        
        return new_analysis

    def _start_new_analysis(self)->None:
        #Exit the module if not data is available in the project
        if not self.project.loaded_datasets or len(self.project.loaded_datasets)==0:
            QMessageBox.critical(self,"New Analysis", """
            No pressure data has been loaded in the project. 
            Please import data first before proceeding with an analysis""")
            return
        
        analysis_dlg = DataLoaderDialogAnalysis(self, self.project)        
        analysis_dlg.show()

    def _check_if_project_has_path(self)-> None:
        has_path = self._project_path is not None
        self.actionSaveProject.setEnabled(has_path)

    def _close_project(self)-> None:
        print("_close_project called, is_modified =", self.project.is_modified)
        if not self._confirm_discard_or_save_if_modified():
            return
        
        #New empty in-memeory project
        self.project = ProjectDataManager()
        self._project_path = None
        self.setWindowTitle("CyPRES RFT Plotter")

        #Clear analysis tabs
        while self.analysis_tabs.count()>0:
            widget = self.analysis_tabs.widget(0)
            self.analysis_tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()

        #Create an empty starter tab
        self._create_a_starting_analysis_tab()

        #Clear the project data and analysese trees
        self._refresh_analyses_tree()
        self._refresh_data_tree()

        #Reset the units combo to match the new project (set default)
        self.units_combo.blockSignals(True)
        self.units_combo.clear()
        for system in self.project.available_unit_systems:
            self.units_combo.addItem(system.label, system)
        idx = self.units_combo.findData(self.project.current_unit_system)
        if idx >= 0:
            self.units_combo.setCurrentIndex(idx)
        self.units_combo.blockSignals(False)

        self._check_if_project_has_path()

    def _confirm_discard_or_save_if_modified(self)->bool:
        if not self.project.is_modified:
            return True
        reply = QMessageBox.question(
            self, 
            "Unsaved Changes", 
            "Save changes before continuing?",
            QMessageBox.StandardButton.Save
            |QMessageBox.StandardButton.Discard
            |QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            self._save_project()
            if self.project._is_modified: #save failed or cancelled
                return False
        
        return True

    def _exit_application(self)-> None:
        if not self._confirm_discard_or_save_if_modified():
            return
        self.close()