# Agent Context Reference — RFT 2026: Line Annotations & pyqtgraph

**Generated:** 21 September 2026  
**Purpose:** Provide a new agent with full context from the recent conversation about chart line annotations and pyqtgraph drawing options, so no background needs to be re-explained.

---

## 1. Response Format Rules (IMPORTANT — follow these exactly)

The user works in two modes. Always apply whichever was last requested.

### "I Am Tired" / "Focused" Mode (default going forward)
- **Short answers only.** One or two paragraphs maximum.
- **Specific code snippets only** — cite the exact lines affected, nothing more.
- **No big rewrites** of files that were not touched.
- **No unsolicited suggestions** — do not offer cleanup, refactors, or improvements unless asked.
- **No preamble** — do not restate the problem before answering.
- If there is more than one issue, list them in bullet form with a max of one sentence each.

### Normal Mode
- Full explanations permitted.
- Suggestions welcome but should be flagged as optional.

---

## 2. Project Stack

| Component | Choice |
|---|---|
| Language | Python 3.12+ |
| UI framework | PyQt6 |
| Plotting | pyqtgraph 0.14.0 |
| Persistence | `pickle` (`.rftproj` files) |
| Units | Custom `units` module with `normalise_from_user_units` / `convert_from_normalised_to_user_units` |
| Project data | `ProjectDataManager` (custom), passed down by reference |

---

## 3. KD Preferred Class Format

All classes **must** follow this exact structure order:

```python
class MyClass(BaseClass):
    def __init__(self, ...) -> None:
        super().__init__(...)

        # Set project variables
        self.project = ...
        self.view = ...

        # Set module variables
        self.foo = ...

        # Initialisation methods
        self._build_ui()
        self._define_menu_actions()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None: ...
    def _connect_signals(self) -> None: ...
    # (other private helpers, alphabetical)

    #--------Public API--------

    def public_method(self) -> None: ...
```

**Rules:**
- All methods have full type hints including `-> None`.
- No `print()`, `breakpoint()`, or debug comments anywhere.
- No query comments (e.g. `# what does this do?`).
- Method signatures that exceed one line use the multi-line format with the closing `)` on its own line.
- `_define_menu_actions` is always called before `_connect_signals` in `__init__` (actions must exist before signals reference them).

---

## 4. Architecture — Line Annotations

### 4.1 Core Problem Solved

`StraightLine` (a `pg.PlotDataItem` subclass) is a UI object and **cannot be pickled reliably**. A separate, pickle-safe dataclass `StraightLineAnnotation` stores the persisted state. The two are linked by `line_id` (a UUID string).

### 4.2 Data Model — `src/rft_app/project/models.py`

```python
@dataclass
class StraightLineAnnotation:
    """Persisted straight-line annotation for charts in an AnalysisView."""
    start_si: tuple[float, float]   # (pressure, depth) — always SI, never display units
    end_si:   tuple[float, float]
    color:    str
    chart_id: str                   # e.g. "pressure_plot" or "xs_pressure_plot"
    line_id:  str                   # uuid4 string, matches StraightLine.id

@dataclass
class AnalysisView:
    ...
    annotations: list[StraightLineAnnotation] = field(default_factory=list)
```

**Key decisions:**
- All coordinates stored in **SI units only**. Display-unit conversion is performed at render time.
- `chart_id` distinguishes which chart (pressure vs excess pressure) a line belongs to. It is set as a string attribute on `DepthGradientChart` at construction.
- `annotations` lives on `AnalysisView`, not `AnalysisObject`, because each view may have different visible annotations.

### 4.3 Persistence Migration — `src/rft_app/project/persistence.py`

Old project files do not have `annotations` on `AnalysisView`. Migration happens at load time:

```python
def load_project(path: str | Path) -> ProjectDataManager:
    ...
    # Migrate older projects pickled before AnalysisView.annotations existed
    for analysis in project.analyses:
        for view in analysis.analysis_views:
            if not hasattr(view, "annotations"):
                view.annotations = []
    return project
```

---

## 5. File Map — Relevant Modules

| File | Role |
|---|---|
| `src/rft_app/project/models.py` | `AnalysisView`, `StraightLineAnnotation`, `ColumnSpec`, etc. |
| `src/rft_app/project/persistence.py` | `save_project` / `load_project` with migration |
| `src/rft_app/ui/depth_gradient_chart/depth_gradient_chart.py` | `DepthGradientChart` — main chart widget |
| `src/rft_app/ui/depth_gradient_chart/straight_line.py` | `StraightLine` — interactive line UI object |
| `src/rft_app/ui/depth_gradient_chart/depth_chart_menu.py` | `DepthMenuChart` — default right-click menu |
| `src/rft_app/ui/analysis_view/graphical_frame.py` | `GraphicalFrame` — holds pressure + xs-pressure charts |
| `src/rft_app/ui/analysis_view/analysis_view.py` | `AnalysisViewWidget` — top-level analysis tab |

---

## 6. Key Class: `DepthGradientChart`

**Location:** `src/rft_app/ui/depth_gradient_chart/depth_gradient_chart.py`  
**Base:** `pg.PlotWidget`

### Constructor signature
```python
def __init__(
        self,
        parent=None,
        x_axis: str = "",
        col_specs: list[ColumnSpec] | None = None,
        chart_id: str = "",
        view: AnalysisView | None = None,
        ) -> None:
```

`project: ProjectDataManager` is **not** a constructor argument — it is set as a plain attribute after construction by `GraphicalFrame`:
```python
self.pressure_chart = DepthGradientChart(frame, ..., view=self.view)
self.pressure_chart.project = self.project
```

### Line drawing flow
1. `start_draw_straight_line()` sets `self.draw_mode = True`.
2. First left-click: records `self.line_start` (view coords) and creates a dashed `preview_line`.
3. Second left-click: calls `_end_draw_straigh_line()`, which:
   - Creates a `StraightLine` object (user-unit coords → converted to SI internally).
   - Appends the line to `self.all_lines`.
   - Creates a `StraightLineAnnotation` (already SI) and appends to `self.view.annotations`.
   - Calls `self.project.mark_modified()`.

### Project load / line rebuild
`_build_ui` iterates `self.view.annotations`, filters by `chart_id`, and rebuilds each `StraightLine` with `points_are_si=True` to prevent double-conversion:
```python
new_line = StraightLine(
    parent=self,
    starting_point=a.start_si,
    end_point=a.end_si,
    color=a.color,
    points_are_si=True,     # ← skips normalise_from_user_units
)
new_line.id = a.line_id     # restore persisted UUID
```

### Unit change handling
`set_data()` refreshes `self.col_specs` from `self.view.column_specs`, re-extracts units, re-formats axes, and calls `_paint_all_lines()`. Lines re-render from SI storage via `refresh_geometry()`.

### Hit-testing — `_is_near_line`
Operates in **view coordinates** (axis units). Computes the nearest point on the segment using the perpendicular projection formula, then converts both the mouse and the nearest point to **scene pixels** via `vb.mapViewToScene(pg.Point(...))` for the pixel-distance comparison:

```python
def _is_near_line(self, line, mouse_view, px_tol=10) -> bool:
    ...
    p_mouse = vb.mapViewToScene(pg.Point(mx, my))
    p_near  = vb.mapViewToScene(pg.Point(nearest_x, nearest_y))
    dist_px = ((p_mouse.x()-p_near.x())**2 + (p_mouse.y()-p_near.y())**2)**0.5
    return dist_px <= px_tol
```

### Right-click menu — `_show_graph_menu`
`pos` from `customContextMenuRequested` is in **widget pixels**. `mapToScene(pos)` converts to scene pixels; `mapSceneToView(scene_pos)` converts to view/data coordinates for `_is_near_line`:

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

> **Known issue (not yet fixed):** `if menu is None` guard block is slightly mis-indented in the current file (indented to match the `for` body rather than the `for` itself). Behaviour is correct but style is inconsistent.

---

## 7. Key Class: `StraightLine`

**Location:** `src/rft_app/ui/depth_gradient_chart/straight_line.py`  
**Base:** `pg.PlotDataItem`

### Constructor
```python
def __init__(
        self,
        parent: pg.PlotWidget | None = None,
        color: QColor | str = "black",
        style: Qt.PenStyle = Qt.PenStyle.DashLine,
        starting_point: tuple[float, float] | None = None,
        end_point: tuple[float, float] | None = None,
        points_are_si: bool = False,
        ) -> None:
```

`self.id = str(uuid.uuid4())` — UUID is generated at construction. If rebuilding from a persisted annotation, overwrite it immediately: `new_line.id = a.line_id`.

### Hover state
```python
self.hovering: bool = False
```
- `on_hover(pos)`: widens pen to width 4, calls `_highlight_line_end_points()`.
- `stop_hovering()`: restores pen width 2, removes `self.temp_scatter` from the chart.
- `DepthGradientChart._on_plot_mouse_move` manages the transition using `line.hovering` to avoid calling `on_hover` on every mouse move event.

### Endpoint highlighting
`_highlight_line_end_points()` adds a `pg.ScatterPlotItem` with an empty circle pen (`"#F0D78C"`, width 2) at both endpoints. The scatter is stored as `self.temp_scatter` and removed in `stop_hovering()`.

`_is_close_to_point(pos, px_tol=10) -> QPointF | None`: converts each endpoint from view coordinates to scene pixels using `vb.mapViewToScene(QPointF(...))`, then does a pixel-distance check. Returns the `QPointF` in view coordinates if close, else `None`.

### Menu actions (stubs — not yet implemented)
- `_convert_line_to_fluid()` — `pass`
- `_delete_self()` — `pass`
- `_duplicate_self()` — `pass`

> **Critical lesson:** always connect with `connect(self._method)`, never `connect(self._method())`. The latter calls the method immediately and passes its return value (usually `None`) to `connect`, which crashes.

### Unit conversion
`_convert_argument_values_to_SI()` converts `starting_point` and `end_point` from user units to SI using `normalise_from_user_units`. This is skipped when `points_are_si=True`.

`refresh_geometry()` converts SI → user units via `convert_from_normalised_to_user_units` and calls `super().setData(...)`.

---

## 8. Coordinate System Clarification

This was a major source of confusion. Canonical definitions:

| Name | Type | Description |
|---|---|---|
| **Widget coordinates** | `QPoint` (integer pixels) | Relative to the top-left of the `PlotWidget`. Emitted by `customContextMenuRequested`. |
| **Scene coordinates** | `QPointF` (float pixels) | Relative to the `QGraphicsScene`. Emitted by `sigMouseMoved` and `sigMouseClicked`. |
| **View / data coordinates** | `QPointF` (axis units, e.g. pressure in bar, depth in m) | The coordinate space of the plotted data. |

### Conversion chain
```
Widget px  →  Scene px    :  self.mapToScene(pos)
Scene px   →  View units  :  vb.mapSceneToView(scene_pos)
View units →  Scene px    :  vb.mapViewToScene(pg.Point(x, y))   # or QPointF
```

- `mapViewToScene` takes a point in **view/data coordinates** (pressure, depth values).
- `mapSceneToView` takes a point in **scene pixels**.
- `mapToScene` (on the widget) takes **widget pixels**.

---

## 9. pyqtgraph Available Annotation Tools (v0.14.0)

Inspected live from the installed package. All items below are in the `pg` namespace.

### ROI family — all share the same signals

| Signal | Meaning |
|---|---|
| `sigRegionChanged` | emitted continuously while dragging |
| `sigRegionChangeFinished` | emitted on mouse-up after drag |
| `sigRegionChangeStarted` | emitted on mouse-down |
| `sigClicked` | emitted on click |
| `sigHoverEvent` | emitted on hover |
| `sigRemoveRequested` | emitted when internal delete handle is clicked |

---

#### `pg.LineSegmentROI` ← **best fit for your straight-line use-case**

```python
pg.LineSegmentROI(positions=((x0, y0), (x1, y1)), **args)
```

- A line segment between two handles. Each handle is individually draggable.
- The whole ROI is draggable as a unit.
- `sigRegionChangeFinished` fires when a drag completes — use this to update `StraightLineAnnotation`.
- **Replaces your current `StraightLine` + custom hit-test approach** entirely. Drag-line and drag-endpoint (CRUD points 3 and 4) are built-in.
- Access endpoint positions: `roi.listPoints()` returns a list of `pg.Point` in the ROI's local coordinate system; transform with `roi.mapToView(p)` to get view/data coordinates.
- Styling: pass `pen=` and `hoverPen=` to constructor.
- **Limitation:** the drag handles use square symbols by default. You can override handle appearance by subclassing or by calling `roi.handles[i]['item'].setPen(...)`.

---

#### `pg.EllipseROI`

```python
pg.EllipseROI(pos=(x, y), size=(w, h), **args)
```

- An ellipse/oval with resize and rotate handles.
- `pos` is the top-left corner of the bounding box (not centre).
- **Fits your "circle/oval to group scatter plots" requirement.** Formatting (pen, brush) is fully supported.
- `movable=True` (default) — can be dragged as a whole.
- `resizable=True` (default), `rotatable=True` (default) — resize and rotate handles visible.
- Can be passed `pen=`, `hoverPen=` for line formatting.

---

#### `pg.CircleROI`

```python
pg.CircleROI(pos=(x, y), size=None, radius=None, **args)
```

- Special case of `EllipseROI` constrained to a circle (aspect-locked).
- Pass either `size=(d, d)` or `radius=r`.
- Same drag/resize/signal behaviour as `EllipseROI`.

---

#### `pg.LineROI`

```python
pg.LineROI(pos1=(x0, y0), pos2=(x1, y1), width=w, **args)
```

- A **thick band** (rectangle) between two points, with width.
- Useful for representing a zone of uncertainty around a line, not a thin segment.
- Not the right choice for a simple drawn line — use `LineSegmentROI` instead.

---

#### `pg.PolyLineROI`

```python
pg.PolyLineROI(positions=[(x0,y0),(x1,y1),(x2,y2),...], closed=False, **args)
```

- A multi-segment open or closed polygon with handles at each vertex.
- Each vertex is individually draggable.
- `closed=True` joins the last point back to the first — good for enclosing a region.
- Could be used for the "circle/oval group" requirement if you want a polygon rather than a smooth ellipse.

---

#### `pg.ROI` (base class)

```python
pg.ROI(pos, size=pg.Point(1,1), angle=0.0, movable=True, rotatable=True, resizable=True, removable=False, pen=None, hoverPen=None, ...)
```

- Generic bounding-box ROI. Subclass this if none of the above fit exactly.
- `addScaleHandle`, `addRotateHandle`, `addTranslateHandle` — add custom handles at specified positions.
- `removable=True` adds a small "×" handle that emits `sigRemoveRequested`.

---

#### `pg.TextItem`

```python
pg.TextItem(text="", color=(200,200,200), html=None, anchor=(0,0), border=None, fill=None, angle=0)
```

- A text label anchored to a point in view coordinates.
- `anchor=(0,0)` = top-left of text at the anchor point; `(0.5, 0.5)` = centred.
- `border=pg.mkPen(...)` draws a box around the text.
- `fill=pg.mkBrush(...)` fills the box background.
- **Not draggable by default** — `TextItem` is a `GraphicsObject`, not an ROI. To make it draggable you need to subclass and override `mouseDragEvent`.
- No signals (it is purely visual).
- **Fits your "text box / comment" requirement** but drag behaviour requires custom code.

---

#### `pg.ArrowItem`

```python
pg.ArrowItem(parent=None, **opts)
```

- A single arrowhead rendered as a `QGraphicsPathItem`.
- Key options: `angle`, `headLen`, `headWidth`, `tailLen`, `tailWidth`, `pen`, `brush`, `pxMode`.
- `pxMode=True` (default) — arrow size is in screen pixels (does not scale with zoom). Set `pxMode=False` for data-space scaling.
- **No drag signals** — it is a static graphic item.
- Intended to be attached to another item as a child (`parent=some_item`), or placed manually at a fixed view position.
- To attach to a `LineSegmentROI` endpoint: add the `ArrowItem` as a child of the handle item, or reposition it in `sigRegionChanged`.
- **Fits "add arrow to line endpoint"** but requires manual positioning logic.

---

#### `pg.InfiniteLine`

```python
pg.InfiniteLine(pos=None, angle=90, pen=None, movable=False, bounds=None, hoverPen=None, label=None, span=(0,1), markers=None)
```

- A line that extends across the entire plot — horizontal (`angle=0`) or vertical (`angle=90`) or arbitrary angle.
- `movable=True` — the line is draggable.
- Signals: `sigDragged`, `sigPositionChanged`, `sigPositionChangeFinished`, `sigClicked`.
- `label=` accepts a string or `pg.InfLineLabel` for a floating label on the line.
- **Not appropriate for a finite two-point line.** Useful for reference lines (e.g. a hydrostatic gradient that spans the whole depth range).

---

#### `pg.TargetItem`

```python
pg.TargetItem(pos=None, size=10, symbol="crosshair", pen=None, hoverPen=None, movable=True, label=None)
```

- A single draggable point marker (crosshair, circle, or any `pg` symbol).
- Signals: `sigPositionChanged`, `sigPositionChangeFinished`.
- `movable=True` by default.
- Could be used as a standalone draggable endpoint handle if you want full control over line geometry without using ROIs.

---

#### `pg.LinearRegionItem`

```python
pg.LinearRegionItem(values=(v0,v1), orientation="vertical", brush=None, pen=None, movable=True, bounds=None)
```

- A shaded band between two parallel lines (vertical or horizontal).
- Both boundary lines are individually draggable; the whole region can be dragged.
- Signals: `sigRegionChanged`, `sigRegionChangeFinished`.
- **Not a match** for your annotation requirements. Useful for depth-window or pressure-range selection UI.

---

## 10. Recommended Mapping — Your Requirements vs pyqtgraph Tools

| Requirement | Recommended tool | Notes |
|---|---|---|
| Straight line between 2 points | `pg.LineSegmentROI` | Replaces `StraightLine + PlotDataItem`. Drag-line and drag-endpoint built in. |
| Drag whole line | `pg.LineSegmentROI` | Built-in — drag the body of the ROI. |
| Drag one endpoint | `pg.LineSegmentROI` | Built-in — drag individual handles. |
| Arrow at endpoint | `pg.ArrowItem` | Attach as child of handle; reposition on `sigRegionChanged`. |
| Text comment box | `pg.TextItem` | Static by default; needs custom `mouseDragEvent` for drag. |
| Circle/oval to group points | `pg.EllipseROI` or `pg.CircleROI` | Drag, resize, rotate built in. Pen/brush fully formattable. |

> **Migration note:** switching from the current `StraightLine (PlotDataItem)` to `LineSegmentROI` would eliminate the need for the custom hit-testing (`_is_near_line`, `_is_near_line_pxl`) and endpoint scatter highlight code. The ROI's own hover and drag signals handle all of that. The persistence model (`StraightLineAnnotation`) and UUID-linking approach remain valid and unchanged.

---

## 11. Open / Pending Work at Time of Summary

### Bugs to fix before next commit
1. **`_show_graph_menu` indentation** — `if menu is None:` block is indented inside the `for` body. Functionally works but style is wrong.

### CRUD features still to implement (in `StraightLine`)
| Feature | Status |
|---|---|
| Drag whole line | Not started |
| Drag endpoint | Not started |
| Delete line | Stub (`pass`) |
| Duplicate line | Stub (`pass`) |
| Convert to fluid | Stub (`pass`) |
| Format line (color, style) | Not started |

### Possible architecture pivot
Given the pyqtgraph `LineSegmentROI` findings, there is a strong case for migrating the current hand-rolled `StraightLine` to a `LineSegmentROI` subclass. This would provide drag, endpoint drag, hover, and signals for free. Decision deferred to user.
