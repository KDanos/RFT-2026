1. Closed: Create a limit on decimal points at import
2. Closed: Create a "project units" widget on the main window
3. Closed: Add icons to the buttons of the main window
4. Ignore: On data loader, make the mapping window to have no empty space underneath it
5. Closed: On data loader, replace all "delete rows" functionality and naming with "ignore rows"
6. Closed: On the data loader, create an "ignore" option for the data columns. Remember to adjust the dataframe creation to account for the ignored columns
7. Closed: On the data loader, in the quantities options create a "text" option
8. Closed: On the data loader, ensure that the "undefined" and "ignore" options are at the top of the table

---

## Deferred: project data model, units, and persistence aka PROJECT IMPORT PIPELINE

Bob, resume the Project Import Pipeline. We last completed Stage 7 of the 11-stage list (data loader hands imported_column_specs back). Next up is Stage 8 — wire MainWindow.loadData. Confirm scope before we change main.py.

*(These were split out so `models.py` could start with only `ColumnSpec` for unit metadata. Implement when wiring the project store and analysis.)*

9. **`project/models.py` — add dataset / project metadata when needed**
    - Introduce `DataSetMeta` (`source_name`, `imported_at: datetime`, `column_specs: list[ColumnSpec]`, `notes`) when dataset-level information is required (source tracking, timestamps, notes).
    - Use `from datetime import datetime` (not `import datetime`) and `list[ColumnSpec]` (or `typing.List[ColumnSpec]`).
    - Add `ProjectData` (`datasets`, `dataset_meta`, `analysis_objects`, `ui_state`) when save/load and the data tree need a single container.
    - Optional helpers on `DataSetMeta`: `spec_for(name)`, `units_map`, `quantities_map` derived from `column_specs`.

10. **`project/__init__.py`**
    - Re-export `ColumnSpec` now, and later `DataSetMeta`, `ProjectData`, manager, persistence for clean `from project import …` imports.

11. **`project/manager.py` — `ProjectDataManager`** (units-only first pass)
    - Hold `datasets: dict[str, pd.DataFrame]` and `column_specs_by_dataset: dict[str, list[ColumnSpec]]`.
    - `add_dataframe(df, column_specs, name=None) -> str`: assign a unique dataset key, store the DataFrame and its column specs, return the key.
    - Convenience: `get_dataframe`, `get_column_specs`, `list_datasets`.
    - Later (when step 9 lands): switch to a `ProjectData` container and accept `DataSetMeta` instead of raw `column_specs`. Also handle same / fewer / new column headings on append/merge.

12. **`project/persistence.py`**
    - `save_project(project, path)` and `load_project(path) -> ProjectData` once `ProjectData` exists.
    - Start with pickle if needed; plan migration to structured format (e.g. Parquet + JSON for metadata).

13. **Data loader — column specs at import**
    - In `_create_dataframe`, for each data column, read `quantity_combo.currentData()` and `units_combo.currentText()`, build `ColumnSpec(name, quantity_key, unit)` in lockstep with `col_names`.
    - Expose `self.imported_column_specs: list[ColumnSpec]` on the dialog (same pattern as `imported_df`).
    - Defensive defaults if a cell widget is missing (`quantity_key="undefined"`, `unit=""`).

14. **`main.py` / main window — wire import into the project**
    - After successful `dlg.exec()`, call `ProjectDataManager.add_dataframe(dlg.imported_df, dlg.imported_column_specs)`.
    - When step 9 introduces `DataSetMeta`, build it here (with `source_name`, `imported_at`, etc.) and pass that instead.
    - Refresh the data tree / project panel when that UI exists.

15. **Data loader — preview popup**
    - Show column headers with unit, e.g. `f"{name}\n[{unit}]"`, using `imported_column_specs` (DataFrame columns stay plain names).

16. **`units/conversion.py` (or extend `units_manager`)**
    - Per-quantity conversion to a canonical unit (or SI), then to display unit.
    - Analysis / plots: convert on demand for view units; do not mutate stored DataFrame unless the user explicitly commits a conversion.
    - Temperature: support affine conversions (scale + offset), not only multiplicative factors.

17. **Duplicate column names**
    - If two columns resolve to the same name, uniquify keys (`col_3`, `col_3_2`) or introduce stable internal ids so `ColumnSpec` / dict lookups stay unambiguous.

18. **Optional: `DataFrame.attrs["units"]`**
    - Mirror a `{name: unit}` map (derived from `column_specs`) on the DataFrame for in-memory debugging only; treat `column_specs` (and later `DataSetMeta`) as the source of truth for persistence.

19. Closed: Ensure that the units in the mapping table of the data loader appear in alphabetical order
20. Closed: On the dataframe preview of the data loader, the empty values appear as NaN, they should appear as ""
21. Closed: On the dataframe preview of the data loader, 0 decimal point rounding still shows as .0 
22. Closed: On the dataframe preview of the data loader, when clicking the "Round Decimals", the action is not triggered