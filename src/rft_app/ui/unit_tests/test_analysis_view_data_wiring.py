"""SSOT AnalysisObject dataset → AnalysisView → FilterableTable → charts."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from PyQt6.QtWidgets import QApplication, QWidget

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from model.canonical_names import (  # noqa: E402
    CANONICAL_EXCESS_PRESSURE,
    CANONICAL_FORMATION_PRESSURE,
    CANONICAL_VERTICAL_DEPTH,
    )
from model.data_models import (  # noqa: E402
    AnalysisObject,
    AnalysisView,
    ColumnSpec,
    DataSet,
    )
from project.manager import ProjectDataManager  # noqa: E402
from ui.analysis_view.analysis_view_data_manager import (  # noqa: E402
    insert_excess_pressure_column,
    )
from ui.analysis_view.analysis_view_widget import AnalysisViewWidget  # noqa: E402
from ui.filterable_table.custom_table_view import CustomTableView  # noqa: E402
from ui.filterable_table.filterable_table import FilterableTable  # noqa: E402
from ui.filterable_table.pandas_table_model import PandasTableModel  # noqa: E402
from ui.filterable_table.proxy_model import ProxyFilterModel  # noqa: E402
from ui.main_window.project_signals import ProjectSignals  # noqa: E402
from units.units_manager import SI_UNITS  # noqa: E402


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def analysis_view_widget(qapp: QApplication):
    project = ProjectDataManager()
    project.current_unit_system = SI_UNITS

    df = pd.DataFrame(
        {
            CANONICAL_VERTICAL_DEPTH: [1000.0, 1500.0, 2000.0],
            CANONICAL_FORMATION_PRESSURE: [1.0e7, 1.5e7, 2.0e7],
            "Well": ["A", "A", "B"],
            }
        )
    column_specs = [
        ColumnSpec(CANONICAL_VERTICAL_DEPTH, "length", "m"),
        ColumnSpec(CANONICAL_FORMATION_PRESSURE, "pressure", "Pa"),
        ColumnSpec("Well", "well", ""),
        ]

    dataset = DataSet(name="KD Fixture Dataset", dataframe=df, column_specs=column_specs)
    analysis = AnalysisObject(name="KD Analysis", analysis_dataset=dataset)
    project.analyses.append(analysis)

    view_df = dataset.dataframe.copy()
    view_specs = list(dataset.column_specs)
    view_df, view_specs = insert_excess_pressure_column(view_df, view_specs, project)

    view = AnalysisView(
        name="KD View",
        analysis_object=analysis,
        df=view_df,
        column_specs=view_specs,
        )
    analysis.analysis_views.append(view)

    signals = ProjectSignals()
    parent = QWidget()
    widget = AnalysisViewWidget(
        parent=parent,
        project=project,
        analysis=analysis,
        analysis_view_object=view,
        signals=signals,
        )
    parent.show()
    qapp.processEvents()

    yield project, analysis, view, widget

    parent.close()
    parent.deleteLater()
    qapp.processEvents()


def test_analysis_ssot_wired_to_view_table_and_plots(
    analysis_view_widget,
    qapp: QApplication,
    ) -> None:
    _project, analysis, view, widget = analysis_view_widget

    # Attribute rename / wiring on the view widget
    assert isinstance(widget.filterable_table, FilterableTable)
    assert isinstance(widget.filterable_table.custom_table_view, CustomTableView)
    assert isinstance(
        widget.filterable_table.custom_table_view.pandas_model,
        PandasTableModel,
        )
    assert isinstance(
        widget.filterable_table.custom_table_view.proxy_model,
        ProxyFilterModel,
        )
    assert widget.proxy is widget.filterable_table.custom_table_view.proxy_model

    # Analysis SSOT → view projection
    ssot = analysis.analysis_dataset
    assert ssot is not None
    assert list(ssot.dataframe.columns) == [
        CANONICAL_VERTICAL_DEPTH,
        CANONICAL_FORMATION_PRESSURE,
        "Well",
        ]
    assert CANONICAL_EXCESS_PRESSURE in view.df.columns
    assert list(view.df[CANONICAL_VERTICAL_DEPTH]) == list(
        ssot.dataframe[CANONICAL_VERTICAL_DEPTH]
        )
    assert list(view.df[CANONICAL_FORMATION_PRESSURE]) == list(
        ssot.dataframe[CANONICAL_FORMATION_PRESSURE]
        )

    # Filterable table + models hold the view df
    ft = widget.filterable_table
    ctv = ft.custom_table_view
    assert ft.df is view.df or ft.df.equals(view.df)
    assert ctv.df.equals(view.df)
    assert ctv.pandas_model.df.equals(view.df)
    assert ctv.pandas_model.rowCount() == len(view.df)
    assert widget.proxy.rowCount() == len(view.df)

    # Plots receive the proxy-visible dataframe
    visible = widget.extract_visible_df_from_proxy()
    assert len(visible) == len(view.df)
    pressure_chart = widget.graphical_frame.pressure_chart
    xs_chart = widget.graphical_frame.xs_pressure_chart
    assert pressure_chart.df is not None
    assert xs_chart.df is not None
    assert pressure_chart.df.equals(visible)
    assert xs_chart.df.equals(visible)
    assert len(pressure_chart.all_scatter_plot_items) >= 1
