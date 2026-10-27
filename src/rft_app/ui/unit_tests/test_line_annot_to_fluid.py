"""LineAnnot → Fluid conversion via NewFluidDialog."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from model.canonical_names import (  # noqa: E402
    CANONICAL_FORMATION_PRESSURE,
    CANONICAL_VERTICAL_DEPTH,
)
from model.data_models import AnalysisObject, AnalysisView, ColumnSpec  # noqa: E402
from model.view_state import StraightLineAnnotation  # noqa: E402
from project.manager import ProjectDataManager  # noqa: E402
from ui.analysis_view.new_fluid_dialog import NewFluidDialog  # noqa: E402
from ui.depth_gradient_chart.depth_gradient_chart import DepthGradientChart  # noqa: E402
from ui.depth_gradient_chart.line_annot import LineAnnot  # noqa: E402
from ui.main_window.project_signals import ProjectSignals  # noqa: E402
from units.units_manager import SI_UNITS  # noqa: E402

# Pressure (Pa) / depth (m): gradient = 10_000 Pa/m, zero-pressure depth = 0 m
START_SI = (10_000_000.0, 1_000.0)
END_SI = (20_000_000.0, 2_000.0)
EXPECTED_GRADIENT_SI = 10_000.0
EXPECTED_ZPD_SI = 0.0


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _fake_view_widget() -> SimpleNamespace:
    tree_item = SimpleNamespace(
        setCheckState=lambda _col, _state: None,
        )
    tree = SimpleNamespace(
        findItems=lambda _name, _flag: [tree_item],
        )
    combo = SimpleNamespace(
        findText=lambda _name: 0,
        setCurrentIndex=lambda _idx: None,
        )
    sidebar = SimpleNamespace(
        active_fluid_combo=combo,
        visible_fluids_tree=tree,
        )
    return SimpleNamespace(
        new_fluid_dialog=None,
        graphical_sidebar=sidebar,
        )


@pytest.fixture
def chart_with_line(qapp: QApplication):
    project = ProjectDataManager()
    project.current_unit_system = SI_UNITS

    analysis = AnalysisObject(name="KD Analysis")
    project.analyses.append(analysis)

    col_specs = [
        ColumnSpec(CANONICAL_FORMATION_PRESSURE, "pressure", "Pa"),
        ColumnSpec(CANONICAL_VERTICAL_DEPTH, "length", "m"),
        ]
    view = AnalysisView(
        name="KD View",
        analysis_object=analysis,
        column_specs=col_specs,
        )
    analysis.analysis_views.append(view)

    signals = ProjectSignals()
    parent = QWidget()
    chart = DepthGradientChart(
        parent=parent,
        view=view,
        project=project,
        signals=signals,
        x_axis=CANONICAL_FORMATION_PRESSURE,
        col_specs=col_specs,
        chart_id="pressure_plot",
        )

    line = LineAnnot(
        parent=chart,
        signals=signals,
        starting_point=START_SI,
        end_point=END_SI,
        points_are_si=True,
        )
    line.view_widget = _fake_view_widget()
    chart.addItem(line)
    chart.all_lines.append(line)
    line.refresh_geometry()

    annotation = StraightLineAnnotation(
        start_si=START_SI,
        end_si=END_SI,
        color="black",
        chart_id=chart.chart_id,
        line_id=line.id,
        )
    view.annotations.append(annotation)

    yield project, analysis, view, chart, line

    parent.close()
    parent.deleteLater()


def test_convert_line_to_fluid_opens_dialog_with_si_values(
    chart_with_line,
    qapp: QApplication,
    ) -> None:
    _project, _analysis, _view, _chart, line = chart_with_line

    line._convert_line_to_fluid()
    qapp.processEvents()

    dlg = line.view_widget.new_fluid_dialog
    assert isinstance(dlg, NewFluidDialog)
    assert dlg.base_line is line
    assert dlg.pressure_gradient_si == pytest.approx(EXPECTED_GRADIENT_SI)
    assert dlg.zero_pressure_depth_si == pytest.approx(EXPECTED_ZPD_SI)
    assert dlg.gradient_units_combo.count() > 0
    assert dlg.zero_pressure_depth_units_combo.count() > 0

    dlg.close()
    qapp.processEvents()


def test_accept_new_fluid_from_line_adds_fluid_and_removes_line(
    chart_with_line,
    qapp: QApplication,
    ) -> None:
    project, analysis, view, chart, line = chart_with_line
    line_id = line.id

    line._convert_line_to_fluid()
    qapp.processEvents()
    dlg = line.view_widget.new_fluid_dialog
    assert dlg is not None

    dlg.name_line_edit.setText("KD Water")
    dlg._on_accept()
    qapp.processEvents()

    assert len(analysis.fluids) == 1
    fluid = analysis.fluids[0]
    assert fluid.name == "KD Water"
    assert fluid.gradient_si == pytest.approx(EXPECTED_GRADIENT_SI)
    assert fluid.zero_pressure_depth_si == pytest.approx(EXPECTED_ZPD_SI)
    assert fluid.plotting_depth_min_si == pytest.approx(1_000.0)
    assert fluid.plotting_depth_max_si == pytest.approx(2_000.0)
    assert fluid.analysis_object is analysis

    assert all(item.id != line_id for item in chart.all_lines)
    assert all(
        not isinstance(a, StraightLineAnnotation) or a.line_id != line_id
        for a in view.annotations
        )
    assert project.is_modified
