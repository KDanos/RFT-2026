from PyQt6.QtCore import QObject, pyqtSignal


class ProjectSignals(QObject):
    fluids_changed = pyqtSignal([],[object])
    project_units_changed = pyqtSignal()