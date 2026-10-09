from dataclasses import dataclass
from project.canonical_names import CANONICAL_EXCESS_PRESSURE, CANONICAL_FORMATION_PRESSURE, CANONICAL_VERTICAL_DEPTH
from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from project.fluid_model import Fluid
from units import get_project_default_units
import pandas as pd

SERIES_COLORS = [
    "blue", "red", "green",  "purple", "cyan",
    "magenta", "brown", "olive", "teal", "navy", "maroon", "orange",
]
SERIES_SYMBOLS = [
    "o", "s", "t", "d", "+", "x", "p", "h", "star", "t1", "t2", "t3",
]

@dataclass
class ScatterSeriesDefinition:
    name:str
    mask:pd.Series
    color:str
    symbol:str

#--------Public API--------

def build_view_df_and_col_specs_from_column_selection(
        analysis_df: pd.DataFrame,
        analysis_specs: list[ColumnSpec],
        selected_names: list[str],
        project: ProjectDataManager,
        ) -> tuple[pd.DataFrame, list[ColumnSpec]]:
    spec_by_name = {s.name: s for s in analysis_specs}
    df = analysis_df[selected_names].copy()
    col_specs = [spec_by_name[name] for name in selected_names]

    df, col_specs = insert_excess_pressure_column(df, col_specs, project)

    # Calculate excess pressure

    return df, col_specs

def insert_excess_pressure_column(
        df: pd.DataFrame,
        col_specs: list[ColumnSpec],
        project: ProjectDataManager,
        ) -> tuple[pd.DataFrame, list[ColumnSpec]]:
    if CANONICAL_EXCESS_PRESSURE in df.columns:
        if len(df.columns) > 2 and df.columns[2] == CANONICAL_EXCESS_PRESSURE:
            return df, col_specs

        cols = list(df.columns)
        cols.remove(CANONICAL_EXCESS_PRESSURE)
        cols.insert(2, CANONICAL_EXCESS_PRESSURE)
        df = df[cols]

        spec = next(s for s in col_specs if s.name == CANONICAL_EXCESS_PRESSURE)
        remaining = [s for s in col_specs if s.name != CANONICAL_EXCESS_PRESSURE]
        col_specs[:] = remaining[:2] + [spec] + remaining[2:]
        return df, col_specs

    df.insert(2, CANONICAL_EXCESS_PRESSURE, pd.NA)
    unit = get_project_default_units(project, "pressure")
    new_spec = ColumnSpec(CANONICAL_EXCESS_PRESSURE, "pressure", unit)
    col_specs.insert(2, new_spec)
    return df, col_specs

def on_column_unit_change(
        view: AnalysisView,
        col: int,
        header: str,
        unit: str,
        ) -> None:
    # Update the object in the model
    updated = []
    for spec in view.column_specs:
        if spec.name == header:
            updated.append(ColumnSpec(header, spec.quantity_key, unit))
        else:
            updated.append(spec)
    view.column_specs = updated

def refresh_view_object_from_column_tree_selection(
        view: AnalysisView,
        analysis: AnalysisObject,
        project: ProjectDataManager,
        selected_columns: list[str],
        ) -> None:
    
    units_by_name = {s.name: s.unit for s in view.column_specs}
    new_df, new_col_specs = build_view_df_and_col_specs_from_column_selection(
        analysis.analysis_dataset.dataframe,
        analysis.analysis_dataset.column_specs,
        selected_columns,
        project,
    )
    view.df = new_df
    view.column_specs = [
        ColumnSpec(s.name, s.quantity_key, units_by_name.get(s.name, s.unit))
        for s in new_col_specs
    ]

def calculate_excess_pressure_column(
    df:pd.DataFrame,
    reference_fluid:Fluid| None,
    )->None: 
    """
    y = mx + c, where   y = pressure of fluid at depth x
                        m = slope in pressure/length
                        c = pressure at depth = 0

        to compute c, use fluid.zero_pressure_depth(d_0):
        0 = m * d_0 + c
        c = -m.d_0

        y = m(x - d_0)    
    """
    if CANONICAL_EXCESS_PRESSURE not in df.columns:
        raise KeyError(
            f"{CANONICAL_EXCESS_PRESSURE!r} missing from dataframe; "
            "insert_excess_pressure_column must run first"
        )
    
    if reference_fluid is None: 
        df[CANONICAL_EXCESS_PRESSURE] = pd.NA
        return

    p = df[CANONICAL_FORMATION_PRESSURE]
    z= df[CANONICAL_VERTICAL_DEPTH]
    p_ref =  reference_fluid.gradient_si * (
        z - reference_fluid.zero_pressure_depth_si
        )
    df [CANONICAL_EXCESS_PRESSURE] =(p-p_ref).where(p.notna() & (p>0))

def build_scatter_series(
    df:pd.DataFrame, 
    primary_identifier:str|None, 
    secondary_identifier:str|None
    )-> list[tuple[str, pd.Series, str, str]]:
    
    """Return [(display_name, boolean_mask, color, symbol)]"""
    
    if df is None or df.empty:
        return []

    primary = (primary_identifier 
        if primary_identifier and primary_identifier != "None" 
        else None)
    secondary = (
        secondary_identifier
        if secondary_identifier and secondary_identifier != "None"
        else None
    )

    if primary is None and secondary is None:
        return[
            ScatterSeriesDefinition
            ("All Data", 
            pd.Series(True, index= df.index),
            SERIES_COLORS[0], 
            SERIES_SYMBOLS[0])
        ]
    
    primary_values = list(df[primary].unique()) if primary else [None]
    secondary_values = list(df[secondary].unique()) if secondary else [None]
    color_count = min(len(SERIES_COLORS), len(primary_values)) if primary else 1
    symbol_count = min(len(SERIES_SYMBOLS), len(secondary_values)) if secondary else 1

    series_defition: list[tuple[str, pd.Series, str, str]] = []
    for s in range(symbol_count):
        for c in range(color_count):
            primary_value = primary_values[c] if primary else None
            secondary_value = secondary_values[s] if secondary else None
            primary_mask = (
                df[primary] == primary_value
                if primary
                else pd.Series(True, index=df.index)
            )
            secondary_mask = (
                df[secondary] == secondary_value
                if secondary
                else pd.Series(True, index=df.index)
            )
            mask = primary_mask & secondary_mask
            if not mask.any():
                continue
            if primary and secondary:
                name = f"{primary_value}, {secondary_value}"
            elif primary:
                name = str(primary_value)
            else:
                name = str(secondary_value)
            
            new_scatter = ScatterSeriesDefinition(
                    name, 
                    mask, 
                    SERIES_COLORS[c], 
                    SERIES_SYMBOLS[s]
                    )
            
            series_defition.append(new_scatter)
    return series_defition
        