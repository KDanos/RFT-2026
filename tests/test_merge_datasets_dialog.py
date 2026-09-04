"""Tests for MergeDatasetsDialog against 260903 Merging Data.rftproj fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QComboBox, QDialog, QLabel, QMessageBox

APP_ROOT = Path(__file__).resolve().parents[1] / "src" / "rft_app"
sys.path.insert(0, str(APP_ROOT))

from project import ProjectDataManager  # noqa: E402
from project.persistence import load_project  # noqa: E402
from project.models import DataSet  # noqa: E402
from ui.main_window.sidebar.all_datasets_tree import AllDataSetsTree  # noqa: E402
from ui.main_window.sidebar.merge_datasets_dialog import MergeDatasetsDialog  # noqa: E402

PROJECT_PATH = APP_ROOT / "260903 Merging Data.rftproj"

MERGE_INSUFFICIENT_DATASETS_MESSAGE = (
    "There must be at least 2 loaded or merged datasets available\n"
    "Please load more data via the 'Load Data' module first."
)

ORIGINAL_SPECS: list[tuple[str, str, str | None]] = [
    ("TVDSL", "length", "m"),
    ("Formation Pressure (user import)", "pressure", "psi"),
    ("Excess Pressure (user import)", "pressure", "psi"),
    ("Mobility", "mobility", "mD/cP"),
    ("Result", "text", ""),
    ("Comments", "text", ""),
    ("MD", "length", "m"),
    ("Run", "text", ""),
    ("Temperature", "temperature", "°C"),
    ("Well", "well", ""),
]

CONVERSION_SPECS: list[tuple[str, str, str | None]] = [
    ("Depth", "length", "ft"),
    ("Pressure", "pressure", "psi"),
    ("Weight", "mass", "lbm"),
]

MODIFIED_SPECS: list[tuple[str, str, str | None]] = [
    ("Depth (TVD)", "length", "m"),
    ("Form. Pr.", "pressure", "psi"),
    ("Excess Pressure (user import)", "pressure", "psi"),
    ("Mobility", "mobility", "mD/cP"),
    ("Comments", "text", ""),
    ("Measured Depth", "length", "m"),
    ("Temperature", "temperature", "°C"),
    ("Well Name", "well", ""),
]

COLOR_SPECS: list[tuple[str, str, str | None]] = [
    ("TVDSL", "length", "m"),
    ("Formation Pressure (user import)", "pressure", "bar"),
]

DATASET_SPECS = {
    "Original Data": ORIGINAL_SPECS,
    "Conversion Data": CONVERSION_SPECS,
    "Modified Data": MODIFIED_SPECS,
    "Color Data": COLOR_SPECS,
}

COL = MergeDatasetsDialog


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def merge_project():
    project = load_project(PROJECT_PATH)
    # Keep dialog tests focused on the four loaded datasets.
    project.merged_datasets = []
    assert len(project.loaded_datasets) == 4
    names = [ds.name for ds in project.loaded_datasets]
    assert names == list(DATASET_SPECS.keys())
    return project


@pytest.fixture
def dialog(qapp, merge_project):
    dlg = MergeDatasetsDialog(project=merge_project)
    dlg.show()
    qapp.processEvents()
    yield dlg
    dlg.close()
    qapp.processEvents()


def header_combo(dlg: MergeDatasetsDialog, col: int) -> QComboBox:
    item = dlg.main_layout.itemAtPosition(1, col)
    assert item is not None
    widget = item.widget()
    assert isinstance(widget, QComboBox)
    return widget


def mapping_combos(dlg: MergeDatasetsDialog, col: int) -> list[tuple[int, QComboBox]]:
    combos: list[tuple[int, QComboBox]] = []
    for row in range(COL.FIRST_DATA_ROW, dlg.main_layout.rowCount()):
        item = dlg.main_layout.itemAtPosition(row, col)
        if item is None:
            continue
        widget = item.widget()
        if isinstance(widget, QComboBox):
            combos.append((row, widget))
    return combos


def quantity_labels(dlg: MergeDatasetsDialog) -> list[tuple[int, QLabel]]:
    labels: list[tuple[int, QLabel]] = []
    for row in range(COL.FIRST_DATA_ROW, dlg.main_layout.rowCount()):
        item = dlg.main_layout.itemAtPosition(row, COL.COL_QUANTITY)
        if item is None:
            continue
        widget = item.widget()
        if isinstance(widget, QLabel):
            labels.append((row, widget))
    return labels


def select_header_dataset(
    dlg: MergeDatasetsDialog, col: int, dataset_name: str, qapp: QApplication
    ) -> None:
    combo = header_combo(dlg, col)
    idx = combo.findText(dataset_name)
    assert idx >= 0, (
        f"{dataset_name!r} not in col {col} options: "
        f"{[combo.itemText(i) for i in range(combo.count())]}"
    )
    combo.setCurrentIndex(idx)
    qapp.processEvents()


def assert_dataset_specs_match(
    ds: DataSet, expected: list[tuple[str, str, str | None]]
    ) -> None:
    assert len(ds.column_specs) == len(expected)
    for spec, (name, key, unit) in zip(ds.column_specs, expected):
        assert spec.name == name
        assert spec.quantity_key == key
        assert spec.unit == unit


def setup_three_merge_columns(
    dlg: MergeDatasetsDialog, qapp: QApplication
    ) -> None:
    dlg.base_set_combo.setCurrentIndex(dlg.base_set_combo.findText("Modified Data"))
    qapp.processEvents()
    select_header_dataset(dlg, COL.COL_FIRST_MERGE, "Original Data", qapp)
    select_header_dataset(dlg, COL.COL_FIRST_MERGE + 1, "Conversion Data", qapp)
    select_header_dataset(dlg, COL.COL_FIRST_MERGE + 2, "Color Data", qapp)


@pytest.mark.parametrize("dataset_count", [0, 1])
def test_merge_datasets_blocks_when_fewer_than_two_datasets(
    qapp, merge_project, monkeypatch, dataset_count: int
) -> None:
    """Merge menu action shows a critical message and does not open the dialog."""
    project = ProjectDataManager()
    project.loaded_datasets = merge_project.loaded_datasets[:dataset_count]

    tree = AllDataSetsTree(project.loaded_datasets, project=project)
    captured: dict[str, object] = {}
    dialog_constructed: list[bool] = []

    def fake_critical(parent, title, text):
        captured["parent"] = parent
        captured["title"] = title
        captured["text"] = text
        return QMessageBox.StandardButton.Ok

    def fake_dialog_constructor(parent, project):
        dialog_constructed.append(True)
        raise AssertionError("MergeDatasetsDialog should not be created")

    monkeypatch.setattr(
        "ui.main_window.sidebar.all_datasets_tree.QMessageBox.critical",
        fake_critical,
    )
    monkeypatch.setattr(
        "ui.main_window.sidebar.all_datasets_tree.MergeDatasetsDialog",
        fake_dialog_constructor,
    )

    tree._merge_datasets()
    qapp.processEvents()

    assert dialog_constructed == []
    assert captured["parent"] is tree
    assert captured["title"] == "Merge Datasets"
    assert captured["text"] == MERGE_INSUFFICIENT_DATASETS_MESSAGE


def test_merge_datasets_opens_dialog_when_two_or_more_datasets_exist(
    qapp, merge_project, monkeypatch
) -> None:
    tree = AllDataSetsTree(merge_project.loaded_datasets, project=merge_project)
    exec_calls: list[bool] = []
    critical_calls: list[bool] = []
    created_emits: list[bool] = []

    class FakeMergeDialog:
        def __init__(self, parent, project):
            self.parent = parent
            self.project = project

        def exec(self):
            exec_calls.append(True)
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr(
        "ui.main_window.sidebar.all_datasets_tree.MergeDatasetsDialog",
        FakeMergeDialog,
    )
    monkeypatch.setattr(
        "ui.main_window.sidebar.all_datasets_tree.QMessageBox.critical",
        lambda *_args, **_kwargs: critical_calls.append(True),
    )
    tree.merged_dataset_created.connect(lambda: created_emits.append(True))

    tree._merge_datasets()
    qapp.processEvents()

    assert critical_calls == []
    assert exec_calls == [True]
    assert created_emits == [True]


@pytest.mark.parametrize("dataset_name", DATASET_SPECS.keys())
def test_project_fixture_column_specs(merge_project, dataset_name: str) -> None:
    ds = next(d for d in merge_project.loaded_datasets if d.name == dataset_name)
    assert_dataset_specs_match(ds, DATASET_SPECS[dataset_name])


def test_base_column_labels_match_original_data(dialog: MergeDatasetsDialog) -> None:
    base = dialog.base_set_combo.currentData()
    assert base.name == "Original Data"
    for i, spec in enumerate(base.column_specs):
        row = i + COL.FIRST_DATA_ROW
        name_item = dialog.main_layout.itemAtPosition(row, COL.COL_BASE)
        qty_item = dialog.main_layout.itemAtPosition(row, COL.COL_QUANTITY)
        assert name_item is not None and qty_item is not None
        assert isinstance(name_item.widget(), QLabel)
        assert isinstance(qty_item.widget(), QLabel)
        assert name_item.widget().text() == spec.name


def test_first_merge_column_is_grid_index_first_merge(dialog: MergeDatasetsDialog) -> None:
    assert isinstance(
        dialog.main_layout.itemAtPosition(0, COL.COL_FIRST_MERGE).widget(), QLabel
    )
    assert isinstance(header_combo(dialog, COL.COL_FIRST_MERGE), QComboBox)


def test_first_merge_header_has_no_none_option(dialog: MergeDatasetsDialog) -> None:
    combo = header_combo(dialog, COL.COL_FIRST_MERGE)
    assert combo.itemText(0) != "None"


def test_second_merge_header_has_none_option(qapp, dialog: MergeDatasetsDialog) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Modified Data", qapp)
    combo = header_combo(dialog, COL.COL_FIRST_MERGE + 1)
    assert combo.itemText(0) == "None"


def test_available_datasets_excludes_base_and_left_merge_sets(
    qapp, dialog: MergeDatasetsDialog
) -> None:
    """Col 5 options exclude base and col 4 only — not datasets in cols to the right."""
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    available = dialog._update_list_of_available_datasets(
        exclude_col=COL.COL_FIRST_MERGE + 1
    )
    names = {ds.name for ds in available}
    assert "Original Data" not in names
    assert "Conversion Data" not in names
    assert {"Modified Data", "Color Data"} <= names


def test_first_merge_header_includes_datasets_from_right_columns(
    qapp, dialog: MergeDatasetsDialog
) -> None:
    """Col 4 must list all non-base datasets even when col 5 already has Color."""
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "Color Data", qapp)
    names = {
        ds.name
        for ds in dialog._update_list_of_available_datasets(exclude_col=COL.COL_FIRST_MERGE)
    }
    assert names == {"Conversion Data", "Modified Data", "Color Data"}
    first_merge_combo = header_combo(dialog, COL.COL_FIRST_MERGE)
    ui_names = {first_merge_combo.itemText(i) for i in range(first_merge_combo.count())}
    assert ui_names == names


def test_row_quantity_keys_start_as_base_keys(dialog: MergeDatasetsDialog) -> None:
    expected = [spec.quantity_key for spec in dialog.base_set_combo.currentData().column_specs]
    assert dialog.row_quantity_keys[:10] == expected


def test_first_merge_extends_rows_for_unused_specs(qapp, dialog: MergeDatasetsDialog) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    assert dialog.row_quantity_keys == [
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
        "mass",
    ]
    combos = mapping_combos(dialog, COL.COL_FIRST_MERGE)
    assert len(combos) == 11
    assert combos[-1][1].currentData().name == "Weight"


def test_modified_data_fits_base_rows_without_extra_mass(
    qapp, dialog: MergeDatasetsDialog
    ) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Modified Data", qapp)
    assert len(dialog.row_quantity_keys) == 10
    combos = mapping_combos(dialog, COL.COL_FIRST_MERGE)
    assert len(combos) == 10
    mapped = [c.currentData() for _row, c in combos if c.currentData() is not None]
    assert len(mapped) == 8
    assert {spec.name for spec in mapped} == {name for name, _k, _u in MODIFIED_SPECS}


def test_conversion_data_maps_depth_and_pressure_only(
    qapp, dialog: MergeDatasetsDialog
        ) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    combos = dict(mapping_combos(dialog, COL.COL_FIRST_MERGE))
    assert combos[COL.FIRST_DATA_ROW].currentData().name == "Depth"
    assert combos[COL.FIRST_DATA_ROW + 1].currentData().name == "Pressure"
    assert combos[COL.FIRST_DATA_ROW + 2].currentData() is None
    assert combos[COL.FIRST_DATA_ROW + 2].isVisible() is False


def test_modified_data_maps_all_eight_columns(qapp, dialog: MergeDatasetsDialog) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Modified Data", qapp)
    combos = dict(mapping_combos(dialog, COL.COL_FIRST_MERGE))
    mapped_names = {
        combos[row].currentData().name
        for row in combos
        if combos[row].currentData() is not None
    }
    assert mapped_names == {name for name, _key, _unit in MODIFIED_SPECS}
    assert sum(1 for row in combos if combos[row].currentData() is None) == 2


def test_later_merge_column_fills_existing_rows_only(
    qapp, dialog: MergeDatasetsDialog
    ) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Modified Data", qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "Color Data", qapp)
    combos = dict(mapping_combos(dialog, COL.COL_FIRST_MERGE + 1))
    assert combos[COL.FIRST_DATA_ROW].currentData().name == "TVDSL"
    assert combos[COL.FIRST_DATA_ROW + 1].currentData().name == "Formation Pressure (user import)"
    for row in range(COL.FIRST_DATA_ROW + 2, COL.FIRST_DATA_ROW + 10):
        assert combos[row].currentData() is None
        assert combos[row].isVisible() is False


def test_later_merge_column_row_count_matches_row_quantity_keys(
    qapp, dialog: MergeDatasetsDialog
        ) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "Color Data", qapp)
    combos = mapping_combos(dialog, COL.COL_FIRST_MERGE + 1)
    assert len(combos) == len(dialog.row_quantity_keys)


def test_clearing_second_merge_column_shrinks_quantity_labels(
    qapp, dialog: MergeDatasetsDialog
) -> None:
    """Col 5 = Original expands quantity rows; col 5 = None must shrink them back."""
    dialog.base_set_combo.setCurrentIndex(
        dialog.base_set_combo.findText("Color Data")
    )
    qapp.processEvents()

    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    assert dialog.row_quantity_keys == ["length", "pressure", "mass"]
    assert len(quantity_labels(dialog)) == 3

    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "Original Data", qapp)
    assert len(dialog.row_quantity_keys) == 11
    assert len(quantity_labels(dialog)) == 11
    assert len(mapping_combos(dialog, COL.COL_FIRST_MERGE + 1)) > 0

    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "None", qapp)
    assert header_combo(dialog, COL.COL_FIRST_MERGE + 1).currentData() is None
    assert dialog.row_quantity_keys == ["length", "pressure", "mass"]
    assert len(quantity_labels(dialog)) == 3
    assert mapping_combos(dialog, COL.COL_FIRST_MERGE + 1) == []

    combos_col4 = mapping_combos(dialog, COL.COL_FIRST_MERGE)
    assert len(combos_col4) == 3
    assert combos_col4[-1][1].currentData().name == "Weight"


def test_changing_merge_dataset_rebuilds_that_column(
    qapp, dialog: MergeDatasetsDialog
    ) -> None:
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    assert header_combo(dialog, COL.COL_FIRST_MERGE).currentText() == "Conversion Data"
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Modified Data", qapp)
    combos = dict(mapping_combos(dialog, COL.COL_FIRST_MERGE))
    assert combos[COL.FIRST_DATA_ROW].currentData().name == "Depth (TVD)"


def test_changing_merge_dataset_restores_right_column_from_prefered_sets(
    qapp, dialog: MergeDatasetsDialog
) -> None:
    """Changing col 4 rebuilds col 5 but restores Color Data from prefered_sets."""
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Modified Data", qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "Color Data", qapp)
    assert header_combo(dialog, COL.COL_FIRST_MERGE + 1).currentText() == "Color Data"
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    assert header_combo(dialog, COL.COL_FIRST_MERGE + 1).currentText() == "Color Data"
    assert dialog.prefered_sets[1].name == "Color Data"
    combos = dict(mapping_combos(dialog, COL.COL_FIRST_MERGE + 1))
    assert len(combos) == len(dialog.row_quantity_keys)
    assert combos[COL.FIRST_DATA_ROW].currentData().name == "TVDSL"
    assert combos[COL.FIRST_DATA_ROW + 1].currentData().name == "Formation Pressure (user import)"

def test_selecting_none_on_second_merge_stays_none(
    qapp, dialog: MergeDatasetsDialog
    ) -> None:
    setup_three_merge_columns(dialog, qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "None", qapp)
    assert header_combo(dialog, COL.COL_FIRST_MERGE + 1).currentText() == "None"
    assert header_combo(dialog, COL.COL_FIRST_MERGE + 1).currentData() is None
    assert dialog.prefered_sets[1] is None


def test_none_on_second_merge_frees_dataset_for_first_merge_header(
    qapp, dialog: MergeDatasetsDialog
    ) -> None:
    setup_three_merge_columns(dialog, qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "None", qapp)
    dialog._populate_merging_dataset_column_options(COL.COL_FIRST_MERGE)
    qapp.processEvents()
    first_merge_combo = header_combo(dialog, COL.COL_FIRST_MERGE)
    names = {first_merge_combo.itemText(i) for i in range(first_merge_combo.count())}
    assert "Conversion Data" in names


def select_base_dataset(
    dlg: MergeDatasetsDialog, dataset_name: str, qapp: QApplication
) -> None:
    idx = dlg.base_set_combo.findText(dataset_name)
    assert idx >= 0
    dlg.base_set_combo.setCurrentIndex(idx)
    qapp.processEvents()


def rename_merged_header(
    dlg: MergeDatasetsDialog, idx: int, text: str, qapp: QApplication
) -> str:
    from utilities import unique_name

    others = [h for i, h in enumerate(dlg.row_headers) if i != idx]
    header = unique_name(text, others)
    dlg.row_headers[idx] = header
    row = idx + COL.FIRST_DATA_ROW
    line_edit = dlg.main_layout.itemAtPosition(row, COL.COL_HEADERS).widget()
    line_edit.setText(header)
    line_edit.setToolTip(header)
    qapp.processEvents()
    return header


def setup_original_conversion_modified(
    dlg: MergeDatasetsDialog, qapp: QApplication
) -> None:
    select_header_dataset(dlg, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    select_header_dataset(dlg, COL.COL_FIRST_MERGE + 1, "Modified Data", qapp)


def setup_color_conversion_original_modified(
    dlg: MergeDatasetsDialog, qapp: QApplication
) -> None:
    select_base_dataset(dlg, "Color Data", qapp)
    select_header_dataset(dlg, COL.COL_FIRST_MERGE, "Conversion Data", qapp)
    select_header_dataset(dlg, COL.COL_FIRST_MERGE + 1, "Original Data", qapp)
    select_header_dataset(dlg, COL.COL_FIRST_MERGE + 2, "Modified Data", qapp)


def test_mapping_original_conversion_modified(qapp, dialog: MergeDatasetsDialog) -> None:
    setup_original_conversion_modified(dialog, qapp)
    mapping = dialog._build_mapping_dict()

    assert mapping["TVDSL"] == {
        "Original Data": "TVDSL",
        "Conversion Data": "Depth",
        "Modified Data": "Depth (TVD)",
    }
    assert mapping["Formation Pressure (user import)"] == {
        "Original Data": "Formation Pressure (user import)",
        "Conversion Data": "Pressure",
        "Modified Data": "Form. Pr.",
    }
    assert mapping["Excess Pressure (user import)"] == {
        "Original Data": "Excess Pressure (user import)",
        "Conversion Data": "",
        "Modified Data": "Excess Pressure (user import)",
    }
    assert mapping["Weight"] == {
        "Original Data": "",
        "Conversion Data": "Weight",
        "Modified Data": "",
    }
    assert mapping["Result"]["Modified Data"] == "Comments"
    assert mapping["MD"]["Modified Data"] == "Measured Depth"


def test_mapping_original_conversion_modified_renamed_headers(
    qapp, dialog: MergeDatasetsDialog
) -> None:
    setup_original_conversion_modified(dialog, qapp)
    comments_idx = dialog.row_headers.index("Comments")
    md_idx = dialog.row_headers.index("MD")
    run_0 = rename_merged_header(dialog, comments_idx, "Run", qapp)
    run_1 = rename_merged_header(dialog, md_idx, "Run", qapp)

    mapping = dialog._build_mapping_dict()

    assert run_0 == "Run_0"
    assert run_1 == "Run_1"
    assert mapping[run_0] == {
        "Original Data": "Comments",
        "Conversion Data": "",
        "Modified Data": "",
    }
    assert mapping[run_1] == {
        "Original Data": "MD",
        "Conversion Data": "",
        "Modified Data": "Measured Depth",
    }
    assert mapping["Run"] == {
        "Original Data": "Run",
        "Conversion Data": "",
        "Modified Data": "",
    }


def test_mapping_color_conversion_original_modified(
    qapp, dialog: MergeDatasetsDialog
) -> None:
    setup_color_conversion_original_modified(dialog, qapp)
    mapping = dialog._build_mapping_dict()

    assert mapping["TVDSL"] == {
        "Color Data": "TVDSL",
        "Conversion Data": "Depth",
        "Original Data": "TVDSL",
        "Modified Data": "Depth (TVD)",
    }
    assert mapping["Formation Pressure (user import)"] == {
        "Color Data": "Formation Pressure (user import)",
        "Conversion Data": "Pressure",
        "Original Data": "Formation Pressure (user import)",
        "Modified Data": "Form. Pr.",
    }
    assert mapping["Weight"] == {
        "Color Data": "",
        "Conversion Data": "Weight",
        "Original Data": "",
        "Modified Data": "",
    }
    assert mapping["Excess Pressure (user import)"]["Color Data"] == ""
    assert mapping["Mobility"]["Original Data"] == "Mobility"


def test_mapping_color_original_conversion(qapp, dialog: MergeDatasetsDialog) -> None:
    select_base_dataset(dialog, "Color Data", qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE, "Original Data", qapp)
    select_header_dataset(dialog, COL.COL_FIRST_MERGE + 1, "Conversion Data", qapp)
    mapping = dialog._build_mapping_dict()

    assert mapping["TVDSL"] == {
        "Color Data": "TVDSL",
        "Original Data": "TVDSL",
        "Conversion Data": "Depth",
    }
    assert mapping["Weight"] == {
        "Color Data": "",
        "Original Data": "",
        "Conversion Data": "Weight",
    }
    assert mapping["Excess Pressure (user import)"]["Conversion Data"] == ""


def test_header_combo_options_match_available_sets(qapp, dialog: MergeDatasetsDialog) -> None:
    setup_three_merge_columns(dialog, qapp)
    dialog._populate_merging_dataset_column_options(COL.COL_FIRST_MERGE)
    qapp.processEvents()
    combo = header_combo(dialog, COL.COL_FIRST_MERGE)
    ui_names = {combo.itemText(i) for i in range(combo.count())}
    logic_names = {
        ds.name
        for ds in dialog._update_list_of_available_datasets(exclude_col=COL.COL_FIRST_MERGE)
    }
    assert ui_names == logic_names
