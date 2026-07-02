from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from project import ColumnSpec, ProjectDataManager
from ui.widgets.table_widgets import UnitsComboBox


class TableDisplayToolbar(QFrame):
    """Units combos per column + decimal rounding controls (not in the table grid)."""

    def __init__(
        self,
        column_specs: list[ColumnSpec],
        project: ProjectDataManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._column_specs = list(column_specs)
        self._unit_combos: list[UnitsComboBox] = []
        self.decimals_check_box: QCheckBox
        self.decimal_limit_spin: QSpinBox

        self._build_display_toolbar()

    def _build_display_toolbar(self) -> None:
        """Build units row and decimal controls."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        units_row = QHBoxLayout()
        self._unit_combos.clear()

        for spec in self._column_specs:
            column_block = QVBoxLayout()

            label = QLabel(spec.name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            combo = UnitsComboBox(spec.quantity_key, self._project)
            if spec.unit:
                idx = combo.findText(spec.unit)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

            column_block.addWidget(label)
            column_block.addWidget(combo)
            units_row.addLayout(column_block)
            self._unit_combos.append(combo)

        outer.addLayout(units_row)
        outer.addStretch()

        decimals_container = QHBoxLayout()
        self.decimals_check_box = QCheckBox("Round decimals")
        self.decimals_check_box.setCheckState(Qt.CheckState.Checked)

        self.decimal_limit_spin = QSpinBox()
        self.decimal_limit_spin.setValue(1)
        self.decimal_limit_spin.setMaximum(10000)
        self.decimal_limit_spin.setReadOnly(False)
        self.decimal_limit_spin.lineEdit().setReadOnly(False)
        self.decimal_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.decimal_limit_spin.setKeyboardTracking(False)

        decimals_container.addWidget(self.decimals_check_box)
        decimals_container.addWidget(self.decimal_limit_spin)

        outer.addLayout(decimals_container)

    @property
    def unit_combos(self) -> list[UnitsComboBox]:
        return self._unit_combos