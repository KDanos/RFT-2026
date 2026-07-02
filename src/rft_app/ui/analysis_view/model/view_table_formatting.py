
import pandas as pd

from dataclasses import dataclass
from typing import Any


from project import ColumnSpec
from utilities import is_numeric
from units import STANDARD_QUANTITIES, convert_from_normalised_to_user_units


@dataclass
class DecimalDisplaySettings:
    """How numeric table cells  are rounded for display."""

    round_enabled:bool = True
    decimal_places:int = 1

def format_normalised_cell_value(
    value:Any, 
    quantity_key:str,
    output_unit: str, 
    ) ->str:
    """Convert one normalised df value to user-unit display text."""
    if pd.isna(value):
        return ""

    qty = STANDARD_QUANTITIES.get(quantity_key, STANDARD_QUANTITIES["undefined"])
    if qty.is_numeric:
        converted = convert_from_normalised_to_user_units(
            output_unit,
            quantity_key, 
            value,
            )
        return str(converted)

    return str(value)

def apply_decimal_formatting(
    display_str:str,
    *,
    round_enabled:bool,
    decimal_places: int,
    )->str:
    """Apply optional rounding to an already-formatted display string."""
    if display_str =="" or not is_numeric(display_str):
        return display_str
    
    if not round_enabled:
        return display_str

    if decimal_places ==0:
        rounded = int(round(float(display_str), decimal_places))
    else:
        rounded = round(float(display_str), decimal_places)
    return str(rounded)

def format_cell_for_table(
    value:Any, 
    column_spec:ColumnSpec, 
    output_unit:str, 
    decimal_settings: DecimalDisplaySettings|None = None, 
    )-> str:
    """Single entry point: unit conert, then optional decimal rounding."""
    if decimal_settings is None:
        decimal_settings = DecimalDisplaySettings()

    display = format_normalised_cell_value(
        value, 
        column_spec.quantity_key,
        output_unit
        )

    return apply_decimal_formatting(
        display, 
        round_enabled=decimal_settings.round_enabled,
        decimal_places=decimal_settings.decimal_places,
    )