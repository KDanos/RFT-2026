"""Unit tests for model.view_state."""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from model.fluid_model import Fluid, FluidContact  # noqa: E402
from model.view_state import (  # noqa: E402
    RectAnnotation,
    StraightLineAnnotation,
    ViewWidgetSidebar,
    )


def _make_fluid(name: str) -> Fluid:
    return Fluid(
        name=name,
        type="Water",
        gradient_si=10000.0,
        zero_pressure_depth_si=0.0,
        bottom_contact=FluidContact(),
        plotting_depth_min_si=100.0,
        plotting_depth_max_si=200.0,
        )


def test_view_widget_sidebar_defaults() -> None:
    sidebar = ViewWidgetSidebar()
    assert sidebar.ref_fluid is None
    assert sidebar.active_fluid is None
    assert sidebar.visible_fluids == []
    assert sidebar.primary_series_identifier == "None"
    assert sidebar.secondary_series_identifier == "None"


def test_view_widget_sidebar_holds_fluid_refs() -> None:
    fluid = _make_fluid("Shallow Water")
    sidebar = ViewWidgetSidebar(
        ref_fluid=fluid,
        active_fluid=fluid,
        visible_fluids=[fluid],
        primary_series_identifier="Well",
        )
    assert sidebar.ref_fluid is fluid
    assert sidebar.active_fluid is fluid
    assert sidebar.visible_fluids == [fluid]
    assert sidebar.primary_series_identifier == "Well"


def test_pickle_roundtrip_view_state() -> None:
    fluid = _make_fluid("Shallow Water")
    sidebar = ViewWidgetSidebar(active_fluid=fluid, visible_fluids=[fluid])
    line = StraightLineAnnotation(
        start_si=(0.0, 1.0),
        end_si=(2.0, 3.0),
        color="black",
        chart_id="pressure",
        line_id="L1",
        )
    rect = RectAnnotation(
        pos_si=(0.0, 0.0),
        size_si=(1.0, 1.0),
        color="green",
        chart_id="pressure",
        rect_id="R1",
        )

    sidebar2 = pickle.loads(pickle.dumps(sidebar))
    line2 = pickle.loads(pickle.dumps(line))
    rect2 = pickle.loads(pickle.dumps(rect))

    assert sidebar2.active_fluid.name == "Shallow Water"
    assert line2.line_id == "L1"
    assert rect2.rect_id == "R1"
    assert type(sidebar2).__module__ == "model.view_state"
