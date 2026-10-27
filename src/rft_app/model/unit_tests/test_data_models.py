"""Unit tests for model.data_models."""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import pytest

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from model.data_models import AnalysisObject, AnalysisView, ColumnSpec  # noqa: E402
from model.fluid_model import Fluid, FluidContact  # noqa: E402
from model.view_state import ViewWidgetSidebar  # noqa: E402


def _make_fluid(name: str, fluid_type: str = "Water") -> Fluid:
    return Fluid(
        name=name,
        type=fluid_type,
        gradient_si=10000.0,
        zero_pressure_depth_si=0.0,
        bottom_contact=FluidContact(),
        plotting_depth_min_si=100.0,
        plotting_depth_max_si=200.0,
        )


def test_column_spec_frozen() -> None:
    spec = ColumnSpec(name="TVDSL", quantity_key="length", unit="m")
    with pytest.raises(Exception):
        spec.name = "Other"  # type: ignore[misc]


def test_analysis_view_defaults_and_link() -> None:
    analysis = AnalysisObject(name="BTC")
    view = AnalysisView(name="View 1", analysis_object=analysis)
    analysis.analysis_views.append(view)

    assert view.sidebar is not None
    assert isinstance(view.sidebar, ViewWidgetSidebar)
    assert view.annotations == []
    assert analysis.is_visible is True

    view.is_visible = False
    assert analysis.is_visible is False


def test_delete_fluid_removes_fluid_and_clears_contacts() -> None:
    analysis = AnalysisObject(name="BTC")
    shallow = _make_fluid("Shallow Water")
    deep = _make_fluid("Deep Water")
    shallow.bottom_contact.top_fluid = shallow
    shallow.bottom_contact.bottom_fluid = deep
    shallow.bottom_contact.exists = True
    shallow.bottom_contact.depth = 150.0
    shallow.bottom_contact.pressure = 1.0e6
    shallow.analysis_object = analysis
    deep.analysis_object = analysis
    analysis.fluids = [shallow, deep]

    view = AnalysisView(name="V1", analysis_object=analysis)
    view.sidebar.visible_fluids = [shallow, deep]
    view.sidebar.active_fluid = deep
    view.sidebar.ref_fluid = deep
    analysis.analysis_views.append(view)

    analysis.delete_fluid(deep)

    assert deep not in analysis.fluids
    assert analysis.fluids == [shallow]
    assert shallow.bottom_contact.bottom_fluid is None
    assert shallow.bottom_contact.exists is False
    assert deep not in view.sidebar.visible_fluids
    assert view.sidebar.active_fluid is None
    assert view.sidebar.ref_fluid is None


def test_pickle_roundtrip_analysis_object() -> None:
    analysis = AnalysisObject(name="BTC")
    fluid = _make_fluid("Shallow Water")
    fluid.analysis_object = analysis
    analysis.fluids.append(fluid)
    view = AnalysisView(name="V1", analysis_object=analysis)
    view.sidebar.visible_fluids.append(fluid)
    view.sidebar.active_fluid = fluid
    analysis.analysis_views.append(view)

    restored = pickle.loads(pickle.dumps(analysis))
    assert restored.name == "BTC"
    assert len(restored.fluids) == 1
    assert restored.fluids[0].name == "Shallow Water"
    assert restored.analysis_views[0].sidebar.active_fluid.name == "Shallow Water"
    assert type(restored).__module__ == "model.data_models"
