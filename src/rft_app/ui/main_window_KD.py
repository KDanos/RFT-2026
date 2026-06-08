from PyQt6.QtCore import QSize, Qt, QSignalBlocker
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, 
                            QSizePolicy, QSplitter,  QToolBar, QTreeWidget, QVBoxLayout, QWidget, 
                            QTabWidget, QToolButton, QMessageBox)
from pathlib import Path

from project import AnalysisView, ProjectDataManager, load_project, save_project, AnalysisObject
from ui.widgets import (AnalysisViewWidget, DataLoaderDialogAnalysis, DataLoaderDialogProject,
                        AllDataSetsTree, AnalysesTree)
from ui import app_icon, load_qss, save_project_as, open_project_dialog

class MainWindowKD(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        #The the window title
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle("CyPRES RFT Plotter")
        
        #Create empty variables and objects
        self.action_list = []
        self.project = ProjectDataManager()
        self._project_path :Path|None = None

        self._build_ui()
        self._check_if_project_has_path()
        # self._load_default_project_on_startup()

    def _load_default_project_on_startup(self) -> None:
        default_path = Path(__file__).resolve().parent.parent / "260604 Two Views KD.rftproj"
        if not default_path.exists():
            return
        try:
            self.project = load_project(default_path)
        except Exception as e:
            QMessageBox.warning(self, "Startup Project", f"Could not load default project:\n{e}")
            return
        self._project_path = default_path
        self.setWindowTitle(f"CyPRES RFT Plotter - {default_path.name}")
        
        self._refresh_loaded_dataset_tree()
        self._refresh_analyses_tree()
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

        #Analysis Tabs
        self.analysis_frame = QFrame(self)
        self.analysis_frame_layout = QVBoxLayout()
        self.analysis_frame.setLayout(self.analysis_frame_layout)

        self.analyses_tabs = QTabWidget(self.analysis_frame)
        self.analysis_frame_layout.addWidget(self.analyses_tabs)

        self.analyses_tabs.setTabShape(QTabWidget.TabShape.Triangular)
        self.analyses_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.analyses_tabs.setTabsClosable(True)
        self.analyses_tabs.setMovable(True)

        self.new_tab_btn = QToolButton(self.analyses_tabs)
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setAutoRaise(True)
        self.analyses_tabs.setCornerWidget(self.new_tab_btn,Qt.Corner.TopRightCorner)
        
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
        self.analyses_tree_layout = QVBoxLayout(self.project_analyses_frame)
        
        self.btn_2 = QPushButton("Second placeholder Button")
        
        #Create the project "Loaded Data Sets" tree
        self.all_loaded_datasets_tree = AllDataSetsTree(self.project_data_frame, self.project)
        self.data_tree_layout.addWidget(self.all_loaded_datasets_tree)
        self._refresh_loaded_dataset_tree()
        
        #Create the project "Analyses" tree
        self.all_analyses_tree = AnalysesTree(self.project_analyses_frame,self.project)
        self.analyses_tree_layout.addWidget(self.all_analyses_tree)
        self._refresh_analyses_tree()

        #Add the frames to the main layout
        vbox.addWidget(self.project_data_frame)
        vbox.addWidget(self.project_analyses_frame)
        vbox.addWidget(self.btn_2)
        
        return self.project_controls_frame

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
        self.all_loaded_datasets_tree.dataset_renamed.connect(self._refresh_analyses_tree)
        self.all_loaded_datasets_tree.dataset_deleted.connect(self._refresh_analyses_tree)
        self.new_tab_btn.clicked.connect(self._add_analysis_tab)

    def _import_new_data(self)-> None:
        dlg = DataLoaderDialogProject(parent = self, project = self.project)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.imported_df is not None:
            df = dlg.imported_df
            column_specs = dlg.imported_column_specs
            dataframe_specs = dlg.dataframe_specs
            self.project.add_loaded_dataset(df, column_specs, dataframe_specs)
            
            #Raise a "need to save flag" prior to exiting the project
            self.project.mark_modified()
            self._refresh_loaded_dataset_tree()

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
        self._refresh_loaded_dataset_tree()
        self._refresh_analyses_tree()
        self._refresh_analyses_tree()
        self._check_if_project_has_path()   

    def _refresh_loaded_dataset_tree(self)-> None:
        self.all_loaded_datasets_tree.project = self.project #if project object can change on open
        self.all_loaded_datasets_tree.reload_from_project()
        self._apply_column_units_to_tree(self.all_loaded_datasets_tree)
        
    def _apply_column_units_to_tree(self, tree:QTreeWidget)->None:
        #Add units next to the column names
        with QSignalBlocker(tree):
            for i in range(tree.topLevelItemCount()):
                dataset_name = tree.topLevelItem(i).text(0)
                columns_node = tree.topLevelItem(i).child(1)
                dataset = self.project.get_dataset_by_name(dataset_name)
                
                for k in range (columns_node.childCount()):
                    col_item = columns_node.child(k)
                    header = col_item.text(0)

                    units = dataset.column_specs[k].unit
                    text = f"{header} [{units}]"
                    col_item.setText(0,text)
 
    def _refresh_analyses_tree(self)->None:
        self.all_analyses_tree.project = self.project
        self.all_analyses_tree.reload_from_project()

    def _refresh_analysis_tabs(self)->None:
        while self.analyses_tabs.count()>0:
            widget = self.analyses_tabs.widget(0)
            self.analyses_tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()
        
        for analysis in self.project.analyses:
            if analysis.is_visible:
                new_analysis_widget=self._add_analysis_tab(analysis)
                for view in analysis.analysis_views:
                    if view.is_visible:
                        self._create_new_analysis_view_tab(new_analysis_widget,analysis,view)

    def _add_analysis_tab(self,analysis:AnalysisObject)->QTabWidget:

        page = QWidget(self.analyses_tabs)
        layout= QVBoxLayout(page)
        new_widget = QTabWidget(page)
        layout.addWidget(new_widget)
        idx = self.analyses_tabs.addTab(page, analysis.name)
        self.analyses_tabs.setCurrentIndex(idx)
        return new_widget

    def _close_analysis_tab(self,idx:int)->None:
        self.analyses_tabs.removeTab(idx)
        self.Widget.deleteLater()
        
        #Mark all views as not visible
        

        #Raise a "need to save flag" prior to exiting the project
        self.project.mark_modified()

    def _create_new_analysis_view_tab(self, 
                                    parent:QTabWidget, 
                                    analysis:AnalysisObject,
                                    analysis_view_object:AnalysisView
                                    )->None: 
        
        page = AnalysisViewWidget(parent =parent,
                                    project = self.project,
                                    analysis = analysis,
                                    analysis_view_object=analysis_view_object )
        
        name = analysis_view_object.name
        idx = parent.addTab(page, name)
        parent.setCurrentIndex(idx)
        
        #Raise a "need to save flag" prior to exiting the project
        self.project.mark_modified()

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
        new_analysis_tab = self._add_analysis_tab(new_analysis_object)
        
        #Create a new analysis view
        new_analysis_view_obj = AnalysisView(name = "New View")
        new_analysis_object.analysis_views.append(new_analysis_view_obj)
        self._create_new_analysis_view_tab( parent = new_analysis_tab, 
                                            analysis = new_analysis_object, 
                                            analysis_view_object=new_analysis_view_obj)

        #Update the project actions
        self.project.mark_modified()
        self._refresh_analyses_tree()

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

        #Clear analysis tabs
        while self.analyses_tabs.count()>0:
            widget = self.analyses_tabs.widget(0)
            self.analyses_tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()

        #Clear the project data and analysese trees
        self._refresh_analyses_tree()
        self._refresh_loaded_dataset_tree()

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

    def closeEvent(self, event):#overide default Qt behaviour when closing an application with a save prompt if required
        if not self._confirm_discard_or_save_if_modified():
            event.ignore() #keep the window open
            return
        event.accept()