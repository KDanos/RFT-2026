from PyQt6 import QtWidgets
from PyQt6.QtGui import QWheelEvent

from units.units_manager import STANDARD_QUANTITIES, QuantityType, UnitSystem


class UnitsComboBox(QtWidgets.QComboBox):
    def __init__(
            self,
            quantity_key: str,
            unit_system: UnitSystem,
            ) -> None:
        super().__init__()

        # Set project variables
        self.unit_system: UnitSystem = unit_system

        # Set module variables
        self.quantity_key: str = quantity_key
        self.quantity_object: QuantityType | None = None

        # Initialisation methods
        self.update_units_list(quantity_key)
        self.set_default_unit(unit_system)

    #--------Private UI--------

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Ignore hover-scroll so units don't change by accident; allow wheel
        # only while the dropdown list is open.
        if self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()

    #--------Public API--------

    def set_default_unit(self, unit_system: UnitSystem) -> None:
        if not isinstance(unit_system, UnitSystem):
            raise TypeError(
                f"UnitsComboBox expects a UnitSystem, got {type(unit_system).__name__}"
            )
        self.unit_system = unit_system
        units_by_quantity = unit_system.units_by_quantity
        if self.quantity_key not in units_by_quantity:
            raise ValueError(
                f"No default unit for quantity {self.quantity_key!r} "
                f"in unit system {unit_system.label!r}"
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
        self.addItems(sorted(self.quantity_object.units))
