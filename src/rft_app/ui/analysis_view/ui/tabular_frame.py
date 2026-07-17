from __future__ import annotations

from collections import defaultdict
from typing import Any

from PyQt6.QtCore import QPoint, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHeaderView, QTableView, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from ui.analysis_view.model.filter_spec import FilterSpec
from ui.analysis_view.model.view_display_controller import ViewDisplayController
from ui.analysis_view.model.view_table_formatting import format_cell_for_table
from ui.analysis_view.ui.column_filter_popup import ColumnFilterPopup
from ui.analysis_view.ui.filterable_header_view import FilterableHeaderView
from ui.analysis_view.ui.table_display_toolbar import TableDisplayToolbar


class TabularFrame(QFrame):
    column_unit_change = pyqtSignal(int, str, str)  # column index, column header and new unit
    row_filter_applied = pyqtSignal(int, object)  # column index, FilterSpec
    row_filter_cleared = pyqtSignal(str)  # column name

    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        analysis: AnalysisObject | None = None,
        view: AnalysisView | None = None,
    ) -> None:
        super().__init__(parent)

        self.project = project
        self.analysis = analysis
        self.view = view
        self._display_controller: ViewDisplayController | None = None
        self._sort_cycle_state: dict[int, int] = {}
        self._header_view: FilterableHeaderView
        self._active_filter_popup: ColumnFilterPopup | None = None
        if analysis:
            self.dataset = analysis.analysis_dataset

        self._build_ui()

    # -------- Public API --------

    def bind_display_controller(self, controller: ViewDisplayController) -> None:
        self._display_controller = controller
        self.table_view.setModel(controller.proxy_model)
        controller.source_model.modelReset.connect(self._schedule_initial_column_layout)
        controller.proxy_model.modelReset.connect(self._schedule_initial_column_layout)
        controller.proxy_model.layoutChanged.connect(self._sync_toolbar_to_header)
        controller.display_changed.connect(self._sync_toolbar_to_header)
        self._schedule_initial_column_layout()

    def set_view_data(self, df, column_specs: list[ColumnSpec]) -> None:
        if self._display_controller is not None:
            self._display_controller.set_view_data(df, column_specs)
        self.toolbar.set_column_specs(column_specs)
        self._connect_toolbar_signals()
        self._sync_units_toolbar_from_specs(column_specs)
        self._sort_cycle_state.clear()
        self._header_view.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.refresh_filter_header()
        self._schedule_initial_column_layout()

    def refresh_filter_header(self) -> None:
        if self.view is None:
            return
        active_names = {spec.column_name for spec in self.view.row_filters}
        self._header_view.set_filtered_column_names(active_names)

    # -------- Private UI --------

    def _build_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)

        self.toolbar = TableDisplayToolbar(self.view.column_specs, self.project, self)
        self.main_layout.addWidget(self.toolbar)

        self._build_table_view_once()
        self._connect_toolbar_signals()

    def _build_table_view_once(self) -> None:
        self.table_view = QTableView(self)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self._header_view = FilterableHeaderView.install_on(self.table_view)
        self._header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._header_view.setStretchLastSection(False)
        self.main_layout.addWidget(self.table_view)

        self._header_view.sectionResized.connect(self._sync_toolbar_to_header)
        self._header_view.sort_requested.connect(self._on_header_clicked)
        self._header_view.filter_requested.connect(self._on_filter_requested)

    def _sync_units_toolbar_from_specs(self, column_specs: list[ColumnSpec] | None = None) -> None:
        specs = self.view.column_specs if column_specs is None else column_specs
        self.toolbar.sync_units_from_specs(specs)
        self._sync_toolbar_to_header()

    def _connect_toolbar_signals(self) -> None:
        for combo in self.toolbar.unit_combos:
            try:
                combo.currentIndexChanged.disconnect()
            except TypeError:
                pass

        for c, combo in enumerate(self.toolbar.unit_combos):
            combo.currentIndexChanged.connect(
                lambda _index, col=c: self._on_toolbar_unit_changed(
                    col,
                    self.toolbar.unit_combos[col].currentText(),
                )
            )

        try:
            self.toolbar.decimal_limit_spin.valueChanged.disconnect()
        except TypeError:
            pass
        try:
            self.toolbar.decimals_check_box.toggled.disconnect()
        except TypeError:
            pass

        self.toolbar.decimal_limit_spin.valueChanged.connect(
            lambda _value: self._on_decimal_settings_changed()
        )
        self.toolbar.decimals_check_box.toggled.connect(
            lambda _checked: self._on_decimal_settings_changed()
        )

    def _on_toolbar_unit_changed(self, col: int, unit: str) -> None:
        if self._display_controller is not None:
            self._display_controller.source_model.set_column_unit(col, unit)
            self._display_controller.display_changed.emit()

        header = self.view.column_specs[col].name
        self.column_unit_change.emit(col, header, unit)

    def _on_decimal_settings_changed(self) -> None:
        if self._display_controller is None:
            return

        self._display_controller.set_decimal_settings(self.toolbar.get_decimal_settings())
        self._display_controller.refresh_formatting()

    def _sync_toolbar_to_header(self, *_args) -> None:
        widths = [self._header_view.sectionSize(col) for col in range(self._header_view.count())]
        leading_offset = self.table_view.verticalHeader().width() + self.table_view.frameWidth()
        self.toolbar.set_column_geometry(leading_offset, widths)

    def _schedule_initial_column_layout(self, *_args) -> None:
        QTimer.singleShot(0, self._apply_initial_column_layout)

    def _apply_initial_column_layout(self) -> None:
        if self._header_view.count() == 0:
            return

        self.table_view.resizeColumnsToContents()

        widths = [self._header_view.sectionSize(col) for col in range(self._header_view.count())]
        total_width = sum(widths)
        available_width = self.table_view.viewport().width()

        if total_width > 0 and available_width > total_width:
            extra_width = available_width - total_width
            per_column, remainder = divmod(extra_width, self._header_view.count())
            for col, width in enumerate(widths):
                bonus = per_column + (1 if col < remainder else 0)
                self._header_view.resizeSection(col, width + bonus)

        self._sync_toolbar_to_header()

    def _on_header_clicked(self, section: int) -> None:
        if self._display_controller is None:
            return

        next_state = (self._sort_cycle_state.get(section, -1) + 1) % 3
        self._sort_cycle_state = {section: next_state}

        if next_state == 0:
            self._header_view.setSortIndicator(section, Qt.SortOrder.AscendingOrder)
            self._display_controller.proxy_model.sort(section, Qt.SortOrder.AscendingOrder)
        elif next_state == 1:
            self._header_view.setSortIndicator(section, Qt.SortOrder.DescendingOrder)
            self._display_controller.proxy_model.sort(section, Qt.SortOrder.DescendingOrder)
        else:
            self._header_view.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            self._display_controller.proxy_model.sort(-1)

    def _on_filter_requested(self, section: int) -> None:
        if self.view is None or self.view.df is None or section >= len(self.view.column_specs):
            return

        column_spec = self.view.column_specs[section]
        column_name = column_spec.name
        value_items = self._filter_value_items_for_section(section)
        existing = next(
            (spec for spec in self.view.row_filters if spec.column_name == column_name),
            None,
        )

        section_pos = self._header_view.sectionViewportPosition(section)
        global_pos = self._header_view.mapToGlobal(QPoint(section_pos, self._header_view.height()))

        if self._active_filter_popup is not None:
            self._active_filter_popup.close()
            self._active_filter_popup = None

        popup = ColumnFilterPopup.open_at(
            global_pos,
            column_name,
            value_items,
            existing,
            self._format_filter_value_for_section(section),
            parent=self,
        )
        self._active_filter_popup = popup
        popup.destroyed.connect(self._on_filter_popup_closed)
        popup.filter_applied.connect(
            lambda spec, col=section: self._on_filter_applied(col, spec)
        )
        popup.filter_cleared.connect(
            lambda _name, col=section: self._on_filter_cleared(col)
        )

    def _on_filter_popup_closed(self, *_args) -> None:
        self._active_filter_popup = None

    def _on_filter_applied(self, section: int, filter_spec: FilterSpec) -> None:
        self.row_filter_applied.emit(section, filter_spec)

    def _on_filter_cleared(self, section: int) -> None:
        if self.view is None or section >= len(self.view.column_specs):
            return
        self.row_filter_cleared.emit(self.view.column_specs[section].name)

    def _filter_value_items_for_section(self, section: int) -> list[tuple[list[Any], str]]:
        column_spec = self.view.column_specs[section]
        series = self.view.df[column_spec.name]
        unit = self.toolbar.unit_combos[section].currentText()
        decimal_settings = self.toolbar.get_decimal_settings()
        if self._display_controller is not None:
            decimal_settings = self._display_controller.decimal_settings

        grouped: defaultdict[str, list] = defaultdict(list)
        for raw in series.dropna().unique():
            display = format_cell_for_table(raw, column_spec, unit, decimal_settings)
            grouped[display].append(raw)

        return [(raws, display) for display, raws in sorted(grouped.items(), key=lambda item: item[0])]

    def _format_filter_value_for_section(self, section: int):
        column_spec = self.view.column_specs[section]
        unit = self.toolbar.unit_combos[section].currentText()

        def format_value(raw) -> str:
            decimal_settings = self.toolbar.get_decimal_settings()
            if self._display_controller is not None:
                decimal_settings = self._display_controller.decimal_settings
            return format_cell_for_table(raw, column_spec, unit, decimal_settings)

        return format_value
