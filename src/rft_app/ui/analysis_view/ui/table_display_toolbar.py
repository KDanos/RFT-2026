from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from project import ColumnSpec, ProjectDataManager
from ui.analysis_view.model.view_table_formatting import DecimalDisplaySettings
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
        self._units_row_container: QWidget | None = None
        self.decimals_check_box: QCheckBox
        self.decimal_limit_spin: QSpinBox

        self._build_display_toolbar()

    def _build_display_toolbar(self) -> None:
        """Build units row and decimal controls."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        decimals_container = QHBoxLayout()
        decimals_container.setContentsMargins(0, 0, 0, 0)
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
        decimals_container.addStretch()

        outer.addLayout(decimals_container)

        self._units_row_container = QWidget(self)
        self._units_row_container.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._units_row_container)
        self.set_column_specs(self._column_specs)

    def set_column_specs(self, column_specs: list[ColumnSpec]) -> None:
        """Rebuild the units controls to match the current visible columns."""
        self._column_specs = list(column_specs)
        self._clear_units_row()
        if self._units_row_container is None:
            return

        self._unit_combos.clear()
        for spec in self._column_specs:
            combo = UnitsComboBox(spec.quantity_key, self._project)
            combo.setParent(self._units_row_container)
            if spec.unit:
                idx = combo.findText(spec.unit)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            self._unit_combos.append(combo)

        self._units_row_container.setMinimumHeight(self._combo_height())

    def sync_units_from_specs(self, column_specs: list[ColumnSpec]) -> None:
        """Update combo selections from the current view specs."""
        for combo, spec in zip(self._unit_combos, column_specs):
            if not spec.unit:
                continue
            idx = combo.findText(spec.unit)
            if idx >= 0:
                combo.blockSignals(True)
                combo.setCurrentIndex(idx)
                combo.blockSignals(False)

    def get_decimal_settings(self) -> DecimalDisplaySettings:
        return DecimalDisplaySettings(
            round_enabled=self.decimals_check_box.isChecked(),
            decimal_places=self.decimal_limit_spin.value(),
        )

    def set_column_geometry(self, offset: int, widths: list[int]) -> None:
        """Keep combo positions and widths aligned with table header sections."""
        if self._units_row_container is None:
            return

        x = max(0, offset)
        height = self._combo_height()
        for combo, width in zip(self._unit_combos, widths):
            combo.setGeometry(x, 0, max(1, width), height)
            x += max(1, width)
        self._units_row_container.setMinimumHeight(height)

    def _clear_units_row(self) -> None:
        if self._units_row_container is None:
            return
        for widget in self._unit_combos:
            if widget is not None:
                widget.deleteLater()

    def _combo_height(self) -> int:
        if self._unit_combos:
            return self._unit_combos[0].sizeHint().height()
        return self.decimal_limit_spin.sizeHint().height()

    @property
    def unit_combos(self) -> list[UnitsComboBox]:
        return self._unit_combos