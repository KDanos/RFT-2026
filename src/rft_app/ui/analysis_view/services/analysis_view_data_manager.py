from project.canonical_names import CANONICAL_EXCESS_PRESSURE
from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from units import get_project_default_units
import pandas as pd


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

def refresh_view_object_from_column_tree_selection(
    view:AnalysisView,
    analysis:AnalysisObject,
    project:ProjectDataManager,
    selected_columns:list[str]
    )->None:
    units_by_name = {s.name:s.unit for s in view.column_specs}
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