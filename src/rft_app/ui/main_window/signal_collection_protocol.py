from typing import Protocol


class SignalCoordinator(Protocol):
    def on_fluids_changed(self)->None:...

    def on_project_units_changed(self)->None:...