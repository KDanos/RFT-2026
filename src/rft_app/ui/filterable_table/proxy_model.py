
from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units, normalise_from_user_units
from utilities import round_value_to_decimal_points
from ui.filterable_table.filter_specs import FilterSpec, FilterSpecNumber

import pandas as pd

class ProxyFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None)->None:
        super().__init__(parent)
        self.active_filters:dict[int, FilterSpec ]={}
        self.use_filtered_rows_for_stats = True
        self.decimals_check_box = parent.decimals_check_box
        self.decimal_limit_spin = parent.decimal_limit_spin
        
    def filterAcceptsRow(self, source_row, source_parent:QModelIndex)->bool: 
        
        # Inform the current model what model to use (reference to source_model in the code below)
        source_model = self.sourceModel() 

        # Accept all rows if no filters at all in the model
        if len(self.active_filters)==0:
            return True
        
        for col,filter_spec in self.active_filters.items():
            cell_value = source_model.df.iat[source_row, col]
            if self._needs_display_rounded_si(filter_spec):
                cell_value = self._to_display_rounded_si(source_model, col, cell_value)
            
            if not filter_spec.pass_filter(cell_value):     
                return False
        return True 

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
        # round_value_to_decimal_points returns str
        rounded = round_value_to_decimal_points(
            user_value, self.decimals_check_box, self.decimal_limit_spin
        )
        try:
            rounded_float = float(rounded)
        except (TypeError, ValueError):
            return raw_cell_value
        return normalise_from_user_units(unit, quantity_key, rounded_float)
       
    
    