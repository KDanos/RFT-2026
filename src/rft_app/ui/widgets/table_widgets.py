from PyQt6 import QtWidgets

from project import ProjectDataManager
from units import STANDARD_QUANTITIES
from units.units_manager import QuantityType


class UnitsComboBox(QtWidgets.QComboBox):
    def __init__(
            self,
            quantity_key: str,
            project: ProjectDataManager,
            ) -> None:
        super().__init__()

        # Set project variables
        self.project: ProjectDataManager = project

        # Set module variables
        self.quantity_key: str = quantity_key
        self.quantity_object: QuantityType | None = None

        # Initialisation methods
        self.update_units_list(quantity_key)
        self.set_default_unit(project)

    #--------Private UI--------
    # (none — helpers live in Public API for shared reuse)

    #--------Public API--------

    def set_default_unit(self, project: ProjectDataManager) -> None:
        units_by_quantity = project.current_unit_system.units_by_quantity
        if self.quantity_key not in units_by_quantity:
            raise ValueError(
                f"No default unit for quantity {self.quantity_key!r} "
                f"in unit system {project.current_unit_system.label!r}"
            )
        default_unit = units_by_quantity[self.quantity_key]
        if not default_unit:
            return
        idx = self.findText(default_unit)
        if idx < 0:
            raise ValueError(
                f"Default unit {default_unit!r} for {self.quantity_key!r} "
                f"is not in the UnitsComboBox items"
            )
        self.setCurrentIndex(idx)

    def update_units_list(self, quantity_key: str) -> None:
        self.quantity_key = quantity_key
        self.quantity_object = STANDARD_QUANTITIES.get(quantity_key)
        self.clear()
        if self.quantity_object is None:
            raise ValueError(
                f"Unknown quantity key for UnitsComboBox: {quantity_key!r}"
            )
        self.addItems(self.quantity_object.units)
