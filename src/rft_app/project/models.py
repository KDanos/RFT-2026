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
    ColumnSpec records what those values mean (Quantiy) and in which units they were imported
    """
    name:str
    quantity_key:str
    unit: str | None = None

@dataclass
class DataSet:
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
    analysis_dataset:DataSet | None = None
    formation_pres_src_col: str = None
    vert_depth_src_col:str = None
    displayed_dataframe: pd.DataFrame | None = None
    fluids:list[Fluid] = field (default_factory= list)
    parameters:dict[str,Any] = field (default_factory= dict)
    analysis_views: list[AnalysisView]  = field(default_factory=list)
    @property
    def is_visible(self)->bool:
        return any(view.is_visible for view in self.analysis_views)

@dataclass
class AnalysisView:
    """Contains a dataframe with at least a vertical depth, formation pressure and excess pressure.
    It is linked to a view_tab, where the main interaction with the graphical data takes place"""
    name: str = ""
    analysis_object: AnalysisObject = None
    is_visible:bool = True
    df: pd.DataFrame= None


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

