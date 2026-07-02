# Tableview Refactoring Plan

*Technical title: QTableView + PandasTableModel + QSortFilterProxyModel Refactor Plan*

**Document file:** `Design Assets/260630 QTableView Refactor Plan KD.md`  
**Project:** RFT 2026 — Analysis View  
**Scope:** Tabular frame + graphical frame (shared display data). Data loaders and `show_dataframe_table_dialog` remain on `QTableWidget`.  
**Date:** 2026-06-30

Follow this plan as explicitly as possible. Implementation proceeds **phase by phase**; request **full code for each numbered item** (e.g. “Phase 0, item 3”) when ready to build. Items **1–55** are listed in §6.

---

## 1. Background

### Current arrangement (`QTableWidget`)

```
view.df  →  create_table_view_frame  →  copy every cell into QTableWidget  →  full rebuild on change
```

- Row 0 holds `UnitsComboBox` widgets; data rows are `QTableWidgetItem` copies.
- Column tick/untick and unit changes trigger `tabular_frame.update_table()` — destroy widget tree and rebuild.
- Works for small tables; becomes sluggish with hundreds/thousands of rows and frequent Excel-style filtering/sorting.

### Target arrangement (Model / View / Proxy)

```
view.df (source, column-selected)
    ↓
PandasTableModel          ← reads df on demand, formats for display
    ↓
ViewSortFilterProxyModel  ← row filter + sort (no full rebuild)
    ↓
QTableView (tabular)          GraphicalFrame (reads same visible rows)
```

Both `TabularFrame` and `GraphicalFrame` subscribe to one **ViewDisplayController** that owns the model + proxy and answers: *which rows are visible?*

### Conceptual comparison

| Aspect | Current `QTableWidget` | Target `QTableView` + model + proxy |
|--------|------------------------|-------------------------------------|
| Where data lives | `view.df` + copied into items | Primarily `view.df`; model reads on demand |
| Filter / sort | Rebuild or manual row hide | Proxy maps rows; `invalidateFilter()` |
| Performance | Slow on large rebuilds | Only visible cells queried |
| Units row | Row 0 `setCellWidget` | Toolbar above table (not a data row) |
| Sortable headers | Custom code needed | `QTableView.setSortingEnabled(True)` on proxy |

---

## 2. Architecture

### Data layers

| Layer | Responsibility |
|-------|----------------|
| `view.df` | Canonical working dataframe (column selection + excess pressure column applied) |
| `view.column_specs` | Display units and quantity keys aligned with `view.df` columns |
| `view.row_filters` *(new field)* | Persisted filter rules for save/load |
| `PandasTableModel` | Adapter: answers `data(row, col)` with formatted display strings |
| `ViewSortFilterProxyModel` | Hides/reorders rows without mutating `view.df` |
| `ViewDisplayController` | Single owner of model + proxy; emits `display_changed` |
| `GraphicalFrame` | Plots `get_visible_dataframe()`, not raw `view.df` |

### Signal flow (orchestrator)

```
ViewSidebar.view_df_changed
    → on_view_df_change
        → build_view_df_and_col_specs_from_column_selection
        → controller.set_view_data(df, column_specs)
        → mark_modified()

TabularFrame.column_unit_change
    → _on_column_unit_change
        → on_column_unit_change(view, ...)
        → controller.refresh_formatting()
        → mark_modified()

Filter UI / proxy
    → on_row_filter_change
        → controller.set_filters(...)
        → display_changed
            → graphical_frame.update_from_visible_data(...)
```

---

## 3. Function map

### A. Shared display formatting (extract from `global_functions.py`)

Keep unit conversion / rounding in one place. Data-loader dialogs keep `QTableWidget`; they may later call the same formatters.

| Function | Description | Proposed file | Replaces |
|----------|-------------|---------------|----------|
| `format_normalised_cell_value(value, quantity_key, output_unit) -> str` | Convert one normalized df value to user-unit display text (handles NA / non-numeric). | `ui/analysis_view/model/view_table_formatting.py` | Inner loop in `create_dataframe_table` → `update_column_values` (`global_functions.py` ~148–158) |
| `apply_decimal_formatting(display_str, *, round_enabled, decimal_places) -> str` | Apply optional rounding to a display string. | same file | `apply_rounding_to_column` + `round_str_to_decimal_points` path in `create_table_view_frame` → `refresh_column` (`global_functions.py` ~245–256) |
| `format_cell_for_table(value, column_spec, output_unit, decimal_settings) -> str` | Single entry point: unit convert + round for one cell. | same file | Combined per-cell work in `update_column_values` + `apply_rounding_to_column` |

**Note:** `round_str_to_decimal_points` in `global_functions.py` **stays** (used by loaders). Analysis view calls the new wrappers above.

---

### B. Filter / view data model

| Function / type | Description | Proposed file | Replaces |
|-----------------|-------------|---------------|----------|
| `FilterSpec` (dataclass) | One rule: column name, operator (`>`, `<`, `==`, `between`, `in`), value(s). | `ui/analysis_view/model/filter_spec.py` | Nothing (new) |
| `row_filter_mask(df, filter_specs, column_specs) -> pd.Series[bool]` | Pure pandas AND mask across all active filters. | `ui/analysis_view/model/analysis_view_data_manager.py` | Future ad-hoc filter code |
| `on_row_filter_change(view, filter_specs) -> None` | Store filters on `AnalysisView`, ready for proxy invalidation. | same file | Nothing (new) |
| `get_visible_row_indices(proxy) -> list[int]` | Map proxy row 0..n-1 to source df row indices (for graph). | same file | Nothing (new) |
| `get_visible_dataframe(view, proxy) -> pd.DataFrame` | `view.df.iloc[visible_indices]` — single source for table + plot. | same file | Implicit “whole df” reads in future graph code |
| `get_plot_series(view, visible_df) -> dict` | Extract depth / pressure / excess columns for plotting (canonical names). | same file | Nothing (new) |

**Model field to add:** `AnalysisView.row_filters: list[FilterSpec]` in `project/models.py`.

**Unchanged:** `build_view_df_and_col_specs_from_column_selection`, `insert_excess_pressure_column`, `on_column_unit_change`.

---

### C. Qt model / proxy layer

| Function / class | Description | Proposed file | Replaces |
|------------------|-------------|---------------|----------|
| `PandasTableModel` | `QAbstractTableModel` reading `view.df`; `data()` calls `format_cell_for_table`. | `ui/analysis_view/model/pandas_table_model.py` | `create_dataframe_table` **for analysis view only** (`global_functions.py` 127–174) |
| `PandasTableModel.set_dataframe(df, column_specs, project, decimal_settings)` | Swap underlying data and emit `modelReset` (column tick/untick). | same class | Full `tabular_frame.update_table()` rebuild |
| `PandasTableModel.set_column_unit(col, unit)` | Update display unit for one column; emit `dataChanged` for that column. | same class | `update_column_values(col)` in `create_dataframe_table` |
| `PandasTableModel.set_decimal_settings(...)` | Reformat all numeric cells without structural rebuild. | same class | `refresh_all_columns` in `create_table_view_frame` (`global_functions.py` 258–260) |
| `ViewSortFilterProxyModel` | `QSortFilterProxyModel` subclass; `filterAcceptsRow` uses `row_filter_mask`. | `ui/analysis_view/model/view_filter_proxy_model.py` | Nothing (new) |
| `ViewSortFilterProxyModel.set_filters(filter_specs)` | Update rules and `invalidateFilter()`. | same class | Nothing (new) |
| `ViewSortFilterProxyModel.source_row_at(proxy_row) -> int` | Thin wrapper over `mapToSource` for graph code. | same class | Nothing (new) |

---

### D. Display coordinator (shared table + graph)

| Function / class | Description | Proposed file | Replaces |
|------------------|-------------|---------------|----------|
| `ViewDisplayController` | Owns `PandasTableModel`, `ViewSortFilterProxyModel`, decimal settings. | `ui/analysis_view/model/view_display_controller.py` | Ad-hoc model/proxy creation inside `tabular_frame` |
| `ViewDisplayController.set_view_data(df, column_specs)` | Push new df/specs into source model after column selection. | same class | `tabular_frame.update_table()` on column change |
| `ViewDisplayController.set_filters(filter_specs)` | Push filters into proxy. | same class | Nothing (new) |
| `ViewDisplayController.get_visible_dataframe() -> pd.DataFrame` | Delegates to `get_visible_dataframe(view, proxy)`. | same class | Nothing (new) |
| `ViewDisplayController.refresh_formatting()` | Unit or decimal change → `dataChanged` only. | same class | `tabular_frame.update_table()` on unit change; `refresh_column` / `refresh_all_columns` in `create_table_view_frame` |

**Signal:** `display_changed` — emitted when filter, sort, df, or format changes; tabular and graphical frames listen.

---

### E. Tabular UI

| Function | Description | Proposed file | Replaces |
|----------|-------------|---------------|----------|
| `_build_table_view_once()` | Create `QTableView`, attach proxy, enable header sort — once in `__init__`. | `ui/analysis_view/ui/tabular_frame.py` | `_build_ui` + `_create_table` destroy/recreate pattern |
| `_build_display_toolbar()` | Units combos per column + decimal checkbox/spin (not data row 0). | `ui/analysis_view/ui/table_display_toolbar.py` | `widgets_frame` in `create_table_view_frame` (`global_functions.py` 223–270) |
| `_sync_units_toolbar_from_specs()` | Set combo texts from `view.column_specs`. | `table_display_toolbar.py` or `tabular_frame.py` | `_update_table_units_combo_from_specs` |
| `_on_toolbar_unit_changed(col, unit)` | Emit `column_unit_change` + `controller.refresh_formatting()`. | `tabular_frame.py` | `_link_table_units_combo_with_signal` + units wiring in `create_table_view_frame._connect_signals` |
| `_on_decimal_settings_changed()` | Forward to `controller.refresh_formatting()`. | `tabular_frame.py` | Decimal spin/checkbox connections in `create_table_view_frame` |
| `bind_display_controller(controller)` | Connect view to shared controller. | `tabular_frame.py` | `create_table_view_frame(...)` call in `_create_table` |
| `set_view_data(df, column_specs)` | `controller.set_view_data(...)` — no widget destroy. | `tabular_frame.py` | `update_table()` |
| `set_row_filters(filter_specs)` | `controller.set_filters(...)`. | `tabular_frame.py` | Nothing (new) |

**Removed after refactor (tabular only):**

| Removed | Was in |
|---------|--------|
| `update_table()` | `tabular_frame.py` |
| `_create_table()` | `tabular_frame.py` |
| `_update_table_units_combo_from_specs()` | `tabular_frame.py` |
| `_link_table_units_combo_with_signal()` | `tabular_frame.py` |

---

### F. Filter UI (Excel-style — Phase 4)

| Function / class | Description | Proposed file | Replaces |
|------------------|-------------|---------------|----------|
| `FilterableHeaderView` | Header click opens filter popup for that column. | `ui/analysis_view/ui/filterable_header_view.py` | Nothing (new) |
| `ColumnFilterPopup` | Operator combo + value field + optional unique-value checklist. | `ui/analysis_view/ui/column_filter_popup.py` | Nothing (new) |
| `_on_filter_applied(col, filter_spec)` | Tabular handler → orchestrator → `on_row_filter_change`. | `tabular_frame.py` | Nothing (new) |

Sortable headers: `QTableView.setSortingEnabled(True)` on the proxy — no custom sort code required.

---

### G. Graphical frame

| Function | Description | Proposed file | Replaces |
|----------|-------------|---------------|----------|
| `bind_display_controller(controller)` | Hold reference; connect `display_changed`. | `ui/analysis_view/ui/graphical_frame.py` | Nothing |
| `update_from_visible_data(visible_df, column_specs)` | Public refresh when table filter/sort/df changes. | same file | Empty `_build_ui` |
| `_render_plot(visible_df)` | Draw depth vs pressure (library TBD). | same file | Nothing (new) |
| `_clear_plot()` | Clear when no visible rows. | same file | Nothing (new) |

**Rule:** Graph uses `controller.get_visible_dataframe()`, not `view.df` directly.

**Fix required:** `analysis_view.py` currently assigns `graphical_frame` as a local variable; refactor must use `self.graphical_frame`.

---

### H. Orchestrator (`analysis_view.py`)

| Function | Description | Proposed file | Replaces |
|----------|-------------|---------------|----------|
| `_init_display_controller()` | Create one `ViewDisplayController` for tabular + graph. | `analysis_view.py` | Implicit per-frame df binding |
| `_on_display_changed()` | `graphical_frame.update_from_visible_data(...)`. | `analysis_view.py` | Nothing (new) |
| `on_view_df_change()` (extend) | After updating `view.df` / specs → `controller.set_view_data(...)`. | `analysis_view.py` | `self.tabular_frame.update_table()` |
| `_on_column_unit_change()` (extend) | After `on_column_unit_change` → `controller.refresh_formatting()`. | `analysis_view.py` | Full table rebuild on unit change |
| `_on_row_filter_change()` (new) | Filter UI → `on_row_filter_change` + `controller.set_filters`. | `analysis_view.py` | Nothing (new) |

---

## 4. What stays untouched

| Area | Stays as-is |
|------|-------------|
| `dialog_data_loader_project.py` | `QTableWidget` preview/mapping |
| `dialog_data_loader_analysis.py` | Own `_update_table` / `_update_table_values` |
| `create_dataframe_table`, `create_table_view_frame` | Used by `show_dataframe_table_dialog` (tree “view dataset”) |
| `create_log_table`, `show_log_table` | Log viewer |
| `view_sidebar.py` | Column tick/untick (structural column filter) |
| `build_view_df_and_col_specs_from_column_selection` | Column subset + excess pressure column |
| Excess pressure **calculation** | Future work (stub remains) |

---

## 5. Proposed folder layout

```
ui/analysis_view/
  model/
    filter_spec.py                 # FilterSpec dataclass
    view_table_formatting.py       # format_cell_for_table, etc.
    pandas_table_model.py          # PandasTableModel
    view_filter_proxy_model.py     # ViewSortFilterProxyModel
    view_display_controller.py     # shared coordinator
    analysis_view_data_manager.py  # existing + row filter helpers
  ui/
    tabular_frame.py               # QTableView host
    table_display_toolbar.py       # units + decimals
    filterable_header_view.py      # Phase 4
    column_filter_popup.py         # Phase 4
    graphical_frame.py             # plot from visible df
    analysis_view.py               # orchestrator
    view_sidebar.py                # unchanged (column selection)
```

---

## 6. Phased implementation plan (items 1–55)

Numbered steps below replace checklist boxes. Each step maps to the function map in §3. When implementing, ask for full code by **phase and item number** (e.g. Phase 1, item 15).

### Phase 0 — Prerequisites (no UI change)

1) Add `FilterSpec` dataclass in `filter_spec.py`  
2) Add `AnalysisView.row_filters: list[FilterSpec]` to `project/models.py`  
3) Create `view_table_formatting.py` with `format_normalised_cell_value`, `apply_decimal_formatting`, `format_cell_for_table`  
4) Verify formatting output matches current `create_dataframe_table` for a sample df (manual or quick test)  
5) Fix `self.graphical_frame` reference in `analysis_view.py` (store on widget, pass `view` + `project` to `GraphicalFrame`)

**Exit criteria:** Formatting helpers exist; model field ready for persistence; graphical frame reachable from orchestrator.

---

### Phase 1 — Model + table view (no row filters yet)

6) Implement `PandasTableModel` class in `pandas_table_model.py` (including `data()`, `rowCount`, `columnCount`, `headerData`)  
7) Implement `PandasTableModel.set_dataframe(df, column_specs, project, decimal_settings)`  
8) Implement `PandasTableModel.set_column_unit(col, unit)`  
9) Implement `PandasTableModel.set_decimal_settings(...)`  
10) Implement `ViewDisplayController` class in `view_display_controller.py` (source model only; proxy stub or pass-through)  
11) Implement `ViewDisplayController.set_view_data(df, column_specs)`  
12) Implement `ViewDisplayController.refresh_formatting()`  
13) Create `table_display_toolbar.py` with `_build_display_toolbar()` (units combos + decimal controls)  
14) Implement `_sync_units_toolbar_from_specs()` in toolbar or `tabular_frame.py`  
15) Refactor `TabularFrame._build_table_view_once()` with `QTableView` attached to controller proxy  
16) Implement `TabularFrame.bind_display_controller(controller)`  
17) Implement `TabularFrame.set_view_data(df, column_specs)` (replaces `update_table()` for data changes)  
18) Implement `TabularFrame._on_toolbar_unit_changed(col, unit)` (emit `column_unit_change` + `controller.refresh_formatting()`)  
19) Implement `TabularFrame._on_decimal_settings_changed()`  
20) Remove `TabularFrame._create_table`, `update_table`, `_update_table_units_combo_from_specs`, `_link_table_units_combo_with_signal`  
21) Implement `AnalysisViewWidget._init_display_controller()`  
22) Wire `on_view_df_change` → `controller.set_view_data` in `analysis_view.py`  
23) Wire `_on_column_unit_change` → `controller.refresh_formatting()` in `analysis_view.py`  
24) Enable `QTableView.setSortingEnabled(True)` on proxy  
25) Confirm column tick/untick, unit change, and decimal rounding still work  
26) Confirm `mark_modified()` still fires on column and unit changes  

**Exit criteria:** Analysis view table uses `QTableView` + model; no full widget rebuild on unit/decimal change; column selection still updates structure via `modelReset`.

**Replaces:** Analysis-view usage of `create_table_view_frame` in `tabular_frame.py`.

---

### Phase 2 — Row filter proxy (backend only)

27) Implement `row_filter_mask(df, filter_specs, column_specs)` in `analysis_view_data_manager.py`  
28) Implement `on_row_filter_change(view, filter_specs)` in `analysis_view_data_manager.py`  
29) Implement `get_visible_row_indices(proxy)` in `analysis_view_data_manager.py`  
30) Implement `get_visible_dataframe(view, proxy)` in `analysis_view_data_manager.py`  
31) Implement `ViewSortFilterProxyModel` class with `filterAcceptsRow` using `row_filter_mask` in `view_filter_proxy_model.py`  
32) Implement `ViewSortFilterProxyModel.set_filters(filter_specs)`  
33) Implement `ViewSortFilterProxyModel.source_row_at(proxy_row)`  
34) Wire proxy into `ViewDisplayController.set_filters` and `ViewDisplayController.get_visible_dataframe`  
35) Implement `TabularFrame.set_row_filters(filter_specs)`  
36) Add temporary dev UI (e.g. simple filter line or test button) to verify proxy filtering without Excel popup  
37) Verify sort + filter compose correctly (sort visible subset)  

**Exit criteria:** Programmatic filters hide rows without rebuild; visible row count matches pandas mask.

---

### Phase 3 — Graphical frame sync

38) Implement `get_plot_series(view, visible_df)` in `analysis_view_data_manager.py`  
39) Implement `GraphicalFrame.bind_display_controller(controller)`  
40) Implement `GraphicalFrame.update_from_visible_data(visible_df, column_specs)`  
41) Implement `GraphicalFrame._render_plot(visible_df)` (minimal plot: depth vs formation pressure)  
42) Implement `GraphicalFrame._clear_plot()`  
43) Implement `AnalysisViewWidget._on_display_changed()` and connect `controller.display_changed`  
44) Verify: table row filter reduces plotted points  
45) Verify: column selection updates both table and plot  

**Exit criteria:** Tabular and graphical views show the same visible row set.

---

### Phase 4 — Excel-style filter UI

46) Implement `FilterableHeaderView` in `filterable_header_view.py`  
47) Implement `ColumnFilterPopup` in `column_filter_popup.py`  
48) Implement `TabularFrame._on_filter_applied(col, filter_spec)`  
49) Implement `AnalysisViewWidget._on_row_filter_change()` (calls `on_row_filter_change` + `controller.set_filters`)  
50) Persist `view.row_filters` on apply; restore on view open  
51) Call `mark_modified()` on filter change  

**Exit criteria:** User can filter columns from header UI; filters survive save/load.

---

### Phase 5 — Optional cleanup

52) Refactor `create_dataframe_table` in `global_functions.py` to call `format_cell_for_table` (DRY with model path)  
53) Trim unused re-exports in `ui/analysis_view/__init__.py` if desired  
54) Remove dead backup files (`analysis_view_old.py`, `tabular_frame_old.py`) if still present  
55) Performance check on 1000+ row dataset (filter, sort, unit change)  

**Exit criteria:** No duplicated display logic; acceptable performance on large tables.

---

### Plan item index (all 55 numbered steps)

| Phase | Items | §3 function map |
|-------|-------|-----------------|
| 0 | 1–5 | A (formatting), B (`FilterSpec`, model field), G (graphical_frame fix) |
| 1 | 6–26 | A, C (`PandasTableModel`), D (`ViewDisplayController`), E (tabular + toolbar), H (orchestrator) |
| 2 | 27–37 | B (filter helpers), C (`ViewSortFilterProxyModel`), D, E (`set_row_filters`) |
| 3 | 38–45 | B (`get_plot_series`), G, H (`_on_display_changed`) |
| 4 | 46–51 | F (filter UI), E, H (`_on_row_filter_change`) |
| 5 | 52–55 | Optional DRY and housekeeping |

---

## 7. Summary counts

| Layer | New items |
|-------|-----------|
| Formatting | 3 functions |
| Data manager + types | 1 type + 5 functions + 1 model field |
| Qt model/proxy | 2 classes, ~6 methods |
| Display controller | 1 class, ~5 methods |
| Tabular UI | ~8 functions; **4 removed** |
| Filter UI (Phase 4) | 2 classes + 1 handler |
| Graphical | 4 functions |
| Orchestrator | 4 functions (2 new, 2 extended) |

**Total:** ~35 named units (functions + class methods + types), expanded to **55 numbered implementation steps** in §6 (includes verification steps and class methods listed separately).

---

## 8. Related documents

- `Design Assets/260623 Connect Column Selection Change Plan KD.md` — column selection workflow (completed)
- `Design Assets/Analysis_Module_Blueprint.md` — broader analysis module design

---

## 9. References

- [PyQt6 Model/View sort and filter tutorial](https://www.pythonguis.com/tutorials/pyqt6-modelview-sort-filter-tables/)
- [QSortFilterProxyModel documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtcore/qsortfilterproxymodel.html)
- [Excel-like filter on QTableWidget (Stack Overflow)](https://stackoverflow.com/questions/8384309/how-to-implement-excel-like-filter-mechanism-on-qtablewidget) — header popup pattern for Phase 4

---

## 10. Printing / PDF export

Tables keep standard markdown pipe format. PDF export uses **portrait A4**, readable fonts (11pt body, 9–9.5pt tables), and `Design Assets/markdown-print.css`.

### Cursor / VS Code — Markdown PDF extension

1. Workspace `.vscode/settings.json` enables portrait + print CSS.
2. **Developer: Reload Window** (once after CSS changes).
3. Open the `.md` file → **Ctrl+Shift+P** → **Markdown PDF: Export (pdf)** (or **Export (html)**).
4. Overwrite the previous PDF/HTML in `Design Assets/`.

### Pandoc (alternative)

```powershell
cd "C:\Users\KonstantinDanos\OneDrive - KD CyPRES Energy ltd\Constantinos Danos\Career\Training\Coding\Python\RFT 2026"
pandoc "Design Assets/260630 QTableView Refactor Plan KD.md" -o "Design Assets/260630 QTableView Refactor Plan KD.pdf" --css="Design Assets/markdown-print.css" -V geometry:margin=14mm
```

### Print CSS behaviour

- Portrait A4; full page width (overrides VS Code preview max-width)
- Body 11pt; tables 9.5pt (9pt for 4-column §3 tables); code 9pt
- Table rows may break across pages (avoids large white gaps)
- `table-layout: fixed` + word-wrap on cells
- Inline code: light gray `#e8eaed`; code blocks: `#f3f4f6`
