from __future__ import annotations

import pandas as pd

from project import AnalysisView, ColumnSpec, ProjectDataManager
from project.canonical_names import CANONICAL_EXCESS_PRESSURE
from ui.analysis_view.model.filter_spec import FilterSpec
from units import get_project_default_units


def insert_excess_pressure_column(df:pd.DataFrame, col_specs:list[ColumnSpec],project:ProjectDataManager)->tuple[pd.DataFrame, list[ColumnSpec]]:
    if CANONICAL_EXCESS_PRESSURE in df.columns:
        if len(df.columns)>2 and df.columns[2] == CANONICAL_EXCESS_PRESSURE:
            return df, col_specs
        
        cols = list(df.columns)
        cols.remove(CANONICAL_EXCESS_PRESSURE)
        cols.insert(2,CANONICAL_EXCESS_PRESSURE)
        df=df[cols]

        spec = next (s for s in col_specs if s.name ==CANONICAL_EXCESS_PRESSURE)
        remaining = [s for s in col_specs if s.name !=CANONICAL_EXCESS_PRESSURE]
        col_specs[:] = remaining [:2]+[spec]+remaining[2:]
        return df, col_specs
    
    df.insert(2,CANONICAL_EXCESS_PRESSURE,pd.NA)
    unit= get_project_default_units(project, "pressure")
    new_spec = ColumnSpec(CANONICAL_EXCESS_PRESSURE, "pressure",unit)
    col_specs.insert(2, new_spec)
    return df, col_specs

def build_view_df_and_col_specs_from_column_selection(
    analysis_df:pd.DataFrame,
    analysis_specs:list[ColumnSpec], 
    selected_names:list[str], 
    project:ProjectDataManager,
    )->tuple[pd.DataFrame,list[ColumnSpec]]:
    spec_by_name = {s.name:s for s in analysis_specs}
    df = analysis_df[selected_names].copy()
    col_specs = [spec_by_name[name] for name in selected_names]
    
    df, col_specs = insert_excess_pressure_column(df, col_specs, project)

    #Calculate excess pressure
    
    return df, col_specs

def on_column_unit_change(view:AnalysisView,col:int, header:str, unit:str)->None:
    updated = []
    for spec in view.column_specs:
        if spec.name == header:            
            updated.append(ColumnSpec(header, spec.quantity_key, unit))
        else:
            updated.append(spec)
    view.column_specs = updated


def on_row_filter_change(view: AnalysisView, filter_specs: list[FilterSpec]) -> None:
    """Store active row filters on the view (proxy filtering wired in Phase 2)."""
    view.row_filters = list(filter_specs)


def apply_column_filter(view: AnalysisView, filter_spec: FilterSpec) -> list[FilterSpec]:
    remaining = [f for f in view.row_filters if f.column_name != filter_spec.column_name]
    return remaining + [filter_spec]


def clear_column_filter(view: AnalysisView, column_name: str) -> list[FilterSpec]:
    return [f for f in view.row_filters if f.column_name != column_name]


def prune_row_filters_for_columns(view: AnalysisView, column_names: set[str]) -> list[FilterSpec]:
    return [f for f in view.row_filters if f.column_name in column_names]
