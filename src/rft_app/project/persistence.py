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

    # Migrate older projects pickled before AnalysisView.annotations existed
    for analysis in project.analyses:
        for view in analysis.analysis_views:
            if not hasattr(view, "annotations"):
                view.annotations = []

    return project
