# RFT 2026 — Full Project Agent Context Reference

**Generated:** 21 September 2026  
**Purpose:** Comprehensive context for a new agent covering the entire project — origin, architecture, modules built, key decisions, coding conventions, and current state.

---

## 1. Response Format Rules (MANDATORY — follow exactly)

These are **two different modes**. Do not conflate them. The user will say which to use. When in doubt, default to **Focused** mode.

### Learning context (always apply)
- This is a **learning project**. The user is learning programming, Python, PyQt, and how to build a real application.
- They have been programming for only a few months; this is their first real project.
- They need space to think through and resolve problems themselves so they can develop skill.
- Support that process: do not take over implementation unless the active mode requires it (especially **"I Am Tired"**).

### "I Am Tired" mode
Use when the user cannot think through the problem and needs a clear, correct answer handed to them.
- Give the **correct replacement code** for the function or function section that needs fixing.
- Point to the **file and location** where the replacement must be made.
- Keep the answer clear and direct — no exploration left for the user to do in this mode.
- No full-file rewrites unless explicitly asked; no unsolicited refactors or side topics.

### Focused mode (default when unsure)
Use when the user is thinking through the problem and wants room to resolve it themselves.
- Respond **only** to the question asked.
- Ignore peripheral elements, extra clarifications, and additional steps.
- **Do not provide code** — answer queries and clarifications in prose so the user can reason and implement.
- No preamble that restates the problem; no unsolicited suggestions.

### Normal Mode
- Full explanations and suggestions permitted.
- Flag optional suggestions as such.
- Code may be shown when it helps understanding, unless the user has asked for Focused mode.

---

## 2. What the Application Is

**RFT 2026** is a desktop application for interpreting well pressure data (RFT = Repeat Formation Tester, also marketed as RCI). It is used in oil and gas reservoir characterisation to:
- Import raw pressure/depth measurements from CSV or similar.
- Display and filter the data in a table.
- Plot pressure vs depth on a gradient chart.
- Annotate the chart (straight lines, eventually fluid gradient lines).
- Persist the full project (data + analysis + annotations) to a `.rftproj` file.

**Tech stack:**

| Component | Choice |
|---|---|
| Language | Python 3.13 (Windows, `.venv\Scripts\python.exe`) |
| UI framework | PyQt6 |
| Plotting | pyqtgraph 0.14.0 |
| Data | pandas |
| Units | pint (via custom `units` module) |
| Persistence | `pickle` → `.rftproj` files |
| Shell | PowerShell (not WSL — that path was abandoned early) |
| OS | Windows 10 |

---

## 3. KD Preferred Class Format

All classes **must** follow this exact structure. A new agent must enforce it on any code it writes or reviews.

```python
class MyClass(BaseClass):
    def __init__(self, ...) -> None:
        super().__init__(...)

        # Set project variables
        self.project = project
        self.view = view

        # Set module variables
        self.foo: int = 0

        # Initialisation methods
        self._build_ui()
        self._define_menu_actions()   # always before _connect_signals
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None: ...
    def _connect_signals(self) -> None: ...
    # (other private helpers, alphabetical order)

    #--------Public API--------

    def public_method(self) -> None: ...
```

**Hygiene rules (enforced before every commit):**
- All methods have full type hints including `-> None` (or the correct return type).
- No `print()`, `breakpoint()`, or debug-timer lines in committed code.
- No query comments (e.g., `# what does this do?`, `# is this correct?`).
- Signals are connected with `connect(self._method)` — **never** `connect(self._method())` (the latter calls the method immediately and passes its return value, usually `None`, to `connect`, which crashes).
- `QAction` objects are created in `_define_menu_actions`, connected in `_connect_signals`.
- `QMenu` must be parented to a `QWidget`, not to a non-widget (e.g., `pg.PlotDataItem`).

---

## 4. Project Folder Structure

```
RFT 2026/
├── .venv/                             # Windows virtual environment (not committed)
├── requirements.txt
├── src/
│   └── rft_app/
│       ├── main.py                    # Entry point — creates QApplication + MainWindowKD
│       ├── project/
│       │   ├── __init__.py            # exports: AnalysisView, ColumnSpec, ProjectDataManager
│       │   ├── canonical_names.py     # CANONICAL_* string constants
│       │   ├── manager.py             # ProjectDataManager
│       │   ├── models.py              # All dataclasses
│       │   ├── persistence.py         # save_project / load_project (pickle)
│       │   └── project_file_actions.py
│       ├── units/
│       │   ├── units_manager.py       # UnitSystem, STANDARD_QUANTITIES, pint registry
│       │   ├── units_normalisation.py # normalise/convert functions, UREG
│       │   └── custom_units_dialog.py
│       ├── ui/
│       │   ├── icons.py
│       │   ├── main_window/
│       │   │   ├── main_window.py     # MainWindowKD (QMainWindow)
│       │   │   ├── analysis_workspace.py  # AnalysisWorkspace (QFrame)
│       │   │   └── sidebar/
│       │   │       ├── project_sidebar.py     # ProjectSidebar (QFrame)
│       │   │       ├── all_datasets_tree.py   # AllDataSetsTree (QTreeWidget)
│       │   │       ├── analyses_tree.py       # AnalysesTree (QTreeWidget)
│       │   │       └── merge_datasets_dialog.py
│       │   ├── analysis_view/
│       │   │   ├── analysis_view.py           # AnalysisViewWidget (QWidget)
│       │   │   ├── analysis_view_data_manager.py
│       │   │   ├── graphical_frame.py         # GraphicalFrame (QFrame)
│       │   │   ├── graphical_sidebar.py       # GraphicalSidebar (QFrame)
│       │   │   └── tabular_sidebar.py         # TabularSidebar (QFrame)
│       │   ├── depth_gradient_chart/
│       │   │   ├── depth_gradient_chart.py    # DepthGradientChart (pg.PlotWidget)
│       │   │   ├── straight_line.py           # StraightLine (pg.PlotDataItem)
│       │   │   └── depth_chart_menu.py        # DepthMenuChart (QMenu)
│       │   ├── filterable_table/
│       │   │   ├── pandas_table_model.py      # PandasTableModel (QAbstractTableModel)
│       │   │   ├── proxy_model.py             # ProxyFilterModel (QSortFilterProxyModel)
│       │   │   ├── filterable_table.py        # FilterableTable (QFrame)
│       │   │   ├── custom_table_view.py       # CustomTableView (QTableView)
│       │   │   ├── filterable_header_view.py  # FilterableHeaderView (QHeaderView)
│       │   │   ├── filter_specs.py            # FilterSpec protocol + clause dataclasses
│       │   │   ├── filter_combos.py           # NumberFilterCombo, TextFilterCombo
│       │   │   ├── filter_by_row_menu.py
│       │   │   └── filter_window.py
│       │   ├── project_data_loader/
│       │   │   ├── dialog_data_loader_project.py   # DataLoaderDialogProject (QDialog)
│       │   │   └── project_data_loader_management.py
│       │   └── widgets/
│       │       ├── dataframe_tree.py
│       │       ├── dialog_data_loader_analysis.py
│       │       ├── dialog_new_analysis_view.py
│       │       └── table_widgets.py           # UnitsComboBox etc.
│       └── utilities/
│           ├── development_functions.py       # trace() debug helper
│           └── global_functions.py
├── Design Assets/                             # Planning docs and MD reference files
└── Tests/
```

---

## 5. Domain Models — `project/models.py`

All domain objects are `@dataclass`. No Qt imports. Safe to pickle.

```python
@dataclass
class ProjectDataManager:           # in manager.py — owns analyses list
    analyses: list[AnalysisObject]
    loaded_datasets: list[DataSet]
    current_unit_system: UnitSystem
    is_modified: bool

@dataclass
class AnalysisObject:
    name: str
    source_datasets: list[str]      # dataset names used
    analysis_dataset: DataSet | None
    formation_pres_src_col: str
    vert_depth_src_col: str
    fluids: list[Fluid]
    parameters: dict[str, Any]
    analysis_views: list[AnalysisView]

@dataclass
class AnalysisView:
    name: str
    analysis_object: AnalysisObject
    is_visible: bool
    df: pd.DataFrame                # display-filtered dataframe (may be None)
    column_specs: list[ColumnSpec]
    column_filters: dict[int, dict]
    annotations: list[StraightLineAnnotation]  # chart line annotations

@dataclass
class StraightLineAnnotation:       # persisted form of a drawn chart line
    start_si: tuple[float, float]   # (pressure, depth) in SI units
    end_si:   tuple[float, float]
    color:    str
    chart_id: str                   # "pressure_plot" or "xs_pressure_plot"
    line_id:  str                   # uuid4 string — links to StraightLine.id

@dataclass(frozen=True)
class ColumnSpec:
    name: str
    quantity_key: str               # matches STANDARD_QUANTITIES keys
    unit: str | None = None

@dataclass
class DataSet:
    name: str
    dataframe: pd.DataFrame         # always SI-normalised after import
    column_specs: list[ColumnSpec]
    info_log: list[DataSetLogEntry]
    created_at: datetime
    user_comments: list[tuple[datetime, str]]

@dataclass
class Fluid:
    name: str
    type: FluidType

@dataclass
class FluidType:
    name: str
    density: float
    color: str
```

---

## 6. Persistence — `project/persistence.py`

Uses `pickle` for the whole `ProjectDataManager` graph.

```python
def save_project(project: ProjectDataManager, path: str | Path) -> None: ...
def load_project(path: str | Path) -> ProjectDataManager: ...
```

**Migration:** Old `.rftproj` files may not have `AnalysisView.annotations`. On load:
```python
for analysis in project.analyses:
    for view in analysis.analysis_views:
        if not hasattr(view, "annotations"):
            view.annotations = []
```
This migration lives in `load_project`, not in `main_window.py`.

---

## 7. Units System — `units/`

**Key principle:** All DataFrames are normalised to SI at import. Display units are converted on the fly at render time. Nothing stored in display units.

### `units_normalisation.py`

| Function | Purpose |
|---|---|
| `normalise_from_user_units(user_unit, quantity_key, value) -> float` | Convert a single value from user units to SI for storage |
| `convert_from_normalised_to_user_units(user_unit, quantity_key, value) -> float` | Convert SI → display units for rendering |
| `identify_si_storage_unit(quantity_key) -> str` | Returns the canonical SI unit string for a given quantity |
| `app_unit_to_pint(app_unit) -> str` | Converts internal unit label strings to pint-compatible names |
| `UREG` | The shared pint `UnitRegistry` — use for array conversions |

**Array conversion pattern (used in `DepthGradientChart`):**
```python
si_unit = app_unit_to_pint(identify_si_storage_unit(quantity_key))
pint_user_unit = app_unit_to_pint(user_unit)
result = UREG.Quantity(np_array, si_unit).to(pint_user_unit).magnitude
```

### `units_manager.py`

- `STANDARD_QUANTITIES`: dict mapping `quantity_key` → `QuantityType` objects.
- `UnitSystem`: named collection of `quantity_key → unit` mappings.
- `ProjectDataManager.current_unit_system` is the active system.
- Unit combos in the UI (`UnitsComboBox`) read available units from `STANDARD_QUANTITIES`.

### `canonical_names.py`

String constants for column names used everywhere:
```python
CANONICAL_VERTICAL_DEPTH        = "Vertical Depth"
CANONICAL_FORMATION_PRESSURE    = "Formation Pressure"
CANONICAL_EXCESS_PRESSURE       = "Excess Pressure"
```

---

## 8. Project Manager — `project/manager.py`

```python
class ProjectDataManager:
    def add_loaded_dataset(self, df, column_specs, name, info_log, user_comment) -> str
    def get_dataset_by_name(self, name: str) -> DataSet
    def mark_modified(self) -> None      # sets dirty flag; triggers save prompt
    def mark_clean(self) -> None
    def is_modified(self) -> bool
    def all_datasets(self) -> list[DataSet]
    def available_unit_systems(self) -> tuple[UnitSystem, ...]
```

`mark_modified()` must be called any time project data changes (line drawn, unit changed, data imported, etc.).

---

## 9. Main Window — `ui/main_window/main_window.py`

`MainWindowKD(QMainWindow)` — the application shell.

**Layout:** Splitter with `ProjectSidebar` (left) and `AnalysisWorkspace` (right).

**Key responsibilities:**
- Menu bar and toolbar (File, Edit, Analysis).
- Load/save project via `project/persistence.py`.
- Import data via `DataLoaderDialogProject`.
- Create analyses, pass them to `AnalysisWorkspace`.
- Save/restore window geometry.

**Data flow on import:**
1. `DataLoaderDialogProject` returns `df`, `column_specs`, `name`.
2. `project.add_loaded_dataset(...)` stores the `DataSet` (SI-normalised).
3. `project.mark_modified()` is called.
4. `ProjectSidebar` tree is refreshed.

---

## 10. Project Sidebar — `ui/main_window/sidebar/`

### `ProjectSidebar (QFrame)`
Container holding `AllDataSetsTree` and `AnalysesTree` in a vertical layout.

### `AllDataSetsTree (QTreeWidget)`
- Shows all loaded datasets as top-level items, with column names as children.
- Supports rename (inline edit, `F2`), which calls `project.rename_dataset(...)`.
- Context menu for dataset-level actions.

### `AnalysesTree (QTreeWidget)`
- Shows all `AnalysisObject` nodes, with `AnalysisView` children.
- Double-click on a view opens it in `AnalysisWorkspace`.
- Supports rename, new analysis, new view, delete.

---

## 11. Analysis Workspace — `ui/main_window/analysis_workspace.py`

`AnalysisWorkspace(QFrame)` — the right panel. Holds a `QTabWidget` where each tab is an `AnalysisViewWidget`.

**Key methods:**
- `open_view(view: AnalysisView)` — opens or focuses the tab for that view.
- `close_view(view: AnalysisView)` — removes the tab.

---

## 12. Data Loader — `ui/project_data_loader/dialog_data_loader_project.py`

`DataLoaderDialogProject(QDialog)` — 635 lines. The full import workflow:
1. Browse for a file (CSV, Excel, etc.).
2. Preview table with column-type mapping.
3. Column header mapping to `quantity_key` (via `STANDARD_QUANTITIES`).
4. Unit selection per column.
5. Row-limit and decimal-preview controls.
6. On confirm: returns normalised `df`, `column_specs`, `name`, `info_log`, `user_comment`.

**Key design decisions from build:**
- The preview table (`QTableWidget`) has a "units row" as row 0, displaying `UnitsComboBox` per column.
- Units combo changes trigger a re-render of preview values only; normalisation always stores SI.
- `DataSetLogEntry` records data-quality issues during import (row, column, old/new value, reason).
- Row-limit spin and "show all" radio work together; the spin fires `valueChanged` only once (debounced to avoid double-fire on manual edit).

---

## 13. Filterable Table System — `ui/filterable_table/`

The main data display inside `AnalysisViewWidget`. This is a full MVC implementation.

### Architecture
```
AnalysisView.df (source)
    ↓
PandasTableModel          ← QAbstractTableModel — reads df, formats for display
    ↓
ProxyFilterModel          ← QSortFilterProxyModel — applies row filters
    ↓
CustomTableView           ← QTableView — renders filtered rows
FilterableHeaderView      ← QHeaderView — column headers with filter dropdowns
    ↓
FilterableTable           ← QFrame — assembles all the above
```

### `PandasTableModel (QAbstractTableModel)`
- `set_dataframe(df, project, decimal_settings)` — replaces source data; calls `beginResetModel() / endResetModel()`.
- `data(index, role)` — returns display text (formatted with `decimal_settings`) or alignment.
- `refresh_display()` — emits `dataChanged` for the whole table; used when units or decimal settings change. **Does not reload the dataframe.**
- `decimal_settings`: dict mapping column name → `(round_enabled: bool, decimal_places: int)`.

### `ProxyFilterModel (QSortFilterProxyModel)`
- `filterAcceptsRow` applies `FilterSpec` objects per column.
- `set_filter(col, spec)` / `clear_filter(col)` — add/remove filters.
- Filters are stored as `AnalysisView.column_filters`.

### `FilterableTable (QFrame)`
- Owns the model + proxy + view + header.
- `filterable_table_refresh(df, col_specs)` — top-level refresh method called from `AnalysisViewWidget`.
- `column_unit_changed` signal emitted when user changes a unit combo in the header.
- Columns resize to header text width on creation, with a minimum column width constant.

### Filter Types — `filter_specs.py`
```python
class FilterSpecNumber   # min/max range filter
class FilterSpecNumberSpecial  # e.g. "is empty", "is not empty"
class FilterSpecValues   # list of allowed discrete values
class FilterSpecText     # contains / starts with / ends with
```

### `FilterableHeaderView (QHeaderView)`
- Custom header that adds a filter combo below each column label.
- `NumberFilterCombo` / `TextFilterCombo` (from `filter_combos.py`) are placed per column.
- `MIN_COLUMN_WIDTH` constant governs minimum width.

---

## 14. Analysis View — `ui/analysis_view/analysis_view.py`

`AnalysisViewWidget(QWidget)` — the main tab content. Combines tabular and graphical frames.

**Layout:**
```
AnalysisViewWidget
├── TabularSidebar      (left — column selector tree)
├── FilterableTable     (centre — the data table)
└── GraphicalFrame      (right — the charts)
```

**Key signals and flow:**

| Signal | Who emits | Who handles |
|---|---|---|
| `FilterableTable.column_unit_changed` | FilterableTable header combo | `AnalysisViewWidget._on_column_unit_change` |
| Unit change → `view.column_specs` updated → `GraphicalFrame.set_data(df)` called | — | — |
| `AnalysisViewWidget.view_df_changed` (custom pyqtSignal) | `_on_view_df_change` | `FilterableTable.filterable_table_refresh` |

**`_on_column_unit_change(col, header, unit)`:**
1. Updates `view.column_specs[col].unit`.
2. Calls `_refresh_plots()` to re-render charts with new units.
3. Calls `project.mark_modified()`.

**`_refresh_plots()`:**
- Gets the visible rows from `visible_df_from_proxy(proxy)`.
- Calls `pressure_chart.set_data(df)` and `xs_pressure_chart.set_data(df)`.

**`visible_df_from_proxy(proxy) -> pd.DataFrame`:**
- Maps proxy rows back to source indices; filters `view.df` to those rows.

---

## 15. Graphical Frame — `ui/analysis_view/graphical_frame.py`

`GraphicalFrame(QFrame)` — holds the two depth-gradient charts side by side.

**Layout:** `HBoxLayout` with three panes (stretch 4 / 1 / 4):
1. `pressure_chart` — `DepthGradientChart` for formation pressure. `chart_id = "pressure_plot"`.
2. `cpi_frame` — placeholder, hidden. `chart_id` not yet assigned.
3. `xs_pressure_chart` — `DepthGradientChart` for excess pressure. `chart_id = "xs_pressure_plot"`. Hidden by default.

**Constructor:**
```python
def __init__(self, parent=None, project=None, col_specs=None, view=None) -> None:
```

`project` is not a constructor arg for `DepthGradientChart` — it is set as a plain attribute after construction:
```python
self.pressure_chart.project = self.project
```

---

## 16. Depth Gradient Chart — `ui/depth_gradient_chart/depth_gradient_chart.py`

`DepthGradientChart(pg.PlotWidget)` — the main interactive chart.

**Constructor:**
```python
def __init__(self, parent=None, x_axis="", col_specs=None, chart_id="", view=None) -> None:
```

**Key attributes:**
- `self.view: AnalysisView` — holds annotations, column_specs.
- `self.project: ProjectDataManager` — set post-construction; needed for `mark_modified()`.
- `self.all_lines: list[StraightLine]` — live UI line objects.
- `self.chart_id: str` — matches annotation `chart_id` for filtering.
- `self.draw_mode: bool` — True while user is drawing a line.

**Line drawing flow:**
1. `start_draw_straight_line()` → `draw_mode = True`.
2. Left-click #1 → stores `line_start` (view coords); creates dashed `preview_line`.
3. Mouse move → `_get_line_starting_point()` updates `preview_line`.
4. Left-click #2 → `_end_draw_straigh_line()`:
   - Creates `StraightLine` (converts user units → SI internally).
   - Appends to `all_lines`.
   - Creates `StraightLineAnnotation` (SI) and appends to `view.annotations`.
   - Calls `project.mark_modified()`.

**Project load / line rebuild** (`_build_ui`):
```python
for a in self.view.annotations:
    if isinstance(a, StraightLineAnnotation) and a.chart_id == self.chart_id:
        new_line = StraightLine(parent=self, ..., points_are_si=True)
        new_line.id = a.line_id   # restore persisted UUID
```

**Unit change handling** (`set_data`):
- Re-reads `col_specs` from `view.column_specs`.
- Re-extracts units and re-formats axes.
- Calls `_paint_all_lines()` which removes and re-adds each line after calling `refresh_geometry()`.

**Coordinate systems (important reference):**

| Name | Type | Description |
|---|---|---|
| Widget coordinates | `QPoint` (integer px) | Relative to `PlotWidget` top-left. Emitted by `customContextMenuRequested`. |
| Scene coordinates | `QPointF` (float px) | Relative to `QGraphicsScene`. Emitted by `sigMouseMoved`, `sigMouseClicked`. |
| View / data coordinates | `QPointF` (axis units) | The data space — pressure in bar, depth in m, etc. |

```python
# Widget px → scene px
scene_pos = self.mapToScene(pos)
# Scene px → view units
mouse = self.getViewBox().mapSceneToView(scene_pos)
# View units → scene px (for pixel-distance comparisons)
px_point = vb.mapViewToScene(pg.Point(x_view, y_view))
```

**Hit-testing — `_is_near_line(line, mouse_view, px_tol=10) -> bool`:**
- Projects the mouse onto the line segment using the dot-product perpendicular formula.
- Converts both the mouse and nearest-segment-point to scene pixels for the distance check.
- `px_tol = 10` pixels.

**Right-click menu — `_show_graph_menu`:**
```python
def _show_graph_menu(self, pos: QPoint) -> None:
    scene_pos = self.mapToScene(pos)
    mouse = self.getViewBox().mapSceneToView(scene_pos)

    menu = None
    for line in self.all_lines:
        if self._is_near_line(line, mouse):
            menu = line.build_menu()
            break
    if menu is None:
        menu = self._built_plot_menu()

    menu.exec(self.mapToGlobal(pos))
```
`break` is essential — without it, the last line in the list wins regardless of which was hit.

---

## 17. Straight Line — `ui/depth_gradient_chart/straight_line.py`

`StraightLine(pg.PlotDataItem)` — interactive line annotation drawn on the chart.

**Constructor:**
```python
def __init__(self, parent=None, color="black", style=Qt.PenStyle.DashLine,
             starting_point=None, end_point=None, points_are_si=False) -> None:
```
- `points_are_si=True` skips `_convert_argument_values_to_SI()` — used when rebuilding from persisted annotations.
- `self.id = str(uuid.uuid4())` — unique ID generated at construction; overwritten with persisted ID on load.

**Unit conversion:**
- `_convert_argument_values_to_SI()` — input user coords → SI storage.
- `refresh_geometry()` — SI → user units via `convert_from_normalised_to_user_units`, then calls `super().setData(...)`.

**Hover state:**
- `self.hovering: bool = False`
- `on_hover(pos)` → pen width 4, calls `_highlight_line_end_points()`.
- `stop_hovering()` → pen width 2, removes `self.temp_scatter`.
- `DepthGradientChart._on_plot_mouse_move` guards with `if not line.hovering` to avoid repeating on every mouse move.

**Endpoint highlighting:**
- `_highlight_line_end_points()` — adds `pg.ScatterPlotItem` at endpoints with empty golden circle pen (`"#F0D78C"`, width 2), stored as `self.temp_scatter`.
- `_is_close_to_point(pos, px_tol=10) -> QPointF | None` — converts endpoints from view to scene pixels; returns the `QPointF` in view coords if within tolerance.

**Menu actions (stubs — not yet implemented):**
- `_convert_line_to_fluid()` — `pass`
- `_delete_self()` — `pass`
- `_duplicate_self()` — `pass`

---

## 18. Tabular Sidebar — `ui/analysis_view/tabular_sidebar.py`

`TabularSidebar(QFrame)` — previously named `ViewSidebar`. Renamed Sep 2026. Contains the column selector tree for the analysis view.

---

## 19. Key Design Decisions (Project-Wide)

### Data normalisation
All imported data is converted to SI immediately on import inside `DataLoaderDialogProject`. The DataFrame stored in `DataSet` and in `AnalysisView.df` is always SI. Display conversion happens only at render time.

### Separation of UI and domain objects
`StraightLine` (a `pg.PlotDataItem`) cannot be pickled. A separate `StraightLineAnnotation` dataclass holds the persisted state. They are linked by `line_id` (UUID string).

### UUID identity
`str(uuid.uuid4())` generates globally unique IDs. The probability of collision in any single project is astronomically low — no deduplication check is needed at construction time.

### `project` passed by reference
The same `ProjectDataManager` instance is passed by reference throughout. When any module calls `project.mark_modified()`, the dirty flag is set for the whole application.

### `assert` for mandatory constructor args
`assert self.view is not None, "DepthGradientChart requires a view"` — preferred over silent `None` checks. The app crashes loudly with a clear message rather than silently producing wrong output.

### Folder structure
The `ui/filterable_table/` module lives outside `ui/analysis_view/` because it is a reusable component. Everything inside `ui/analysis_view/` is specific to that view.

### `@dataclass` vs manual `__init__`
Domain objects use `@dataclass` (no Qt, no pickle issues). UI objects use manual `__init__` following KD Preferred Class Format.

### `@property` decorator
Used in `ProjectDataManager` for computed read-only attributes (e.g., `available_unit_systems`, `is_modified`). The caller uses it like an attribute but the logic runs as a method.

---

## 20. pyqtgraph Annotation Tools (v0.14.0) — Key Findings

Inspected live. All are in the `pg` namespace.

### ROI family — shared signals
`sigRegionChanged`, `sigRegionChangeFinished`, `sigRegionChangeStarted`, `sigClicked`, `sigHoverEvent`, `sigRemoveRequested`

| Class | Constructor (key args) | Best use |
|---|---|---|
| `LineSegmentROI` | `positions=((x0,y0),(x1,y1))` | **Best fit for straight-line annotations** — drag-line and drag-endpoint built in, replaces current `StraightLine + custom hit-test` |
| `EllipseROI` | `pos=(x,y), size=(w,h)` | Oval/circle to group scatter points; drag/resize/rotate built in |
| `CircleROI` | `pos=(x,y), radius=r` | Constrained-circle version of EllipseROI |
| `LineROI` | `pos1, pos2, width` | Thick band between two points — not for thin lines |
| `PolyLineROI` | `positions=[...]` | Multi-segment polygon; `closed=True` for enclosing region |
| `ROI` | `pos, size` | Base class; subclass for custom shapes |

### Non-ROI items

| Class | Key args | Key signals | Notes |
|---|---|---|---|
| `TextItem` | `text, color, anchor, border, fill` | None | Static label; not draggable by default; subclass + override `mouseDragEvent` for drag |
| `ArrowItem` | `angle, headLen, headWidth, pen, brush, pxMode` | None | Static arrowhead; attach as child of handle item or reposition on `sigRegionChanged` |
| `InfiniteLine` | `pos, angle, movable, label` | `sigDragged`, `sigPositionChanged` | Extends across full plot — for reference lines only, not finite segments |
| `TargetItem` | `pos, size, symbol, movable` | `sigPositionChanged`, `sigPositionChangeFinished` | Single draggable marker; useful for standalone endpoint handles |
| `LinearRegionItem` | `values, orientation, movable` | `sigRegionChanged` | Shaded band between two parallel lines; for selection/highlight zones |

### Recommended mapping — your annotation requirements

| Requirement | Tool | Notes |
|---|---|---|
| Straight line between 2 points | `LineSegmentROI` | Replaces `StraightLine + PlotDataItem`; drag-line and drag-endpoint free |
| Drag whole line | `LineSegmentROI` | Built in |
| Drag one endpoint | `LineSegmentROI` | Built in — individual handle drag |
| Arrow at endpoint | `ArrowItem` | Position as child of ROI handle; update on `sigRegionChanged` |
| Text comment box | `TextItem` | Static; needs custom `mouseDragEvent` for drag |
| Circle/oval to group points | `EllipseROI` or `CircleROI` | Drag, resize, rotate built in; pen/brush formattable |

> **Architecture note:** Migrating to `LineSegmentROI` would eliminate the need for `_is_near_line`, `_is_close_to_point`, and the `ScatterPlotItem` endpoint highlight — all replaced by built-in ROI signals and handles. The persistence model (`StraightLineAnnotation`) and UUID-linking approach remain valid unchanged.

---

## 21. Open / Pending Work

### Known bug — `_show_graph_menu` indentation
`if menu is None:` block is mis-indented (inside the `for` body rather than at the same level). Behaviour is currently correct but the style is wrong.

### CRUD features for `StraightLine` — not yet implemented

| Feature | Status |
|---|---|
| Drag whole line | Not started |
| Drag one endpoint | Not started |
| `_delete_self()` | Stub — `pass` |
| `_duplicate_self()` | Stub — `pass` |
| `_convert_line_to_fluid()` | Stub — `pass` |
| Format line (color, width, style dialog) | Not started |

### Architecture decision deferred
Whether to keep the current `StraightLine (PlotDataItem)` with custom hit-testing, or migrate to `LineSegmentROI`. The ROI approach gives drag and endpoint drag for free but requires a refactor of the drawing flow and hover/hover-stop logic.

---

## 22. Git Workflow Reminders

- User stages and commits manually — **never commit on behalf of the user**.
- Before committing: remove all `print()`, debug timers, query comments; enforce KD Preferred Class Format.
- `git status -sb` — short status with branch.
- `git add <file>` — stage individual files.
- `git diff --name-only` — see what has changed.
- `git diff --cached --name-only` — see what is staged.

---

## 23. Qt Model/View — How `dataChanged` and `data()` Actually Work

This was explored in depth. Critical corrections to common misconceptions:

### `dataChanged` does NOT call `data()`
`dataChanged.emit(top_left, bottom_right, [DisplayRole])` runs connected slots **synchronously and immediately**. It does **not** queue anything for `processEvents`. The slots it runs are:
1. The proxy model forwards the signal.
2. `QTableView` marks the affected viewport region as **stale** (dirty). No painting, no `data()` calls.
3. On the **next paint event**, the view calls `data()` only for **visible cells** in the dirty region.

### `setData()` vs `data()`
- `setData()` — called when the **user edits** a cell (e.g. types into it). Not part of the display-refresh path.
- `data()` — called by Qt whenever the **view needs to paint a cell**. This is the pull side. It is also called by `resizeColumnsToContents()` for every column/row to measure text width.

### Why the DataFrame is never rewritten on unit change
`PandasTableModel.df` is always SI-normalised. `column_specs[col].unit` holds the display unit. `data()` converts on every call:
```python
user_unit = self.column_specs[col].unit
value = convert_from_normalised_to_user_units(user_unit, quantity_key, value)
```
Changing a unit combo updates `column_specs` in-place; the next `data()` call produces a different string without touching the DataFrame.

### `column_specs` is a shared list
After `load_data(df, column_specs, ...)` all of the following hold the **same Python list object**:
- `AnalysisView.column_specs`
- `FilterableTable.column_specs`
- `CustomTableView.column_specs`
- `PandasTableModel.column_specs`
- `GraphicalFrame.col_specs` / `DepthGradientChart.col_specs`

`column_specs[idx] = ColumnSpec(...)` replaces one slot in the shared list. All holders immediately see the new unit.

### `processEvents()` — debug tool only
`QApplication.processEvents()` flushes the event queue mid-slot, forcing the pending paint to happen before the function returns. It was added temporarily to capture per-paint conversion counts in debug timers. It must never be in committed code — it can re-enter other slots while still inside the current one.

---

## 24. Filterable Table — Performance Fix (Sep 2026)

### Problem
`resizeColumnsToContents()` walked every cell (including off-screen rows) to measure text width. It called `data()` for each cell × each role the delegate requested (DisplayRole + SizeHintRole). With 407 rows and ~10 columns, this produced ~14,788 conversion calls and took ~2s per unit change.

### Fix
Replaced with header-text-only sizing at load time. Added `MIN_COL_WIDTH_PX = 80` as a class constant on `CustomTableView`. Removed `resizeColumnsToContents()` from `filterable_table_refresh`.

**In `CustomTableView._build_ui`:**
```python
self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
```

**In `CustomTableView.load_data` (replaces `resizeColumnsToContents()`):**
```python
header = self.horizontalHeader()
for i in range(self.model().columnCount()):
    width = max(header.sectionSizeFromContents(i).width(), self.MIN_COL_WIDTH_PX)
    self.setColumnWidth(i, width)
```

`sectionSizeFromContents(i)` uses the **header label** only — no `data()` calls, no row scanning. `FilterableHeaderView.sectionSizeFromContents` already adds `ICON_SIZE + (ICON_MARGIN * 2)` for the filter icon.

**After this fix:** unit change completes in ~0.05s with 186 conversion calls (visible-cell paint only), down from ~2s and 14,788 calls.

### `filterable_table_refresh` — final clean form
```python
def filterable_table_refresh(self) -> None:
    self.table.table_model.refresh_display()
    self._sync_units_table_column_widths()
```
No resizing. No timers. No prints.

---

## 25. Unit Change Data Flow Map

Full chain when user changes a `UnitsComboBox`:

```
USER changes UnitsComboBox (column i)
        |
        v
FilterableTable._on_units_change(i)
        |
        +-- column_specs[i] = ColumnSpec(name, quantity, new_unit)
        |     (same list as AnalysisView + table model + charts)
        |
        +-- filterable_table_refresh()          [TABLE PATH, always]
        |         |
        |         +-- PandasTableModel.refresh_display()
        |         |         emit dataChanged(all cells, DisplayRole)
        |         |         proxy forwards
        |         |         QTableView: viewport stale
        |         |         later PAINT -> data() per visible cell
        |         |         data() converts SI -> user unit from spec
        |         |
        |         +-- sync units-row widths (no-op if widths unchanged)
        |
        +-- emit column_unit_change(i, name, new_unit)
                  |
                  v
AnalysisViewWidget._on_column_unit_change     [VIEW PATH, listener]
        |
        +-- if name in {Vertical Depth, Formation Pressure, Excess Pressure}:
        |         _refresh_plots()
        |              visible_df_from_proxy  (filtered rows, SI values)
        |              DepthGradientChart.set_data(df)
        |                   _extract_quantity_and_units()  <- shared specs
        |                   _format_chart()                <- axis labels
        |                   convert arrays -> scatter
        |
        +-- project.mark_modified()             [always]
```

**Why chart refresh is NOT inside `FilterableTable`:** `FilterableTable` is a reusable component used in contexts without `AnalysisViewWidget` (e.g. merge preview). Chart refresh is the concern of the controller, connected via `column_unit_change` signal.

**Decimals only** trigger `filterable_table_refresh` — they do **not** emit `column_unit_change`, so charts do not replot.

**`analysis_view_data_manager.on_column_unit_change`** — this function is unused and a leftover. Do not call it.

---

## 26. AnalysisViewWidget Layout Restructure (Sep 2026)

### Old layout
```
QHBoxLayout
├── ViewSidebar        (narrow left — data tree)
└── QFrame (main)
    └── QSplitter (Vertical, 50/50)
        ├── GraphicalFrame   (top)
        └── FilterableTable  (bottom)
```

### New layout
```
QVBoxLayout
└── QSplitter (Vertical, 50/50)  — self.main_frame_splitter
    ├── QSplitter (Horizontal, 1:5)  — self.graphical_row_splitter
    │   ├── GraphicalSidebar         — self.graphical_widgets_frame  (left, narrow)
    │   └── GraphicalFrame           — self.graphical_frame          (right, wide)
    └── QSplitter (Horizontal, 1:5)  — self.tabular_row_splitter
        ├── TabularSidebar           — self.sidebar_frame            (left, narrow)
        └── FilterableTable          — self.tabular_frame            (right, wide)
```

Visual:
```
[ GraphicalSidebar | GraphicalFrame  ]
[ TabularSidebar   | FilterableTable ]
```

- Top/bottom remain 50/50.
- Each row uses `setSizes([1000, 5000])` — same 1:5 ratio as the old sidebar splitter.
- `FilterableTable` and `GraphicalFrame` are unchanged internally.

### File changes
- `ui/analysis_view/analysis_view.py` — `_build_ui` rewritten.
- `ui/analysis_view/view_sidebar.py` — **deleted**.
- `ui/analysis_view/tabular_sidebar.py` — **new file**, `TabularSidebar(QFrame)`. Identical to old `ViewSidebar` but renamed. Signal `view_df_changed` preserved.
- `ui/analysis_view/graphical_sidebar.py` — **new file**, `GraphicalSidebar(QFrame)`. Empty pane with `main_layout = QVBoxLayout(self)` ready for graph controls.
- `ui/analysis_view/__init__.py` — updated exports.

---

## 27. DepthMenuChart — Class Format Update (Sep 2026)

`DepthMenuChart(QMenu)` in `depth_chart_menu.py` was updated to conform to KD Preferred Class Format:

- `__init__` now accepts `parent: QWidget | None = None` and passes it to `super().__init__(parent)`.
- Actions defined in `_define_main_menu_actions()`, connected in `_connect_signals()`.
- `_build_ui()` adds actions to the menu.
- `_add_a_gradient_line()` is a stub (`print("here we go")`) — not yet implemented.
- `DepthGradientChart._show_graph_menu` updated to pass `self` as parent: `DepthMenuChart(self)`.

---

## 28. `analysis_view_data_manager.py` — Scope Decision

Keep the file. `insert_excess_pressure_column` is imported by:
- `main_window.py`
- `dialog_new_analysis_view.py`
- `analysis_view/__init__.py` (re-exported)

Folding it into `analysis_view.py` would force those callers to import a Qt widget file for a pure pandas function — wrong dependency direction.

`refresh_view_object_from_column_tree_selection` is used only by `AnalysisViewWidget` and could be inlined, but keeping it in the data manager keeps the widget file clean.

`on_column_unit_change` in the data manager is **unused** — a leftover. Safe to delete.
