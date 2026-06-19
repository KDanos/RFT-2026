from PyQt6.QtCore import QSize, Qt, QSignalBlocker
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QSizePolicy, 
                            QSplitter, QTabWidget,  QToolBar, QVBoxLayout, QWidget, QMessageBox)
from pathlib import Path

from project import AnalysisObject, AnalysisView, ProjectDataManager, load_project, save_project
from ui.widgets import (DataLoaderDialogAnalysis, DataLoaderDialogProject, NewViewDialog)
from ui.main_window.analysis_workspace import AnalysisWorkspace
from ui.main_window.project_sidebar import ProjectSidebar

from ui import app_icon, load_qss, save_project_as, open_project_dialog

class MainWindowKD(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        #The the window title
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("CyPRES RFT Plotter")
        
        #Create empty variables and objects
        self.project = ProjectDataManager()
        self._project_path :Path|None = None

        self._build_ui()
        self._check_if_project_has_path()
        self._load_default_project_on_startup("260619 Three Analyses KD")

    def _load_default_project_on_startup(self, project_name:str) -> None:
        default_path = Path(__file__).resolve().parent.parent.parent / f"{project_name}.rftproj"
        print("Looking for:", default_path, "exists:", default_path.exists())
        if not default_path.exists():
            return
        try:
            self.project = load_project(default_path)
        except Exception as e:
            QMessageBox.warning(self, "Startup Project", f"Could not load default project:\n{e}")
            return
        self._project_path = default_path
        self.setWindowTitle(f"CyPRES RFT Plotter - {default_path.name}")
        
        # Update the sidebar
        self.project_sidebar.set_project(self.project)
        self.project_sidebar.refresh()
        # Update the workspace
        self.analysis_workspace.set_project(self.project)
        self.analysis_workspace.refresh_tabs_from_project()
        # Update the save action
        self._check_if_project_has_path() 
        self.project.mark_clean() 

    def _build_ui(self):
        self._build_actions()
        self._build_central_widget()
        self._build_menubar()
        # self._build_statusbar()
        self._connect_signals()
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)

    def _build_central_widget(self):
        central_widget = QWidget(self)
        hbox = QHBoxLayout(central_widget)
        self.mainSplitter = QSplitter()
        #Toolbar
        self._build_toolbar()
        
        #Create the Analysis WorkSpace
        self.analysis_workspace = AnalysisWorkspace(self.project)
        
        # Create the Sidebar
        self.project_sidebar = ProjectSidebar(self.project)
        #Status Bar
        
        #Manage the main splitter
        self.mainSplitter.addWidget(self.project_sidebar)
        self.mainSplitter.addWidget(self.analysis_workspace)
        hbox.addWidget(self.mainSplitter)
        self.mainSplitter.setSizes([1000,5000])
        self.setCentralWidget(central_widget)

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

    def _connect_signals(self)-> None:
        
        #Actions
        self.actionLoadData.triggered.connect(self._import_new_data)
        self.actionSaveAs.triggered.connect(self._save_project_as)
        self.actionSaveProject.triggered.connect(self._save_project)
        self.actionOpenProject.triggered.connect(self._open_project)
        self.actionCloseProject.triggered.connect(self._close_project)
        self.actionExitApplication.triggered.connect(self._exit_application)
        self.actionNewAnalysis.triggered.connect(self._start_new_analysis)
        
        #Widgets
        self.units_combo.currentIndexChanged.connect(self._on_project_units_changed)

        # Analyses tree 
        self.project_sidebar.all_analyses_tree.analysis_renamed.connect(self.analysis_workspace.refresh_tabs_from_project)
        self.project_sidebar.all_analyses_tree.analysis_deleted.connect(self.analysis_workspace.refresh_tabs_from_project)
        self.project_sidebar.all_analyses_tree.analysis_visibility_changed.connect(self.analysis_workspace.refresh_tabs_from_project)
        self.project_sidebar.all_analyses_tree.analysis_visibility_changed.connect(self.project_sidebar.refresh_all_analyses_tree)
        self.project_sidebar.all_analyses_tree.new_view_requested.connect(lambda analysis: self.create_new_analysis_view(analysis))

    def _import_new_data(self)-> None:
        dlg = DataLoaderDialogProject(parent = self, project = self.project)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.imported_df is not None:
            df = dlg.imported_df
            column_specs = dlg.imported_column_specs
            
            new_data_set_name = self.project.add_loaded_dataset(
                                            df, 
                                            column_specs,
                                            dlg.imported_name,
                                            info_log = dlg.info_log)
            new_data_set =self.project.get_dataset_by_name(new_data_set_name)

            #Raise a "need to save flag" prior to exiting the project
            self.project.mark_modified()
            self.project_sidebar.refresh_all_loaded_datasets_tree()

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
        
        self.project_sidebar.set_project(self.project)
        self.project_sidebar.refresh()
        
        self.analysis_workspace.set_project(self.project)
        self.analysis_workspace.refresh_tabs_from_project()

        self.project.mark_clean()
        self._check_if_project_has_path()   
    
    def _start_new_analysis(self)->None:
        #Exit the function if not data is available in the project
        if not self.project.datasets or len(self.project.datasets)==0:
            QMessageBox.critical(self,"New Analysis", """
            No pressure data has been loaded in the project. 
            Please import data first before proceeding with an analysis""")
            return
        
        #Open the analysis dialog to create a new analysis object
        analysis_dlg = DataLoaderDialogAnalysis(self, self.project)        
        if analysis_dlg.exec() != QDialog.DialogCode.Accepted:
            return

        #Add the new analysis object to the project
        new_analysis_object = analysis_dlg.result_analysis
        if new_analysis_object is None:
            return
        self.project.analyses.append(new_analysis_object)
        
        #Create a new analysis view
        self.create_default_analysis_view(new_analysis_object)
    
    def _check_if_project_has_path(self)-> None:
        has_path = self._project_path is not None
        self.actionSaveProject.setEnabled(has_path)

    def _close_project(self)-> None:

        if not self._confirm_discard_or_save_if_modified():
            return
        #New empty in-memeory project
        self.project = ProjectDataManager()
        self._project_path = None
        self.setWindowTitle("CyPRES RFT Plotter")

        # Clear the sidebar
        self.project_sidebar.set_project(self.project)
        self.project_sidebar.refresh()

        # Clear the workspace
        self.analysis_workspace.set_project(self.project)
        self.analysis_workspace.clear()

        #Reset the units combo to match the new project (set default)
        with QSignalBlocker(self.units_combo): 
            self.units_combo.clear()
            for system in self.project.available_unit_systems:
                self.units_combo.addItem(system.label, system)
            idx = self.units_combo.findData(self.project.current_unit_system)
            if idx >= 0:
                self.units_combo.setCurrentIndex(idx)

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

    def closeEvent(self, event):#overide default Qt behaviour when closing an application with a save prompt if required
        if not self._confirm_discard_or_save_if_modified():
            event.ignore() #keep the window open
            return
        event.accept()

    def create_default_analysis_view(self,analysis:AnalysisObject,tab:QTabWidget|None=None,):
        # #Create a new analysis view
        new_analysis_view_obj = AnalysisView(name = "New View")
        analysis.analysis_views.append(new_analysis_view_obj)

        # #Update the project actions
        self.project.mark_modified()
        self.project_sidebar.refresh_all_analyses_tree()
        self.analysis_workspace.refresh_tabs_from_project()

    def create_new_analysis_view(self, analysis:AnalysisObject)->None:
        # Launch the dialog window for the creation of a new view object
        dlg = NewViewDialog(self, analysis, self.project)
        if dlg.exec() !=QDialog.DialogCode.Accepted:
            return
        
        # Update the project actions
        self.project.mark_modified()
        self.project_sidebar.refresh_all_analyses_tree()
        self.analysis_workspace.refresh_tabs_from_project()

        
