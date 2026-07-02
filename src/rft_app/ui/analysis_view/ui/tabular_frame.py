from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHeaderView, QTableView, QVBoxLayout, QWidget

from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from ui.analysis_view.model.view_display_controller import ViewDisplayController
from ui.analysis_view.ui.table_display_toolbar import TableDisplayToolbar


class TabularFrame(QFrame):
    column_unit_change = pyqtSignal(int, str, str)  # column index, column header and new unit

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
        self.table_view.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self._schedule_initial_column_layout()

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
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        self.main_layout.addWidget(self.table_view)
        header.sectionResized.connect(self._sync_toolbar_to_header)
        header.sectionClicked.connect(self._on_header_clicked)

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
        header = self.table_view.horizontalHeader()
        widths = [header.sectionSize(col) for col in range(header.count())]
        leading_offset = self.table_view.verticalHeader().width() + self.table_view.frameWidth()
        self.toolbar.set_column_geometry(leading_offset, widths)

    def _schedule_initial_column_layout(self, *_args) -> None:
        QTimer.singleShot(0, self._apply_initial_column_layout)

    def _apply_initial_column_layout(self) -> None:
        header = self.table_view.horizontalHeader()
        if header.count() == 0:
            return

        self.table_view.resizeColumnsToContents()

        widths = [header.sectionSize(col) for col in range(header.count())]
        total_width = sum(widths)
        available_width = self.table_view.viewport().width()

        if total_width > 0 and available_width > total_width:
            extra_width = available_width - total_width
            per_column, remainder = divmod(extra_width, header.count())
            for col, width in enumerate(widths):
                bonus = per_column + (1 if col < remainder else 0)
                header.resizeSection(col, width + bonus)

        self._sync_toolbar_to_header()

    def _on_header_clicked(self, section: int) -> None:
        if self._display_controller is None:
            return

        next_state = (self._sort_cycle_state.get(section, -1) + 1) % 3
        self._sort_cycle_state = {section: next_state}
        header = self.table_view.horizontalHeader()

        if next_state == 0:
            header.setSortIndicator(section, Qt.SortOrder.AscendingOrder)
            self._display_controller.proxy_model.sort(section, Qt.SortOrder.AscendingOrder)
        elif next_state == 1:
            header.setSortIndicator(section, Qt.SortOrder.DescendingOrder)
            self._display_controller.proxy_model.sort(section, Qt.SortOrder.DescendingOrder)
        else:
            header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            self._display_controller.proxy_model.sort(-1)
