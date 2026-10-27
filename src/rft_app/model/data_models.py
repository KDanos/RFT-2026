"""Domain data models (datasets, analyses, analysis views)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from model.fluid_model import Fluid, FluidContact
from model.view_state import (RectAnnotation, StraightLineAnnotation, ViewWidgetSidebar,)



@dataclass
class AnalysisObject:
    """Contains all the variables and objects generated, visualised and used in an analysis tab"""
    name: str = ""
    source_datasets: list[str] = field(default_factory=list)
    analysis_dataset: DataSet | None = None
    formation_pres_src_col: str = None
    vert_depth_src_col: str = None
    fluids: list[Fluid] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    analysis_views: list[AnalysisView] = field(default_factory=list)

    @property
    def is_visible(self) -> bool:
        return any(view.is_visible for view in self.analysis_views)

    def delete_fluid(self, fluid: Fluid) -> None:
        # Remove the fluid as a possible contact to other fluids
        for other in self.fluids:
            bottom_fluid = other.bottom_contact.bottom_fluid
            if bottom_fluid is not None and bottom_fluid is fluid:
                other.bottom_contact.bottom_fluid = None
                other.bottom_contact.set_contact_data()

        # Remove the fluid from the analysis fluids
        self.fluids.remove(fluid)

        # Remove it from the analysis view persisted data
        for view in self.analysis_views:
            sidebar = view.sidebar
            if fluid in sidebar.visible_fluids:
                sidebar.visible_fluids.remove(fluid)
            if fluid is sidebar.active_fluid:
                sidebar.active_fluid = None
            if fluid is sidebar.ref_fluid:
                sidebar.ref_fluid = None

    def duplicate_fluid(self, fluid: Fluid, depth_shift:float) ->Fluid:
        from utilities import unique_name
        new_name = unique_name(
            fluid.name, 
            [f.name for f in self.fluids]
        )
        
        new_fluid = Fluid(
            name = new_name,
            type = fluid.type, 
            gradient_si=fluid.gradient_si,
            zero_pressure_depth_si= fluid.zero_pressure_depth_si+depth_shift,
            bottom_contact=  FluidContact(),
            plotting_depth_min_si= fluid.plotting_depth_min_si +depth_shift,
            plotting_depth_max_si= fluid.plotting_depth_max_si+depth_shift,
            analysis_object= self,
        )
        self.fluids.append(new_fluid)
        return new_fluid

    def rename_fluid(self, fluid: Fluid, new_name: str) -> None:
        from utilities import unique_name
        checked_name = unique_name(
            new_name,
            [f.name for f in self.fluids if f is not fluid],
            )
        fluid.name = checked_name


@dataclass
class AnalysisView:
    """Contains a dataframe with at least a vertical depth, formation pressure and excess pressure.
    It is linked to a view_tab, where the main interaction with the graphical data takes place"""
    name: str = ""
    analysis_object: AnalysisObject = None
    is_visible: bool = True
    df: pd.DataFrame = None
    column_specs: list[ColumnSpec] = field(default_factory=list)
    column_filters: dict[int, dict] = field(default_factory=dict)
    annotations: list[
        StraightLineAnnotation | RectAnnotation
        ] = field(default_factory=list)
    sidebar: ViewWidgetSidebar = field(default_factory=ViewWidgetSidebar)


@dataclass(frozen=True)
class ColumnSpec:
    """Metadata for a single column of an imported DataFrame

    Stored alongside the DataFrame (not inside it). The DataFrame holds only alpha-numeric or empty values.
    ColumnSpec records what those values mean (Quantiy) and in which units they were imported
    """
    name: str
    quantity_key: str
    unit: str | None = None


@dataclass
class DataSet:
    """Contains the dataframe, column specs and metadata of after data load for
        persistence and usage in the project"""
    name: str
    dataframe: pd.DataFrame
    column_specs: list[ColumnSpec]
    info_log: list[DataSetLogEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "Undefined"
    user_comments: list[tuple[datetime, str]] = field(default_factory=list)


@dataclass
class DataSetLogEntry:
    message: str
    level: str = "Warning"
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    row: int | None = None
    column: str | None = None
    column_idx: int | None = None
    old_value: Any = None
    new_value: Any = None
    quantity_key: str | None = None
    reason: str | None = None
