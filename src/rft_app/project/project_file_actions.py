from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from project.manager import ProjectDataManager
from project.persistence import save_project, load_project


def save_project_as(parent, project, current_path)->Path|None:
    start = str(current_path) if current_path else "untitled.rftproj"
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Project AS",
        start,
        "RFT Project (*.rftproj);;All Files (*)",
    )
    if not path:
        return None #user cancelled

    path = Path(path)
    if path.suffix.lower() != ".rftproj":
        path= path.with_suffix(".rftproj")
    
    try: 
        save_project(project,path)
        #Mark the project as clean and no save required
        project.mark_clean()

    except OSError as e: 
        QMessageBox.critical(
            parent,
            "Save as",
            f"Could not save project \n{e}")
        return None
    
    #Return the path to the main window
    return path 

def open_project_dialog(parent, current_path :Path|None = None)->tuple[ProjectDataManager,Path]|None:
    start_dir = str(current_path.parent) if current_path else ""

    path_str,_ = QFileDialog.getOpenFileName(
        parent, 
        "Open Project", 
        start_dir, 
        "RFT Project (*.rftproj);;All Files (*)"
    )
    
    if not path_str:
        return None #user cancelled

    path = Path(path_str)
    try:
       project = load_project(path)
    except (OSError, TypeError) as e:
        QMessageBox.critical(
            parent, 
            "Open Project",
            f"Could not open project:\n{e}"
        )
        return None

    #Raise a "need to save flag" prior to exiting the project, as a safety net
    project.mark_clean()
    
    return project, path
