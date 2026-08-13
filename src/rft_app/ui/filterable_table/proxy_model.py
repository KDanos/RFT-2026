from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel, pyqtSignal

from project.models import AnalysisView
from ui.filterable_table.filter_specs import (
    FilterSpec,
    FilterSpecNumber,
    filter_spec_from_dict,
    filter_spec_to_dict,
)
from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units, normalise_from_user_units
from utilities import round_value_to_decimal_points

import pandas as pd


class ProxyFilterModel(QSortFilterProxyModel):
    filters_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.active_filters: dict[int, FilterSpec] = {}
        self.use_filtered_rows_for_stats = True
        self.decimals_check_box = parent.decimals_check_box
        self.decimal_limit_spin = parent.decimal_limit_spin

    #--------Private UI--------
    def _analysis_view(self)->AnalysisView | None:
        """Return the AnalysisView for filter persistence (active_filters on the proxy vs column_filters on the view)."""
        parent = self.parent()
        return getattr(parent, "view", None) if parent is not None else None

    def _needs_display_rounded_si(self, filter_spec: FilterSpec) -> bool:
        if not isinstance(filter_spec, FilterSpecNumber):
            return False
        operators = {filter_spec.clause1.operator}
        if filter_spec.clause2 is not None:
            operators.add(filter_spec.clause2.operator)
        return bool(operators & {"==", "!="})

    def _to_display_rounded_si(self, source_model, col: int, raw_cell_value):
        if raw_cell_value is None or pd.isna(raw_cell_value):
            return raw_cell_value
        col_spec = source_model.column_specs[col]
        quantity_key = col_spec.quantity_key
        if not STANDARD_QUANTITIES[quantity_key].is_numeric:
            return raw_cell_value
        unit = col_spec.unit
        user_value = convert_from_normalised_to_user_units(
            unit, quantity_key, raw_cell_value
        )
        rounded = round_value_to_decimal_points(
            user_value, self.decimals_check_box, self.decimal_limit_spin
        )
        try:
            rounded_float = float(rounded)
        except (TypeError, ValueError):
            return raw_cell_value
        return normalise_from_user_units(unit, quantity_key, rounded_float)

    #--------Public API--------
    def clear_all_filters(self) -> None:
        if not self.active_filters:
            return
        self.active_filters.clear()
        self.sync_filters_to_view()
        self.notify_filters_changed()

    def clear_column_filter(self, column_index: int) -> None:
        self.active_filters.pop(column_index, None)
        self.sync_filters_to_view()
        self.notify_filters_changed()

    def filterAcceptsRow(self, source_row, source_parent: QModelIndex) -> bool:

        source_model = self.sourceModel()

        if len(self.active_filters) == 0:
            return True

        col_count = source_model.df.shape[1]
        for col, filter_spec in self.active_filters.items():

            if col < 0 or col >= col_count:
                continue

            cell_value = source_model.df.iat[source_row, col]
            if self._needs_display_rounded_si(filter_spec):
                cell_value = self._to_display_rounded_si(source_model, col, cell_value)

            if not filter_spec.pass_filter(cell_value):
                return False
        return True

    def notify_filters_changed(self) -> None:
        """Re-run row filtering and repaint header filter icons.

        invalidateFilter() updates which rows the proxy shows, but does not
        guarantee the horizontal header is repainted. The header draws its
        filter icon from active_filters in paintSection(), so we must call
        viewport().update() whenever filters are applied or cleared.
        """
        self.invalidateFilter()
        parent = self.parent()
        if parent is not None:
            header = parent.horizontalHeader()
            if header is not None:
                header.viewport().update()
        self.filters_changed.emit()

    def restore_filters_from_view(self) -> None:
        self.active_filters.clear()
        analysis_view = self._analysis_view()
        if analysis_view is None or not analysis_view.column_filters:
            return

        source_model = self.sourceModel()
        col_count = source_model.df.shape[1] if source_model is not None else 0
        for col, spec_dict in analysis_view.column_filters.items():
            column_index = int(col)
            if column_index < 0 or column_index >= col_count:
                continue
            self.active_filters[column_index] = filter_spec_from_dict(spec_dict)

    def set_column_filter(self, column_index: int, spec: FilterSpec) -> None:
        self.active_filters[column_index] = spec
        self.sync_filters_to_view()
        self.notify_filters_changed()

    def sync_filters_to_view(self) -> None:
        analysis_view = self._analysis_view()
        if analysis_view is None:
            return
        analysis_view.column_filters = {
            col: filter_spec_to_dict(spec)
            for col, spec in self.active_filters.items()
        }
