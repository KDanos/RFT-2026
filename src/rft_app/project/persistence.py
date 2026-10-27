from pathlib import Path
import pickle

from project.manager import ProjectDataManager


def save_project(project: ProjectDataManager, path: str | Path) -> None:
    path = Path(path)
    with path.open("wb") as f:
        pickle.dump(project, f)

def load_project(path: str | Path) -> ProjectDataManager:
    path = Path(path)
    with path.open("rb") as f:
        project = pickle.load(f)

    if not isinstance(project, ProjectDataManager):
        raise TypeError("The selected file does not contain a valid RFT project")
    _ensure_fluid_contacts(project)
    return project

def _ensure_fluid_contacts(project: ProjectDataManager) -> None:
    from project.fluid_model import FluidContact
    for analysis in project.analyses:
        for fluid in analysis.fluids:
            if fluid.bottom_contact is None:
                fluid.bottom_contact = FluidContact(top_fluid=fluid)