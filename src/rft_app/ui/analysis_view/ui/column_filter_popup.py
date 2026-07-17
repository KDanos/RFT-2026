from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.analysis_view.model.filter_spec import FilterOperator, FilterSpec

_SCALAR_OPERATORS: list[tuple[str, FilterOperator]] = [
    ("> Greater than", FilterOperator.GT),
    ("< Less than", FilterOperator.LT),
    ("= Equals", FilterOperator.EQ),
    (">= Greater or equal", FilterOperator.GEQ),
    ("<= Less or equal", FilterOperator.LEQ),
    ("!= Not equal", FilterOperator.NEQ),
    ("Between", FilterOperator.BETWEEN),
    ("In list", FilterOperator.IN),
]

_PAGE_SCALAR = 0
_PAGE_BETWEEN = 1
_PAGE_IN = 2


class ColumnFilterPopup(QWidget):
    """Excel-style filter popup for one table column."""

    filter_applied = pyqtSignal(FilterSpec)
    filter_cleared = pyqtSignal(str)

    def __init__(
        self,
        column_name: str,
        value_items: list[tuple[Any, str]] | None = None,
        current_spec: FilterSpec | None = None,
        display_value: Callable[[Any], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self._column_name = column_name
        self._value_items = list(value_items or [])
        self._current_spec = current_spec
        self._display_value_fn = display_value or self._default_display_value

        self._operator_combo: QComboBox
        self._value_stack: QStackedWidget
        self._scalar_value_edit: QLineEdit
        self._between_lower_edit: QLineEdit
        self._between_upper_edit: QLineEdit
        self._value_list: QListWidget
        self._select_all_check: QCheckBox

        self._build_ui()
        self._connect_signals()
        self._restore_from_spec()

    @classmethod
    def open_at(
        cls,
        global_pos: QPoint,
        column_name: str,
        value_items: list[tuple[Any, str]] | None = None,
        current_spec: FilterSpec | None = None,
        display_value: Callable[[Any], str] | None = None,
        parent: QWidget | None = None,
    ) -> ColumnFilterPopup:
        """Create, position, and show a popup under a header filter button."""
        popup = cls(column_name, value_items, current_spec, display_value, parent)
        popup.adjustSize()
        popup.move(global_pos)
        popup.show()
        return popup

    def _build_ui(self) -> None:
        self.setMinimumWidth(240)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        title = QLabel(f"Filter: {self._column_name}")
        title.setWordWrap(True)
        root.addWidget(title)

        self._operator_combo = QComboBox(self)
        for label, operator in _SCALAR_OPERATORS:
            self._operator_combo.addItem(label, operator)
        root.addWidget(self._operator_combo)

        self._value_stack = QStackedWidget(self)

        scalar_page = QWidget(self)
        scalar_layout = QVBoxLayout(scalar_page)
        scalar_layout.setContentsMargins(0, 0, 0, 0)
        self._scalar_value_edit = QLineEdit(scalar_page)
        self._scalar_value_edit.setPlaceholderText("Value")
        scalar_layout.addWidget(self._scalar_value_edit)
        self._value_stack.addWidget(scalar_page)

        between_page = QWidget(self)
        between_layout = QVBoxLayout(between_page)
        between_layout.setContentsMargins(0, 0, 0, 0)
        self._between_lower_edit = QLineEdit(between_page)
        self._between_lower_edit.setPlaceholderText("From")
        self._between_upper_edit = QLineEdit(between_page)
        self._between_upper_edit.setPlaceholderText("To")
        between_layout.addWidget(self._between_lower_edit)
        between_layout.addWidget(self._between_upper_edit)
        self._value_stack.addWidget(between_page)

        in_page = QWidget(self)
        in_layout = QVBoxLayout(in_page)
        in_layout.setContentsMargins(0, 0, 0, 0)
        self._select_all_check = QCheckBox("Select all", in_page)
        self._select_all_check.setTristate(True)
        self._value_list = QListWidget(in_page)
        self._value_list.setMinimumHeight(140)
        for raw_values, display_label in self._value_items:
            item = QListWidgetItem(display_label)
            item.setData(Qt.ItemDataRole.UserRole, raw_values)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self._value_list.addItem(item)
        in_layout.addWidget(self._select_all_check)
        in_layout.addWidget(self._value_list)
        self._value_stack.addWidget(in_page)

        root.addWidget(self._value_stack)

        button_row = QHBoxLayout()
        apply_button = QPushButton("Apply", self)
        clear_button = QPushButton("Clear", self)
        cancel_button = QPushButton("Cancel", self)
        button_row.addWidget(apply_button)
        button_row.addWidget(clear_button)
        button_row.addWidget(cancel_button)
        root.addLayout(button_row)

        apply_button.clicked.connect(self._on_apply)
        clear_button.clicked.connect(self._on_clear)
        cancel_button.clicked.connect(self.close)

    def _connect_signals(self) -> None:
        self._operator_combo.currentIndexChanged.connect(self._on_operator_changed)
        self._select_all_check.stateChanged.connect(self._on_select_all_changed)
        self._value_list.itemChanged.connect(self._on_list_item_changed)

    def _on_operator_changed(self, _index: int) -> None:
        operator = self._selected_operator()
        if operator == FilterOperator.BETWEEN:
            self._value_stack.setCurrentIndex(_PAGE_BETWEEN)
        elif operator == FilterOperator.IN:
            self._value_stack.setCurrentIndex(_PAGE_IN)
        else:
            self._value_stack.setCurrentIndex(_PAGE_SCALAR)

    def _on_select_all_changed(self, state: int) -> None:
        if state == Qt.CheckState.PartiallyChecked.value:
            return
        check_state = (
            Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        )
        self._value_list.blockSignals(True)
        for row in range(self._value_list.count()):
            self._value_list.item(row).setCheckState(check_state)
        self._value_list.blockSignals(False)

    def _on_list_item_changed(self, _item: QListWidgetItem) -> None:
        self._sync_select_all_state()

    def _sync_select_all_state(self) -> None:
        checked_count = sum(
            1
            for row in range(self._value_list.count())
            if self._value_list.item(row).checkState() == Qt.CheckState.Checked
        )
        total = self._value_list.count()
        self._select_all_check.blockSignals(True)
        if checked_count == 0:
            self._select_all_check.setCheckState(Qt.CheckState.Unchecked)
        elif checked_count == total:
            self._select_all_check.setCheckState(Qt.CheckState.Checked)
        else:
            self._select_all_check.setCheckState(Qt.CheckState.PartiallyChecked)
        self._select_all_check.blockSignals(False)

    def _restore_from_spec(self) -> None:
        spec = self._current_spec
        if spec is None or spec.column_name != self._column_name:
            self._on_operator_changed(self._operator_combo.currentIndex())
            return

        index = self._operator_combo.findData(spec.operator)
        if index >= 0:
            self._operator_combo.setCurrentIndex(index)
        self._on_operator_changed(self._operator_combo.currentIndex())

        if spec.operator == FilterOperator.BETWEEN:
            self._between_lower_edit.setText(self._display_value_fn(spec.value))
            self._between_upper_edit.setText(self._display_value_fn(spec.value2))
        elif spec.operator == FilterOperator.IN:
            allowed_raw = set(spec.value or [])
            for row in range(self._value_list.count()):
                item = self._value_list.item(row)
                raw_values = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(raw_values, list):
                    checked = any(raw in allowed_raw for raw in raw_values)
                else:
                    checked = raw_values in allowed_raw
                item.setCheckState(
                    Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )
            self._sync_select_all_state()
        else:
            self._scalar_value_edit.setText(self._display_value_fn(spec.value))

    def _on_apply(self) -> None:
        spec = self._build_filter_spec()
        if spec is None:
            return
        self.filter_applied.emit(spec)
        self.close()

    def _on_clear(self) -> None:
        self.filter_cleared.emit(self._column_name)
        self.close()

    def _selected_operator(self) -> FilterOperator:
        return self._operator_combo.currentData()

    def _build_filter_spec(self) -> FilterSpec | None:
        operator = self._selected_operator()

        if operator == FilterOperator.BETWEEN:
            lower = self._parse_scalar(self._between_lower_edit.text())
            upper = self._parse_scalar(self._between_upper_edit.text())
            if lower is None or upper is None:
                return None
            return FilterSpec(
                column_name=self._column_name,
                operator=operator,
                value=lower,
                value2=upper,
            )

        if operator == FilterOperator.IN:
            selected: list[Any] = []
            for row in range(self._value_list.count()):
                item = self._value_list.item(row)
                if item.checkState() != Qt.CheckState.Checked:
                    continue
                raw_values = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(raw_values, list):
                    selected.extend(raw_values)
                else:
                    selected.append(raw_values)
            if not selected:
                return None
            return FilterSpec(
                column_name=self._column_name,
                operator=operator,
                value=selected,
            )

        parsed = self._parse_scalar(self._scalar_value_edit.text())
        if parsed is None:
            return None
        return FilterSpec(
            column_name=self._column_name,
            operator=operator,
            value=parsed,
        )

    @staticmethod
    def _default_display_value(value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _parse_scalar(text: str) -> Any | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            if "." in stripped or "e" in stripped.lower():
                return float(stripped)
            return int(stripped)
        except ValueError:
            return stripped
