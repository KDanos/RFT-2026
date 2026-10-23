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

    # Migrate older projects pickled before Fluid.analysis_object existed
    btc = next((a for a in project.analyses if a.name == "Best Technical Case"), None)
    for analysis in project.analyses:
        for fluid in analysis.fluids:
            if not hasattr(fluid, "analysis_object") or fluid.analysis_object is None:
                fluid.analysis_object = btc if btc is not None else analysis

    # # Migrate older project pickeld before Fluid.is_editable attribute existed
    # for analysis in project.analyses:
    #     for fluid in fluid.analysis: 
    #         if not hasattr(fluid, "is_editable"):
    #             fluid.is_editable = False

    
    
    return project

