# Analysis View Plots — Design Plan (KD)

**Date:** 2026-09-04  
**Status:** Planning (implementation not started)  
**Stack decision:** **pyqtgraph** for all analysis-view graphs  
**Related code today:**
- `src/rft_app/ui/analysis_view/graphical_frame.py` (empty shell)
- `src/rft_app/ui/analysis_view/analysis_view.py` (table + empty graphical frame)
- `src/rft_app/ui/filterable_table/` (proxy model = filtered row source of truth)

---

## 1. Product requirements (captured)

| # | Requirement |
|---|-------------|
| 1 | **Pressure plot** — scatter of points from the **filtered** table (same rows as the proxy model behind `FilterableTable`) |
| 2 | **Y-axis** = depth column, **reversed** (depth increasing downward) |
| 3 | **X-axis (pressure plot)** = formation / pressure column |
| 4 | **Series colour** from a user-chosen categorical column (e.g. well name) |
| 5 | **Series symbol** from a second user-chosen categorical column (e.g. zone, fluid type) |
| 6 | **Excess pressure plot** — Y-axis limits always **synchronised** with the pressure plot |
| 7 | **X-axis (excess plot)** = excess pressure column |
| 8 | **Series synchronised** between pressure and excess plots (same colour/symbol grouping) |
| 9 | Excess plot **may be hidden** |
| 10 | Optional middle **CPI** track; horizontal width ratio about **4 : 1 : 4** (pressure : CPI : excess) |
| 11 | CPI synced on **depth Y**; series/lines from other data sources (not yet in project) |
| 12 | Typical graph UX: zoom, pan/drag, context menu, collect points to a list, etc. |
| 13 | Interactive graphics: drag a line, draw a line between two points, etc. |

---

## 2. Dockable graphs — what that means (and what it is not)

### Not a `QFrame` option

`QFrame` / `QWidget` have **no** built-in “dockable” flag.  
Docking in Qt is done with:

- **`QDockWidget`** — a wrapper that can float, tab, or snap to the edges of a **`QMainWindow`**
- Host API: `QMainWindow.addDockWidget(area, dock)`, `splitDockWidget`, `tabifyDockWidget`, `setCentralWidget(...)`

Typical pattern:

```text
QMainWindow
  ├── central widget          (main work area)
  └── QDockWidget(s)          (panels user can move / float / hide)
        └── your content (plot, tree, table, …)
```

Sketch:

```python
dock = QDockWidget("Pressure plot", main_window)
dock.setWidget(pressure_plot_widget)   # the pyqtgraph widget goes inside
dock.setAllowedAreas(
    Qt.DockWidgetArea.LeftDockWidgetArea
    | Qt.DockWidgetArea.RightDockWidgetArea
)
main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
```

Users then drag the dock title bar to move, float, or stack docks.

### How this relates to *our* three graphs

| Approach | Pros | Cons for RFT tracks |
|----------|------|---------------------|
| **A. `QSplitter` inside `GraphicalFrame`** (recommended start) | Simple; fixed **4–1–4** layout; easy **shared depth Y**; hide excess/CPI with `setVisible` | Not freely “tear off” as separate floating windows |
| **B. One `QDockWidget` for the whole plot strip** | Plot panel can dock vs table / float as a unit | Still uses splitter *inside* the dock for the three tracks |
| **C. One `QDockWidget` per plot** | Maximum layout freedom | **Hard** to keep depth Y + series in sync when undocked/resized independently; 4–1–4 is lost; more UI complexity |

**Decision for this plan (default):**

1. **Start with Approach A** — horizontal `QSplitter` in `GraphicalFrame` (pressure | CPI | excess).  
2. Treat **true docking as optional Phase later** (Approach B first if needed: dock the whole graphical strip).  
3. Avoid Approach C until there is a clear product need; if done, still keep a **PlotCoordinator** owning Y-link and series so undocked panes do not drift out of sync.

**Optional docks that *do* fit well later:** legend, “collected points” list, plot settings — as side `QDockWidget`s on `MainWindowKD` or on a nested `QMainWindow` inside the analysis tab. Those are panels, not depth-synced tracks.

> Note: `AnalysisViewWidget` today is a `QWidget` inside tabs, not a `QMainWindow`. Real `QDockWidget` hosting needs either the app `MainWindowKD`, or making the analysis view (or graphical area) a nested `QMainWindow`. Document that cost before choosing Approach B/C.

---

## 3. Plotting library

**Use pyqtgraph.**

Reasons aligned to requirements:
- Native Qt widgets (fits PyQt6 app)
- Built-in pan / zoom
- **`ViewBox.setYLink(...)`** for shared depth axis across panes
- `ScatterPlotItem` for pressure / excess
- `InfiniteLine`, ROI / custom items for interactive lines (req. 13)
- Context menus and mouse events are straightforward

**Dependency:** add `pyqtgraph` to `requirements.txt` when implementation starts.

---

## 4. Architecture

### Principle

The **proxy model decides which rows are visible**.  
Plots do **not** act as another Qt view of that model.  
A coordinator **reads** filtered rows and **rebuilds** series on the plot widgets.

```text
FilterableTable.proxy_model
        │ filters_changed
        ▼
  PlotCoordinator
        │ extract visible rows → group by colour / symbol columns
        ▼
  GraphicalFrame
        QSplitter (H)  ≈ 4 : 1 : 4
           ├── PressurePlotWidget
           ├── CpiPlotWidget        (stub / hideable)
           └── ExcessPressurePlotWidget (hideable)
```

### Column roles (persist later on `AnalysisView`)

| Role | Meaning | Example |
|------|---------|---------|
| `depth` | Y (inverted) | TVD / MD |
| `pressure` | X on pressure plot | Formation pressure |
| `excess_pressure` | X on excess plot | Excess pressure |
| `series_colour` | Categorical → colour | Well name |
| `series_symbol` | Categorical → marker | Zone / fluid |

Roles are chosen by the user (sidebar / plot toolbar). Until UI exists, hardcode sensible defaults from known column names / indices.

### Main types (proposed modules under `ui/analysis_view/`)

| Module / class | Responsibility |
|----------------|----------------|
| `graphical_frame.py` → `GraphicalFrame` | Owns splitter; show/hide CPI & excess; hosts plot widgets |
| `plots/pressure_plot.py` → `PressurePlotWidget` | pyqtgraph pane; inverted depth Y; pressure X |
| `plots/excess_pressure_plot.py` → `ExcessPressurePlotWidget` | Same Y link; excess X |
| `plots/cpi_plot.py` → `CpiPlotWidget` | Stub first; Y-linked; foreign data later |
| `plots/plot_coordinator.py` → `PlotCoordinator` | Filter → series rebuild; push to all plots; Y-link setup |
| (later) `plots/plot_roles.py` or fields on `AnalysisView` | Persist role mapping + plot visibility |

### Data extraction sketch

```python
# On filters_changed (and role / unit / df refresh):
proxy = tabular_frame.table.proxy_model
source = proxy.sourceModel()
rows = [
    proxy.mapToSource(proxy.index(r, 0)).row()
    for r in range(proxy.rowCount())
]
df = source.df.iloc[rows]
# groupby colour column → list of (x, y, symbol) → update ScatterPlotItems
```

Respect display units the same way the table does (use current `column_specs[].unit` when converting for plot axes), or plot in SI and label axes in user units — pick one approach in Phase 1 and stick to it (recommendation: **plot in current display units** so numbers match the table).

---

## 5. Synchronisation rules

| What | How |
|------|-----|
| Depth Y limits / pan / zoom | Link ViewBoxes: excess + CPI `setYLink(pressure_view_box)`; invert Y on the **master** (pressure) once |
| Series set (colour / symbol) | Coordinator builds series once; applies to pressure + excess together |
| Filtered rows | Single listener on `proxy.filters_changed` |
| Excess / CPI visibility | `widget.setVisible(...)`; splitter stretch still 4–1–4 among *visible* panes (recompute sizes when toggling) |

---

## 6. Implementation phases (refer to these later)

### Phase 0 — Dependency & shell
- [ ] Add `pyqtgraph` to `requirements.txt` / venv
- [ ] Flesh out `GraphicalFrame._build_ui`: horizontal `QSplitter`, one empty `PlotWidget` placeholder
- [ ] Pass `project` / `analysis` / `view` into `GraphicalFrame` from `AnalysisViewWidget` (today only parent is passed)

### Phase 1 — MVP pressure plot
- [ ] `PressurePlotWidget` with inverted depth Y
- [ ] `PlotCoordinator` wired to `tabular_frame.table.proxy_model.filters_changed`
- [ ] Hardcoded roles: depth + pressure (+ colour-by if column exists)
- [ ] Refresh plot when view df / columns change (`_on_view_df_change`)
- [ ] Basic pan / zoom (pyqtgraph defaults)

### Phase 2 — Series styling
- [ ] Colour-by column (user selectable)
- [ ] Symbol-by column (user selectable)
- [ ] Legend (dockable *list* panel optional later)

### Phase 3 — Excess pressure pane
- [ ] `ExcessPressurePlotWidget`
- [ ] Y-link to pressure; shared series refresh
- [ ] Show / hide excess plot; adjust splitter sizes (~4–0–4 or 4–1–4)

### Phase 4 — CPI stub
- [ ] `CpiPlotWidget` placeholder + Y-link
- [ ] Splitter ratio ~4–1–4
- [ ] Document hook points for external CPI data (not in project yet)

### Phase 5 — Interaction UX
- [ ] Context menu (reset zoom, copy, hide series, …)
- [ ] Collect points → list (candidate for a small `QDockWidget` or side panel)
- [ ] Interactive lines: drag horizontal/vertical; draw segment between two clicks (`InfiniteLine` / custom)

### Phase 6 — Persistence & docking (optional)
- [ ] Persist plot roles + pane visibility on `AnalysisView`
- [ ] Decide Approach B: wrap `GraphicalFrame` in a dock host if product needs floating plot strip
- [ ] Do **not** undock individual depth tracks unless sync story is designed

### Phase 7 — Polish
- [ ] Axis titles/units from `ColumnSpec`
- [ ] Performance: rebuild only dirty series; debounce rapid filter edits if needed
- [ ] Tests for coordinator row extraction / grouping (pure logic, no GUI if possible)

---

## 7. Wiring checklist in `AnalysisViewWidget`

When implementing Phase 1:

1. Construct `GraphicalFrame` with `project`, `analysis`, `view`.
2. After `FilterableTable` exists, create `PlotCoordinator(graphical_frame, tabular_frame)`.
3. Connect:
   - `proxy.filters_changed` → coordinator refresh  
   - existing `_on_view_df_change` → also coordinator refresh  
   - (later) role-change signals from sidebar  
4. Keep table and plots as siblings under the vertical splitter (unchanged layout intent).

---

## 8. Explicit non-goals (for now)

- Embedding matplotlib / Plotly
- Per-plot `QDockWidget` tear-off as the default layout
- CPI real data loaders
- Full print/export pipeline

---

## 9. Revision log

| Date | Note |
|------|------|
| 2026-09-04 | Initial plan: requirements 1–13, pyqtgraph, coordinator + splitter, docking explained, phased delivery |
