
import sys
from pathlib import Path
APP_ROOT = Path(__file__).resolve().parents[1] / "src" / "rft_app"
sys.path.insert(0, str(APP_ROOT))

from project.models import AnalysisObject, AnalysisView


analysis = AnalysisObject(name = "Test Analysis")
analysis.analysis_views = [
    AnalysisView(name = "View 1"),
    AnalysisView(name ="New View"),
    AnalysisView(name = "Plot A")
]

list_of_existing_view_names = [view.name for view in (analysis.analysis_views if analysis is not None else [])]

print (list_of_existing_view_names)