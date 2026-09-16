from PyQt6.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget

from project import ColumnSpec, ProjectDataManager


class GraphicalSidebar(QFrame):
    def __init__(
            self,
            parent: QWidget | None = None,
            project: ProjectDataManager | None = None,
            col_specs: list[ColumnSpec] | None = None,
            ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project
        self.col_specs = col_specs

        # Set module variables
        # (none)

        # Initialisation methods
        self._build_ui()

    #--------Private UI--------

    def _build_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.btn2 = QPushButton("Placeholder")
        self.main_layout.addWidget(self.btn2)

    #--------Public API--------
    # No public methods yet.
