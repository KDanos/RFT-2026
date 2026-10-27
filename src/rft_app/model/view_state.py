"""Persisted view-state models (sidebar selections, chart annotations)."""
from __future__ import annotations

from dataclasses import dataclass, field

from model.fluid_model import Fluid


@dataclass
class ViewWidgetSidebar:
    """Captures the selections of the GUI sidebar"""
    ref_fluid: Fluid | None = None
    primary_series_identifier: str = "None"
    secondary_series_identifier: str = "None"
    active_fluid: Fluid | None = None
    visible_fluids: list[Fluid] = field(default_factory=list)


@dataclass
class StraightLineAnnotation:
    """Persisted straight-line annotation for charts in an AnalysisView."""
    start_si: tuple[float, float]
    end_si: tuple[float, float]
    color: str
    chart_id: str
    line_id: str


@dataclass
class RectAnnotation:
    """Persisted rectangle annotation for charts in an AnalysisView."""
    pos_si: tuple[float, float]
    size_si: tuple[float, float]
    color: str
    chart_id: str
    rect_id: str
