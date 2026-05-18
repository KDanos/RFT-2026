from pathlib import Path
import pickle

from project.manager import ProjectDataManager

def save_project(project:ProjectDataManager, path: str|Path)->None:
    path = Path(path)
    with path.open("wb") as f: # w: write mode, b:binary mode
        pickle.dump(project,f)

def load_project(path:str|Path)->ProjectDataManager:
    path = Path(path)
    with path.open ("rb") as f: # r: read mode, b: binary mode
        project = pickle.load(f)
    
    if not isinstance(project, ProjectDataManager):
        raise TypeError ("The selected file does not contain a valid RFT project")

    return project