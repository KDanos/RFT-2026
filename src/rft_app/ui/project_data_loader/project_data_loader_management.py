from typing import Any
from PyQt6.QtWidgets import QTableWidget
from project.canonical_names import RESERVED_CANONICAL_NAMES, USER_IMPORT_SUFFIX
from project import ColumnSpec, DataSetLogEntry
from units import STANDARD_QUANTITIES, normalise_from_user_units
from utilities import force_numeric, unique_name

def check_against_canonical_names(name:str)->str:
    stripped = name.strip()
    if stripped in RESERVED_CANONICAL_NAMES:
        return (f"{stripped} ({USER_IMPORT_SUFFIX})")
    return stripped

def create_column_specs(
    selected_mapping_columns:list[int],
    mapping_table:QTableWidget,
    column_names:list[str]
    )->list[ColumnSpec]:
    
    column_specs =[]
   
    for idx, mapping_col in enumerate(selected_mapping_columns):
        #Create the column specs, to hold the units
        quantity_combo = mapping_table.cellWidget(0,mapping_col)
        quantity_key = (
            quantity_combo.currentData()
            if quantity_combo is not None and quantity_combo.currentData()
            else "undefined"
        )
        units_combo = mapping_table.cellWidget(1,mapping_col)
        units = units_combo.currentText() if units_combo is not None else ""
        name = column_names[idx]
        current_spec = ColumnSpec(name,quantity_key, units )
        column_specs.append(current_spec)
    
    return column_specs

def define_column_names(
    selected_mapping_columns:list[int],
    mapping_table:QTableWidget
    )->list[str]:

    #Define temporary variables to help with the function
    col_names = []
    
    for mapping_col in selected_mapping_columns:
        #Extract the name of the column
        item = mapping_table.item(2,mapping_col)
        name = item.text().strip() if item and item.text().strip() else f"col_{mapping_col}"
        canonical_vetted_name = check_against_canonical_names(name)
        uniq_name = unique_name(canonical_vetted_name, col_names)
        
        col_names.append(uniq_name)
    return col_names

def populate_data_rows(
    data_rows:list[list[str]],
    rows_to_ignore:set[int],
    selected_mapping_columns:list[int],
    imported_column_specs:list[ColumnSpec],
    )->tuple[list[list[Any]],list[DataSetLogEntry]]:
    
    #Define temporary variables to help with the function
    info_log:list[DataSetLogEntry] = [] #reset at each import attempt
    rows:list[list[Any]] = []

    for r in range(len(data_rows)):  
        #Skip any rows that have been clicked to ignore
        if r in rows_to_ignore:
            continue

        row_values_to_import = data_rows[r]
        row_vals_for_df = []
        
        for idx,mapping_col in enumerate(selected_mapping_columns):
            source_column = mapping_col-1
            raw_value = row_values_to_import[source_column] if 0<=source_column<len(row_values_to_import) else ""
            
            # Normalise the numeric data
            spec = imported_column_specs[idx]
            quantity_key = spec.quantity_key
            user_unit = spec.unit
            
            # Is the quantity expected to be numeric?
            qty = STANDARD_QUANTITIES.get(quantity_key, STANDARD_QUANTITIES["undefined"])
            if  qty.is_numeric:
                coerced = force_numeric(raw_value)
            
                if coerced is None and not (
                    raw_value is None 
                    or (isinstance(raw_value,str) and raw_value.strip()=="")):
                    new_log_entry = DataSetLogEntry(
                                    message=f"Non-numeric {quantity_key} value removed; set to None",
                                    level="warning",
                                    row=r+1, # +1 so that the row number reflects the source data row (index starting at 1 instead of 0). Unclear what happens with eliminated rows
                                    column=spec.name,
                                    column_idx= idx,
                                    old_value = raw_value,
                                    new_value = coerced,
                                    quantity_key = quantity_key,
                                    reason = f"Expected a numeric value for {quantity_key}"
                                    )

                    info_log.append(new_log_entry)
                if coerced is None:
                    value = None
                elif user_unit:
                    value = normalise_from_user_units(user_unit,quantity_key,coerced)
                else: value = coerced

            else: # Non-numeric quantities (undefined, text, etc.)
                if isinstance (raw_value, str) and raw_value.strip()=="":
                    value = None
                else:
                    value = raw_value

            row_vals_for_df.append(value)
        rows.append(row_vals_for_df)

    return rows, info_log
