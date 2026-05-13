from dataclasses import dataclass
from __future__ import annotations
import pandas as pd


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
class Analysis:
    """Contains all the variables and objects generated, visualised and used in an analysis tab"""
    name:str
    data:pd.DataFrame | None = None
    column_units:list[]
    fluids:list[Fluid]

@dataclass
class Fluid:
    "An interpreted fluid in the reseroir"
    name:str
    type: FluidType 

@dataclass
class FluidType:
    "Standard fluid types available for selection in the project"
    name:str
    density: float
    color: str