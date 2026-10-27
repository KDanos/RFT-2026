"""Load (project data loader), rename, merge, and new-analysis workflow.

Hard-copy fixtures under ``unit_tests/fixtures/`` (snapshotted from
``Design Assets/Raw Data/19.10.25 Dummy Data KD.xlsx``).
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from model.canonical_names import (  # noqa: E402
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
from project.persistence import save_project  # noqa: E402
from ui.analysis_view import insert_excess_pressure_column  # noqa: E402
from ui.project_data_loader.project_data_loader_management import (  # noqa: E402
    check_against_canonical_names,
    populate_data_rows,
    )
from units.units_manager import FIELD_UNITS, UnitSystem  # noqa: E402
from units.units_normalisation import identify_si_storage_unit  # noqa: E402
from utilities import unique_name  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Column definitions for each fixture TSV: (header, quantity_key, user_unit)
ORIGINAL_COLUMNS = [
    ("TVDSL", "length", "m"),
    ("Formation Pressure", "pressure", "psi"),
    ("Excess Pressure", "pressure", "psi"),
    ("Mobility", "mobility", "mD/cP"),
    ("Result", "text", ""),
    ("Comments", "text", ""),
    ("MD", "length", "m"),
    ("Run", "text", ""),
    ("Temperature", "temperature", "°C"),
    ("Well", "well", ""),
]
CONVERSION_COLUMNS = [
    ("Depth", "length", "ft"),
    ("Pressure", "pressure", "psi"),
    ("Weight", "mass", "lbm"),
]
MODIFIED_COLUMNS = [
    ("Depth (TVD)", "length", "m"),
    ("Form. Pr.", "pressure", "psi"),
    ("Excess Pressure", "pressure", "psi"),
    ("Mobility", "mobility", "mD/cP"),
    ("Result", "text", ""),
    ("Comments", "text", ""),
    ("Measured Depth", "length", "m"),
    ("Run", "text", ""),
    ("Temperature", "temperature", "°C"),
    ("Well Name", "well", ""),
]

MOD_COLUMNS_AFTER_IGNORE = [
    "Depth (TVD)",
    "Form. Pr.",
    "Excess Pressure (user import)",
    "Mobility",
    "Measured Depth",
    "Run",
    "Temperature",
    "Well Name",
]

PRESSURE_COL = "Formation Pressure (user import)"
EXCESS_COL = "Excess Pressure (user import)"

MERGED_HEADERS = [
    "TVDSS",
    PRESSURE_COL,
    EXCESS_COL,
    "Mobility",
    "Result",
    "Comments",
    "Meas. Depth",
    "Run",
    "Temperature",
    "Well",
]

MERGE_MAPPING = {
    "TVDSS": {
        "Original Pressure Data": "TVDSL",
        "Mod. Data": "Depth (TVD)",
    },
    PRESSURE_COL: {
        "Original Pressure Data": PRESSURE_COL,
        "Mod. Data": "Form. Pr.",
    },
    EXCESS_COL: {
        "Original Pressure Data": EXCESS_COL,
        "Mod. Data": EXCESS_COL,
    },
    "Mobility": {
        "Original Pressure Data": "Mobility",
        "Mod. Data": "Mobility",
    },
    "Result": {
        "Original Pressure Data": "Result",
        "Mod. Data": "",
    },
    "Comments": {
        "Original Pressure Data": "Comments",
        "Mod. Data": "",
    },
    "Meas. Depth": {
        "Original Pressure Data": "MD",
        "Mod. Data": "Measured Depth",
    },
    "Run": {
        "Original Pressure Data": "Run",
        "Mod. Data": "Run",
    },
    "Temperature": {
        "Original Pressure Data": "Temperature",
        "Mod. Data": "Temperature",
    },
    "Well": {
        "Original Pressure Data": "Well",
        "Mod. Data": "Well Name",
    },
}

MERGE_QUANTITY_KEYS = [
    "length",
    "pressure",
    "pressure",
    "mobility",
    "text",
    "text",
    "length",
    "text",
    "temperature",
    "well",
]


def _read_tsv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows:
        raise ValueError(f"Empty fixture: {path}")
    return rows[0], rows[1:]


def load_via_project_data_loader(
    project: ProjectDataManager,
    *,
    fixture_path: Path,
    column_defs: list[tuple[str, str, str]],
    name: str,
    ignore_columns: set[str] | None = None,
    ) -> DataSet:
    """Mirror DataLoaderDialogProject import without the Qt mapping table.

    Uses ``populate_data_rows`` (SI normalisation + logging) then
    ``ProjectDataManager.add_loaded_dataset``.
    """
    ignore_columns = ignore_columns or set()
    headers, data_rows = _read_tsv(fixture_path)
    assert headers == [c[0] for c in column_defs], (
        f"Fixture headers {headers} do not match column defs "
        f"{[c[0] for c in column_defs]}"
    )

    kept = [
        (i, name_, qty, unit)
        for i, (name_, qty, unit) in enumerate(column_defs)
        if name_ not in ignore_columns
    ]
    # mapping_table columns are 1-based (col 0 is the ignore checkbox column)
    selected_mapping_columns = [i + 1 for i, *_ in kept]
    column_names: list[str] = []
    for _, name_, _, _ in kept:
        column_names.append(
            unique_name(check_against_canonical_names(name_), column_names)
        )

    imported_specs = [
        ColumnSpec(col_name, qty, unit)
        for (_, _, qty, unit), col_name in zip(kept, column_names)
    ]
    rows, info_log = populate_data_rows(
        data_rows,
        set(),
        selected_mapping_columns,
        imported_specs,
    )
    df = pd.DataFrame(rows, columns=column_names).dropna(how="all").reset_index(drop=True)

    stored_specs = [
        ColumnSpec(spec.name, spec.quantity_key, identify_si_storage_unit(spec.quantity_key) or spec.unit)
        for spec in imported_specs
    ]
    chosen = project.add_loaded_dataset(
        df,
        stored_specs,
        name,
        info_log=info_log,
        user_comment=None,
    )
    return project.get_dataset_by_name(chosen)


def rename_dataset(project: ProjectDataManager, old_name: str, new_name: str) -> DataSet:
    dataset = project.get_dataset_by_name(old_name)
    existing = {ds.name for ds in project.all_datasets if ds is not dataset}
    dataset.name = unique_name(new_name.strip() or old_name, existing)
    return dataset


def merge_datasets(
    project: ProjectDataManager,
    *,
    base: DataSet,
    other: DataSet,
    mapping: dict[str, dict[str, str]],
    quantity_keys: list[str],
    out_name: str,
    ) -> DataSet:
    """Same column-mapping concat as MergeDatasetsDialog._create_combined_dataframe."""
    headers = list(mapping.keys())
    blocks: list[pd.DataFrame] = []
    for ds in (base, other):
        block = pd.DataFrame(index=ds.dataframe.index, columns=headers)
        for header in headers:
            source_col = mapping[header].get(ds.name, "")
            if source_col:
                block[header] = ds.dataframe[source_col].values
            else:
                block[header] = np.nan
        blocks.append(block)
    merged_df = pd.concat(blocks, ignore_index=True)
    specs = [
        ColumnSpec(header, quantity_keys[i], identify_si_storage_unit(quantity_keys[i]))
        for i, header in enumerate(headers)
    ]
    chosen = unique_name(out_name, {ds.name for ds in project.all_datasets})
    merged = DataSet(chosen, merged_df, specs)
    project.merged_datasets.append(merged)
    project.mark_modified()
    return merged


def create_analysis_from_dataset(
    project: ProjectDataManager,
    dataset: DataSet,
    *,
    analysis_name: str,
    vert_depth_src_col: str,
    formation_pres_src_col: str,
    ) -> AnalysisObject:
    """Mirror DataLoaderDialogAnalysis._create_analysis_object ordering/rename."""
    spec_by_name = {spec.name: spec for spec in dataset.column_specs}
    other_cols = [
        name
        for name in dataset.dataframe.columns
        if name not in (vert_depth_src_col, formation_pres_src_col)
    ]
    ordered = [vert_depth_src_col, formation_pres_src_col, *other_cols]
    df = dataset.dataframe[ordered].copy().rename(
        columns={
            vert_depth_src_col: CANONICAL_VERTICAL_DEPTH,
            formation_pres_src_col: CANONICAL_FORMATION_PRESSURE,
        }
    )
    new_specs: list[ColumnSpec] = []
    for col_name in df.columns:
        if col_name == CANONICAL_VERTICAL_DEPTH:
            old = spec_by_name[vert_depth_src_col]
            new_specs.append(ColumnSpec(CANONICAL_VERTICAL_DEPTH, old.quantity_key, old.unit))
        elif col_name == CANONICAL_FORMATION_PRESSURE:
            old = spec_by_name[formation_pres_src_col]
            new_specs.append(ColumnSpec(CANONICAL_FORMATION_PRESSURE, old.quantity_key, old.unit))
        else:
            new_specs.append(spec_by_name[col_name])

    analysis_ds = DataSet(analysis_name, df, new_specs)
    analysis = AnalysisObject(
        name=analysis_name,
        source_datasets=[dataset.name],
        analysis_dataset=analysis_ds,
        vert_depth_src_col=vert_depth_src_col,
        formation_pres_src_col=formation_pres_src_col,
    )
    project.analyses.append(analysis)
    project.mark_modified()
    return analysis


def create_konstantin_unit_system(project: ProjectDataManager) -> UnitSystem:
    """Field-based custom system: depth in m, temperature in °C; set as project default."""
    units = dict(FIELD_UNITS.units_by_quantity)
    units["length"] = "m"
    units["temperature"] = "°C"
    existing_names = [system.label for system in project.available_unit_systems]
    name = unique_name("Konstantin", existing_names)
    system = UnitSystem(key=name, label=name, units_by_quantity=units)
    project.user_unit_systems.append(system)
    project.current_unit_system = system
    project.mark_modified()
    return system


def create_default_analysis_view(
    project: ProjectDataManager,
    analysis: AnalysisObject,
    *,
    view_name: str = "New View",
    ) -> AnalysisView:
    """Mirror MainWindow._create_default_analysis_view (single view)."""
    dataset = analysis.analysis_dataset
    df = (
        dataset.dataframe.copy()
        if dataset is not None and dataset.dataframe is not None
        else None
    )
    column_specs = list(dataset.column_specs) if dataset is not None else []
    df, column_specs = insert_excess_pressure_column(df, column_specs, project)

    view = AnalysisView(
        name=view_name,
        analysis_object=analysis,
        df=df,
        column_specs=column_specs,
    )
    analysis.analysis_views.append(view)
    project.mark_modified()
    return view


#--------Pytest fixtures (pipeline stages)--------

@pytest.fixture
def empty_project() -> ProjectDataManager:
    return ProjectDataManager()


@pytest.fixture
def project_with_konstantin_units(empty_project: ProjectDataManager) -> ProjectDataManager:
    create_konstantin_unit_system(empty_project)
    return empty_project


@pytest.fixture
def project_with_loaded_datasets(
    project_with_konstantin_units: ProjectDataManager,
    ) -> ProjectDataManager:
    project = project_with_konstantin_units
    load_via_project_data_loader(
        project,
        fixture_path=FIXTURES / "original_data.tsv",
        column_defs=ORIGINAL_COLUMNS,
        name="Original Data",
    )
    rename_dataset(project, "Original Data", "Base Data")

    load_via_project_data_loader(
        project,
        fixture_path=FIXTURES / "conversion_data.tsv",
        column_defs=CONVERSION_COLUMNS,
        name="Conversion Data",
    )
    rename_dataset(project, "Conversion Data", "Conv. Data")

    load_via_project_data_loader(
        project,
        fixture_path=FIXTURES / "modified_data.tsv",
        column_defs=MODIFIED_COLUMNS,
        name="Mod. Data",
        ignore_columns={"Result", "Comments"},
    )
    rename_dataset(project, "Base Data", "Original Pressure Data")
    return project


@pytest.fixture
def project_with_merged_dataset(
    project_with_loaded_datasets: ProjectDataManager,
    ) -> ProjectDataManager:
    project = project_with_loaded_datasets
    original = project.get_dataset_by_name("Original Pressure Data")
    mod = project.get_dataset_by_name("Mod. Data")
    merge_datasets(
        project,
        base=original,
        other=mod,
        mapping=MERGE_MAPPING,
        quantity_keys=MERGE_QUANTITY_KEYS,
        out_name="Merged Pressure Data",
    )
    return project


@pytest.fixture
def project_with_analysis(
    project_with_merged_dataset: ProjectDataManager,
    ) -> ProjectDataManager:
    project = project_with_merged_dataset
    merged = project.get_dataset_by_name("Merged Pressure Data")
    analysis = create_analysis_from_dataset(
        project,
        merged,
        analysis_name="Pressure Analysis",
        vert_depth_src_col="TVDSS",
        formation_pres_src_col=PRESSURE_COL,
    )
    create_default_analysis_view(project, analysis)
    return project


#--------Tests--------

def test_create_konstantin_unit_system(
    project_with_konstantin_units: ProjectDataManager,
    ) -> None:
    project = project_with_konstantin_units
    system = project.current_unit_system
    assert system in project.user_unit_systems
    assert system.label == "Konstantin"
    assert system.units_by_quantity["length"] == "m"
    assert system.units_by_quantity["temperature"] == "°C"
    assert system.units_by_quantity["pressure"] == FIELD_UNITS.units_by_quantity["pressure"]


def test_load_and_rename_datasets(
    project_with_loaded_datasets: ProjectDataManager,
    ) -> None:
    project = project_with_loaded_datasets
    assert [ds.name for ds in project.loaded_datasets] == [
        "Original Pressure Data",
        "Conv. Data",
        "Mod. Data",
    ]

    original = project.get_dataset_by_name("Original Pressure Data")
    mod = project.get_dataset_by_name("Mod. Data")
    conv = project.get_dataset_by_name("Conv. Data")

    assert len(original.dataframe) == 407
    assert len(mod.dataframe) == 407
    assert len(conv.dataframe) == 3
    assert "Result" in [s.name for s in original.column_specs]
    assert "Comments" in [s.name for s in original.column_specs]
    assert "Run" in [s.name for s in mod.column_specs]
    assert [s.name for s in mod.column_specs] == MOD_COLUMNS_AFTER_IGNORE
    assert [s.name for s in conv.column_specs] == ["Depth", "Pressure", "Weight"]
    assert PRESSURE_COL in original.dataframe.columns


def test_merge_original_and_mod_datasets(
    project_with_merged_dataset: ProjectDataManager,
    ) -> None:
    project = project_with_merged_dataset
    original = project.get_dataset_by_name("Original Pressure Data")
    mod = project.get_dataset_by_name("Mod. Data")
    merged = project.get_dataset_by_name("Merged Pressure Data")

    assert merged in project.merged_datasets
    assert list(merged.dataframe.columns) == MERGED_HEADERS
    assert len(merged.dataframe) == len(original.dataframe) + len(mod.dataframe) == 814
    assert merged.dataframe["TVDSS"].notna().all()
    assert merged.dataframe[PRESSURE_COL].notna().any()

    mod_block = merged.dataframe.iloc[len(original.dataframe) :]
    assert mod_block["Meas. Depth"].notna().any()
    assert mod_block["Run"].notna().any()
    assert (mod_block["Well"] == "Aw1").any()
    assert mod_block["Result"].isna().all()
    assert mod_block["Comments"].isna().all()


def test_create_analysis_with_default_view(
    project_with_analysis: ProjectDataManager,
    ) -> None:
    project = project_with_analysis
    merged = project.get_dataset_by_name("Merged Pressure Data")
    assert len(project.analyses) == 1
    analysis = project.analyses[0]

    assert analysis.name == "Pressure Analysis"
    assert analysis.source_datasets == ["Merged Pressure Data"]
    assert analysis.vert_depth_src_col == "TVDSS"
    assert analysis.formation_pres_src_col == PRESSURE_COL
    assert list(analysis.analysis_dataset.dataframe.columns[:2]) == [
        CANONICAL_VERTICAL_DEPTH,
        CANONICAL_FORMATION_PRESSURE,
    ]
    assert len(analysis.analysis_dataset.dataframe) == len(merged.dataframe)
    assert len(analysis.analysis_views) == 1
    view = analysis.analysis_views[0]
    assert view.name == "New View"
    assert view.df is not None
    assert len(view.df) == len(merged.dataframe)


def test_save_completed_workflow_project(
    project_with_analysis: ProjectDataManager,
    ) -> None:
    project = project_with_analysis
    stamp = date.today().strftime("%y%m%d")
    base_stem = f"{stamp} Tested Data Load Merge and New Analysis KD"
    existing_stems = {path.stem for path in APP_ROOT.glob("*.rftproj")}
    save_stem = unique_name(base_stem, existing_stems)
    save_path = APP_ROOT / f"{save_stem}.rftproj"
    save_project(project, save_path)
    assert save_path.is_file()
    assert "KD" in save_path.stem
    assert save_stem == base_stem or save_stem.startswith(f"{base_stem}_")
