from PyQt6.QtWidgets import QFrame, QWidget

from project import AnalysisObject, AnalysisView, ProjectDataManager


class GraphicalFrame(QFrame):
    def __init__(
            self,
            parent: QWidget | None = None,
            project: ProjectDataManager | None = None,
            analysis: AnalysisObject | None = None,
            view: AnalysisView | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project
        self.analysis = analysis
        self.view = view

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self) -> None:
        pass

    #--------Public API--------
    # No public methods yet.
