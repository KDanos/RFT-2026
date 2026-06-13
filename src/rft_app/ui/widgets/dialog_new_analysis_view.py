


from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QLabel,QComboBox, QHBoxLayout, QLineEdit, QPushButton, 
                            QVBoxLayout)

from project import AnalysisObject, AnalysisView, ProjectDataManager
from utilities import unique_name

class NewViewDialog(QDialog):
    def __init__(
        self,
        parent = None, 
        analysis: AnalysisObject = None, 
        project:ProjectDataManager = None)->None: 
        super().__init__(parent)
    
        # Provide access to the project data
        self.project = project
        self.analysis = analysis
 
        # Create new empty variables
        self.copy_from:AnalysisView = None  # the existing view which will form the basis of the new view
        self.new_view_name = ""
        self.df = None

        if analysis is not None and len(analysis.analysis_views)>0:
            self._offer_to_copy_existing_view()
        else: 
            self._create_new_empty_view()

        self._make_name_unique()
        
        self.analysis.analysis_views.append (self._create_new_view_instance())

    def _offer_to_copy_existing_view(self):

        # Start a dialog window
        copy_view_dialog = QDialog(self)
        copy_view_dialog.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        copy_view_dialog.setWindowTitle(self.analysis.name)
        
        # Chose a name
        name_line_edit = QLineEdit()
        name_line_edit.setPlaceholderText("New View Name")
        
        # Available views
        avail_views_layout = QHBoxLayout()
        avail_views_label = QLabel("Available Views: ")
        views_combo = QComboBox(copy_view_dialog)
        self.existing_views_list = [(view.name,view) for view in self.analysis.analysis_views]
        for name,view in self.existing_views_list:
            views_combo.addItem(name,view)
        
        avail_views_layout.addWidget(avail_views_label)
        avail_views_layout.addWidget(views_combo)

        # Button Box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel, 
            parent = copy_view_dialog,
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Copy Existing View")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Create Empty View")
        button_box.accepted.connect(copy_view_dialog.accept)
        button_box.rejected.connect(copy_view_dialog.reject)

        # Main Layout
        main_layout = QVBoxLayout(copy_view_dialog)
        main_layout.addWidget(name_line_edit)
        main_layout.addLayout(avail_views_layout)
        main_layout.addWidget(button_box)

        # Close if user does not want to copy an existing view
        if copy_view_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        self.copy_from = views_combo.currentData()
        self.new_view_name = name_line_edit.text().strip() or views_combo.currentText()
        self.df = self.copy_from.df

    def _create_new_empty_view(self)->None:
        # Start a dialog window
        copy_view_dialog = QDialog(self)
        copy_view_dialog.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        copy_view_dialog.setWindowTitle("Select a name for the new view")
        
        # Chose a name
        name_line_edit = QLineEdit()
        name_line_edit.setPlaceholderText("New View Name")

         # Main Layout
        main_layout = QVBoxLayout(copy_view_dialog)
        main_layout.addWidget(name_line_edit)
        self.new_view_name =name_line_edit.text()
        self.df = self.analysis.analysis_dataset.df
    
    def _make_name_unique(self):
        
        if self.new_view_name =="":
            self.new_view_name = "View"
        if len(self.analysis.analysis_views)>0:
            existing_names = [view.name for view in self.analysis.analysis_views]
        else:
            return self.new_view_name
        
        self.new_view_name = unique_name(self.new_view_name, existing_names)
        
    def _create_new_view_instance(self)->AnalysisView:
        new_view_object = AnalysisView(
            name = self.new_view_name,
            analysis_object= self.analysis,
            df = self.df
        )
        return new_view_object
