from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import Any

import pandas as pd


@dataclass
class DataSetLogEntry:
    message: str
    level:str = "Warning"
    timestamp:datetime= field(default_factory  = lambda:datetime.now())
    row: int | None = None
    column:str | None = None
    column_idx: int | None = None
    old_value: Any = None
    new_value: Any = None
    quantity_key:str | None = None
    reason:str | None = None

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
    info_log:list[DataSetLogEntry] =field(default_factory=list)
    created_at:datetime=field (default_factory=lambda:datetime.now(timezone.utc))
    created_by:str = "Undefined"
    user_comments: list[str] = field(default_factory=list)

@dataclass
class AnalysisObject:
    """Contains all the variables and objects generated, visualised and used in an analysis tab"""
    name:str = ""
    source_datasets:list[str] = field(default_factory= list)
    analysis_dataset:DataSet | None = None
    formation_pres_src_col: str = None
    vert_depth_src_col:str = None
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
    column_specs : list[ColumnSpec] =field (default_factory=list)


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

