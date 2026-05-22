from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class DataFrameSpecs:
    "Meta data for loaded data set"
    name:str

@dataclass(frozen=True)
class ColumnSpec:
    """Metadata for a single column of an imported DataFrame

    Stored alongside the DataFrame (not inside it). The DataFrame holds only alpha-numeric or empty values. 
    ColumnSpec records what those values mean (Qquantiy) and in which units they were imported
    """
    name:str
    quantity_key:str
    unit: str

@dataclass
class LoadedDataSet:
    """Contains the dataframe, column specs and metadata of after data load for 
        persistence and usage in the project"""
    name:str
    dataframe: pd.DataFrame
    column_specs: list[ColumnSpec]

@dataclass
class AnalysisObject:
    """Contains all the variables and objects generated, visualised and used in an analysis tab"""
    name:str = ""
    source_datasets:list[str] = field(default_factory= list)
    column_indices:list[int] = field(default_factory= list)
    stored_data:pd.DataFrame | None = None
    displayed_data: pd.DataFrame | None = None
    column_specs: list[AnalysisColumnSpec] = field (default_factory= list)
    fluids:list[Fluid] = field (default_factory= list)
    parameters:dict[str,Any] = field (default_factory= dict)

@dataclass
class Fluid:
    """An interpreted fluid in the reservoir"""
    name:str
    type: FluidType 

@dataclass
class FluidType:
    """Standard fluid types available for selection in the project"""
    name:str
    density: float
    color: str

@dataclass
class AnalysisColumnSpec:
    """Carries the metadata, unit and unit conversion facilitation for the displayed data in the analysis"""
    name:str
    quantity_key: str
    source_unit: str
    display_unit: str
