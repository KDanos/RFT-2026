
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidgetAction,
)

import pandas as pd

from ui import app_icon
from ui.filterable_table.filter_combos import NumberFilters, TextFilters
from ui.filterable_table.filter_specs import FilterSpecNumberSpecial, FilterSpecValues
from ui.filterable_table.filter_window import FilteringWindow
from ui.filterable_table.proxy_model import ProxyFilterModel
from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units
from utilities import round_value_to_decimal_points


class FilterByRowMenu(QMenu):
    def __init__(
            self,
            column_index: int,
            column_name: str,
            proxy_model: ProxyFilterModel,
            ) -> None:
        super().__init__()

        # Set project variables
        self.proxy_model = proxy_model

        # Set module variables
        self.column_index = column_index
        self.column_name = column_name

        pandas_model = self.proxy_model.sourceModel()
        self.df_si = pandas_model.df
        self.column_spec = pandas_model.column_specs[self.column_index]
        self.column_units = self.column_spec.unit
        self.column_quantity_key = self.column_spec.quantity_key
        self.column_is_numeric = STANDARD_QUANTITIES[self.column_spec.quantity_key].is_numeric
        self.decimals_check_box = pandas_model.decimals_check_box
        self.decimal_limit_spin = pandas_model.decimal_limit_spin

        self.tree = None
        self.tree_model = None

        # Initialisation methods
        self._build_ui()
        self._connect_actions_to_slots()

    #--------Private UI--------

    def _build_main_menu_options(self) -> None:

        if self.column_is_numeric:
            self.arithmetic_stats_widget = self._create_stats_widget()
            self.addAction(self.arithmetic_stats_widget)
            self.addSeparator()

            self.addAction(self.actionSortSmallesttoLargest)
            self.addAction(self.actionSortLargestoSmallest)

        else:
            self.addAction(self.actionSortAtoZ)
            self.addAction(self.actionSortZtoA)

        self.addAction(self.actionClearSorting)
        self.addSeparator()
        self.addAction(self.actionClearFilter)
        if self.column_is_numeric:
            self.addMenu(self.number_filter_menu)
        else:
            self.addMenu(self.text_filter_menu)

        self.addSeparator()
        self.tree_widget_action = self._create_filtering_tree_widget()
        self.addAction(self.tree_widget_action)

    def _build_number_filter_menu_options(self) -> None:
        self.number_filter_menu.addAction(self.actionNumberEquals)
        self.number_filter_menu.addAction(self.actionNumberDoesNotEqual)
        self.number_filter_menu.addSeparator()
        self.number_filter_menu.addAction(self.actionGreaterThan)
        self.number_filter_menu.addAction(self.actionGreaterThanOrEqualTo)
        self.number_filter_menu.addAction(self.actionLessThan)
        self.number_filter_menu.addAction(self.actionLessThanOrEqualTo)
        self.number_filter_menu.addAction(self.actionBetween)
        self.number_filter_menu.addSeparator()
        self.number_filter_menu.addAction(self.actionTop10)
        self.number_filter_menu.addAction(self.actionBottom10)
        self.number_filter_menu.addAction(self.actionAboveAverage)
        self.number_filter_menu.addAction(self.actionBelowAverage)

    def _build_text_filter_menu_options(self) -> None:
        self.text_filter_menu.addAction(self.actionTextEquals)
        self.text_filter_menu.addAction(self.actionTextDoesNotEqual)
        self.text_filter_menu.addSeparator()
        self.text_filter_menu.addAction(self.actionBeginsWith)
        self.text_filter_menu.addAction(self.actionEndsWith)
        self.text_filter_menu.addSeparator()
        self.text_filter_menu.addAction(self.actionContains)
        self.text_filter_menu.addAction(self.actionDoesNotContain)

    def _build_ui(self) -> None:
        self._define_main_menu_actions()
        self._define_number_filter_actions()
        self._define_text_filter_actions()
        self._define_menus()
        self._build_number_filter_menu_options()
        self._build_text_filter_menu_options()
        self._build_main_menu_options()

    def _build_value_tree_model(self) -> QStandardItemModel:

        model = QStandardItemModel()
        groups = self._get_unique_value_groups_for_tree()

        if self.column_is_numeric:
            labels = sorted(
                groups.keys(),
                key=lambda label: float("-inf") if label == "(blank)" else float(label),
            )
        else:
            labels = sorted(groups.keys())

        sellect_all_item = QStandardItem("(Select All)")
        sellect_all_item.setCheckable(True)
        sellect_all_item.setCheckState(Qt.CheckState.Checked)
        model.appendRow(sellect_all_item)

        for label in labels:
            item = QStandardItem(label)
            item.setCheckable(True)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(groups[label], Qt.ItemDataRole.UserRole)
            model.appendRow(item)

        model.itemChanged.connect(self._on_tree_item_changed)
        return model

    def _clear_column_filters(self, idx: int) -> None:
        self.proxy_model.clear_column_filter(idx)
        self._mark_project_modified()

    def _connect_actions_to_slots(self) -> None:

        self.actionClearFilter.triggered.connect(
            lambda checked=False, idx=self.column_index: self._clear_column_filters(idx)
        )

        for action in [
            self.actionNumberEquals,
            self.actionNumberDoesNotEqual,
            self.actionGreaterThan,
            self.actionGreaterThanOrEqualTo,
            self.actionLessThan,
            self.actionLessThanOrEqualTo,
            self.actionBetween,
        ]:
            action.triggered.connect(
                lambda checked=False, action=action: self._launch_filtering_window(action)
            )

        for action in [
            self.actionBelowAverage,
            self.actionAboveAverage,
            self.actionTop10,
            self.actionBottom10,
        ]:
            action.triggered.connect(
                lambda checked=False, action=action: self._on_special_numeric_filter(action)
            )

        for action in [
            self.actionTextEquals,
            self.actionTextDoesNotEqual,
            self.actionBeginsWith,
            self.actionEndsWith,
            self.actionContains,
            self.actionDoesNotContain,
        ]:
            action.triggered.connect(
                lambda checked=False, action=action: self._launch_filtering_window(action)
            )

    def _create_filtering_tree_widget(self) -> QWidgetAction:
        panel = QFrame(self)
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(0, 0, 0, 0)

        search_bar = QLineEdit(panel)
        search_bar.setPlaceholderText("Search")
        search_bar.textChanged.connect(self._filter_tree_items)
        main_layout.addWidget(search_bar)

        self.tree = QTreeView(panel)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setMinimumHeight(150)
        main_layout.addWidget(self.tree)

        self.tree_model = self._build_value_tree_model()
        self.tree.setModel(self.tree_model)

        ok_btn = QPushButton("OK", panel)
        ok_btn.clicked.connect(self._on_clicked_ok)
        cancel_btn = QPushButton("Cancel", panel)
        cancel_btn.clicked.connect(lambda: self.close())

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        main_layout.addLayout(buttons_layout)
        action = QWidgetAction(self)
        action.setDefaultWidget(panel)

        return action

    def _create_stats_widget(self) -> QWidgetAction:

        panel = QFrame(self)

        main_layout = QVBoxLayout(panel)
        stats_label = QLabel("Statistics")
        font = stats_label.font()
        font.setBold(True)
        stats_label.setFont(font)
        main_layout.addWidget(stats_label)

        stats_layout = QHBoxLayout()
        main_layout.addLayout(stats_layout)
        grid_layout = QGridLayout()
        stats_layout.addLayout(grid_layout)
        stats_layout.addStretch()
        grid_layout.setHorizontalSpacing(5)

        active_rows = self._get_active_rows()
        series = pd.to_numeric(
            self.df_si.iloc[active_rows, self.column_index],
            errors="coerce",
        ).dropna()

        min_value = series.min() if not series.empty else None
        max_value = series.max() if not series.empty else None
        average_value = series.mean() if not series.empty else None

        data_dict = {
            "Minimum": min_value,
            "Maximum": max_value,
            "Average": average_value,
        }

        for idx, (key, value) in enumerate(data_dict.items()):
            if value is None:
                display_value = "-"
            else:
                value = convert_from_normalised_to_user_units(
                    self.column_units, self.column_quantity_key, value
                )
                value = round_value_to_decimal_points(
                    value, self.decimals_check_box, self.decimal_limit_spin
                )
                display_value = str(value)

            key_label = QLabel(key)
            value_label = QLabel(display_value)
            grid_layout.addWidget(key_label, idx, 0)
            grid_layout.addWidget(value_label, idx, 1)

        action = QWidgetAction(self)
        action.setDefaultWidget(panel)
        return action

    def _define_main_menu_actions(self) -> None:

        self.actionSortSmallesttoLargest = QAction(
            app_icon("fa5s.sort-numeric-down"), "Sort Smallest to Largest", self
        )
        self.actionSortSmallesttoLargest.triggered.connect(
            lambda checked=False: self._sort_ascending_or_descending(Qt.SortOrder.AscendingOrder)
        )

        self.actionSortLargestoSmallest = QAction(
            app_icon("fa5s.sort-numeric-up"), "Sort Largest to Smallest", self
        )
        self.actionSortLargestoSmallest.triggered.connect(
            lambda checked=False: self._sort_ascending_or_descending(Qt.SortOrder.DescendingOrder)
        )

        self.actionClearSorting = QAction(app_icon("msc.remove"), "Clear Sorting", self)
        self.actionClearSorting.triggered.connect(lambda checked=False: self.proxy_model.sort(-1))

        self.actionClearFilter = QAction(app_icon("mdi.filter-off"), "Clear Filter", self)

        self.actionSortAtoZ = QAction(app_icon("fa5s.sort-alpha-down"), "Sort A to Z")
        self.actionSortAtoZ.triggered.connect(
            lambda checked=False: self._sort_ascending_or_descending(Qt.SortOrder.AscendingOrder)
        )

        self.actionSortZtoA = QAction(app_icon("fa5s.sort-alpha-down-alt"), "Sort Z to A")
        self.actionSortZtoA.triggered.connect(
            lambda checked=False: self._sort_ascending_or_descending(Qt.SortOrder.DescendingOrder)
        )

    def _define_menus(self) -> None:
        self.number_filter_menu = QMenu("Number Filters", self)
        self.number_filter_menu.setIcon(app_icon("mdi.numeric"))
        self.text_filter_menu = QMenu("Text Filters", self)
        self.text_filter_menu.setIcon(app_icon("ph.text-aa-light"))

    def _define_number_filter_actions(self) -> None:
        self.actionNumberEquals = QAction("Equals...", self)
        self.actionNumberEquals.setData(NumberFilters.EQUALS)

        self.actionNumberDoesNotEqual = QAction("Does Not Equal...", self)
        self.actionNumberDoesNotEqual.setData(NumberFilters.DOESNOTEQUAL)

        self.actionGreaterThan = QAction("Greater Than...", self)
        self.actionGreaterThan.setData(NumberFilters.GREATERTHAN)

        self.actionGreaterThanOrEqualTo = QAction("Greater Than Or Equal to...", self)
        self.actionGreaterThanOrEqualTo.setData(NumberFilters.GREATERTHANOREQUALTO)

        self.actionLessThan = QAction("Less Than...", self)
        self.actionLessThan.setData(NumberFilters.LESSTHAN)

        self.actionLessThanOrEqualTo = QAction("Less Than Or Equal To...", self)
        self.actionLessThanOrEqualTo.setData(NumberFilters.LESSTHANOREQUALTO)

        self.actionBetween = QAction("Between...", self)
        self.actionBetween.setData(NumberFilters.BETWEEN)

        self.actionTop10 = QAction("Top 10...", self)
        self.actionTop10.setData(NumberFilters.TOP10)

        self.actionBottom10 = QAction("Bottom 10...", self)
        self.actionBottom10.setData(NumberFilters.BOTTOM10)

        self.actionAboveAverage = QAction("Above Average...", self)
        self.actionAboveAverage.setData(NumberFilters.ABOVEAVERAGE)

        self.actionBelowAverage = QAction("Below Average...", self)
        self.actionBelowAverage.setData(NumberFilters.BELOWAVERAGE)

    def _define_text_filter_actions(self) -> None:

        self.actionTextEquals = QAction("Equals...", self)
        self.actionTextEquals.setData(TextFilters.EQUALS)

        self.actionTextDoesNotEqual = QAction("Does Not Equal...", self)
        self.actionTextDoesNotEqual.setData(TextFilters.DOESNOTEQUAL)

        self.actionBeginsWith = QAction("Begins With...", self)
        self.actionBeginsWith.setData(TextFilters.BEGINSWITH)

        self.actionEndsWith = QAction("Ends With...", self)
        self.actionEndsWith.setData(TextFilters.ENDSWITH)

        self.actionContains = QAction("Contains...", self)
        self.actionContains.setData(TextFilters.CONTAINS)

        self.actionDoesNotContain = QAction("Does Not Contain...", self)
        self.actionDoesNotContain.setData(TextFilters.DOESNOTCONTAIN)

    def _filter_tree_items(self, text: str) -> None:
        if self.tree_model is None:
            return

        needle = text.casefold().strip()
        for row in range(1, self.tree_model.rowCount()):
            item = self.tree_model.item(row)
            should_hide = needle not in item.text().casefold()
            self.tree.setRowHidden(row, self.tree.rootIndex(), should_hide)

    def _get_active_rows(self) -> list[int]:
        active_rows = []
        if self.proxy_model.use_filtered_rows_for_stats:
            for r in range(self.proxy_model.rowCount()):
                proxy_model_index = self.proxy_model.index(r, 0)
                pandas_model_index = self.proxy_model.mapToSource(proxy_model_index)
                active_rows.append(pandas_model_index.row())
        else:
            active_rows = list(range(len(self.df_si)))
        return active_rows

    def _get_unique_value_groups_for_tree(self) -> dict[str, frozenset]:
        active_rows = self._get_active_rows()
        series = self.df_si.iloc[active_rows, self.column_index]
        groups: dict[str, set] = {}

        if self.column_is_numeric:
            for si_value in series:
                if pd.isna(si_value):
                    label = "(blank)"
                    groups.setdefault(label, set()).add(float("nan"))
                    continue
                user_value = convert_from_normalised_to_user_units(
                    self.column_units, self.column_quantity_key, si_value
                )
                user_value = round_value_to_decimal_points(
                    user_value, self.decimals_check_box, self.decimal_limit_spin
                )
                label = str(user_value)
                groups.setdefault(label, set()).add(si_value)
        else:
            for value in series:
                label = "" if pd.isna(value) else str(value)
                groups.setdefault(label, set()).add(label)
        return {label: frozenset(values) for label, values in groups.items()}

    def _launch_filtering_window(self, action: QAction) -> None:

        filter_name = action.data().label if action.data() else ""

        window = FilteringWindow(self, self.column_name, filter_name)
        if window.exec() == QDialog.DialogCode.Accepted:
            self.proxy_model.set_column_filter(self.column_index, window.result_spec)
            self._mark_project_modified()

    def _mark_project_modified(self) -> None:
        table_view = self.proxy_model.parent()
        project = getattr(table_view, "project", None)
        if project is not None:
            project.mark_modified()

    def _on_clicked_ok(self) -> None:

        if self.tree_model is None:
            return

        selected_values = set()

        for row in range(1, self.tree_model.rowCount()):
            item = self.tree_model.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                stored = item.data(Qt.ItemDataRole.UserRole)
                if stored:
                    selected_values.update(stored)

        self.proxy_model.set_column_filter(self.column_index, FilterSpecValues(selected_values))
        self._mark_project_modified()
        self.close()

    def _on_special_numeric_filter(self, action: QAction) -> None:
        data = action.data()

        if data is None:
            return

        filter_applied = False
        if data is NumberFilters.TOP10 or data is NumberFilters.BOTTOM10:
            filter_applied = self._run_top_or_bottom_10_filter(action)

        if data is NumberFilters.ABOVEAVERAGE or data is NumberFilters.BELOWAVERAGE:
            filter_applied = self._run_above_or_below_average_filter(action) or filter_applied

        if filter_applied:
            self.proxy_model.sync_filters_to_view()
            self.proxy_model.notify_filters_changed()
            self._mark_project_modified()

    def _on_tree_item_changed(self, item: QStandardItem) -> None:
        if self.tree_model is None:
            return

        if item.row() == 0:
            state = item.checkState()
            for row in range(1, self.tree_model.rowCount()):
                child = self.tree_model.item(row)
                child.setCheckState(state)

    def _run_above_or_below_average_filter(self, action: QAction) -> bool:
        data = action.data()
        if data is None:
            return False

        active_rows = self._get_active_rows()
        series = pd.to_numeric(
            self.df_si.iloc[active_rows, self.column_index],
            errors="coerce",
        ).dropna()

        if series.empty:
            return False

        average = series.mean()
        new_spec = FilterSpecNumberSpecial(data.label, average)
        self.proxy_model.active_filters[self.column_index] = new_spec
        return True

    def _run_top_or_bottom_10_filter(self, action: QAction) -> bool:
        data = action.data()
        if data is None:
            return False

        active_rows = self._get_active_rows()
        series = pd.to_numeric(
            self.df_si.iloc[active_rows, self.column_index],
            errors="coerce",
        ).dropna()

        if series.empty:
            return False

        values = set(series)
        if data.symbol == "top10":
            unique = sorted(values, reverse=True)[:10]
        elif data.symbol == "bottom10":
            unique = sorted(values)[:10]
        else:
            return False

        threshold = float(unique[-1])
        new_spec = FilterSpecNumberSpecial(data.label, threshold)
        self.proxy_model.active_filters[self.column_index] = new_spec
        return True

    def _sort_ascending_or_descending(self, order: Qt.SortOrder) -> None:
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy_model.sort(self.column_index, order)

    #--------Public API--------
    # No public methods: this menu is constructed and shown by FilterableHeaderView.

