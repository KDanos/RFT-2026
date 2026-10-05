from typing import Protocol


class SignalCoordinator(Protocol):
    def on_fluids_changed(self)->None:...

    def on_units_changed(self)->None:...