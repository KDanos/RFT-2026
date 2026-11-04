from PyQt6.QtCore import QObject, pyqtSignal

from model import AnalysisObject


class ProjectSignals(QObject):
    fluids_changed = pyqtSignal([],[object])
    project_units_changed = pyqtSignal()
    analysis_dataset_changed = pyqtSignal(AnalysisObject)

    # Inherited variables
    # None

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # Set project variables

        # Set module variables

        # Initialisation methods

    #--------Private UI--------
    # (none)

    #--------Public API--------
    # (none)
