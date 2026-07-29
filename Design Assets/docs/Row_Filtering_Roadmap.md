# Row filtering roadmap — `FilterableTable`

Agreed design (recap):

- **Header icon:** custom-painted `QHeaderView` subclass. Icon is drawn *inside* each section's existing rect (no extra width added to the column), with a reserved strip so header text is never clipped. Icon has two visual states — filter inactive / filter active — driven by whether the proxy model currently holds a filter for that column.
- **Filtering mechanism:** a `QSortFilterProxyModel` subclass sits between `PandasTableModel` and `CustomTableView`. Non-destructive — `view.df` is never touched; filtering only changes what the proxy exposes to the view.
- **Filter popup:** a `QMenu` opened at the icon's position, styled after the reference screenshot — Sort Ascending/Descending, "Number Filters" submenu (operator-based: equals, greater than, between, …), a search box + checklist of unique values with "(Select All)", "Clear Filter From …", and OK/Cancel.

This doc is a checklist of milestones, not a script — build them in whatever order feels right at the time. Each milestone lists a goal, what "done" looks like (so you know when to move on), any brand-new PyQt concepts/syntax worth flagging before you start (ask about these specifically when you get there), and design decisions that need an answer before that milestone can be finished.

---

## M1 — Static filter icon in every header section

**Goal:** subclass `QHeaderView`, override `paintSection()` to draw a small icon inside each section (no click handling yet).

**New concepts to flag when you get here:** `QHeaderView` subclassing, overriding `paintSection()` (calling into `super().paintSection()` first vs. drawing everything yourself), `QStyleOptionHeader`, painting a `QIcon` into a `QRect`, overriding `sizeHint()`/content size so the reserved icon strip is accounted for by `resizeColumnsToContents()`.

**Suggested location:** a new file, e.g. `ui/filterable_table/filter_header_view.py`, kept separate from `pandas_table_model.py`/`custom_table_view.py`.

**Definition of done:**
- Icon visible in every column's header, same icon for every column (no per-column state yet).
- Full header text still readable — nothing clipped by the icon.
- Load a project, change the column selection on the sidebar tree: `units_table`'s combo row still lines up with the data columns exactly as before (this is the regression to watch for, since the header's size hint changed).

---

## M2 — Detect a click on the icon specifically

**Goal:** override a mouse event handler on the header subclass, hit-test the click position against that column's icon rect, and (for now) just `print(f"clicked column {col}")`.

**New concepts to flag:** `mousePressEvent`/`mouseReleaseEvent` on `QHeaderView`, `event.pos()`, `logicalIndexAt(x)` to get which column a pixel position belongs to, `QRect.contains(point)`.

**Definition of done:**
- Clicking the icon prints the correct column index — test the first column, last column, and a column after resizing others (index vs. pixel position can get confused if you're not careful here).
- Clicking anywhere else in the header (the text/sort area) does **not** print, and existing behavior (column resize by dragging the border) still works.

---

## M3 — Replace the print with an (empty) menu anchored to the icon

**Goal:** on icon click, construct a `QMenu` and show it positioned at the icon's screen location for that column — no real actions yet.

**New concepts to flag:** `QMenu()`, `.popup()` vs `.exec()`, `mapToGlobal(...)` to convert a widget-local rect/point into screen coordinates for anchoring a popup (as opposed to just showing the menu at the cursor).

**Definition of done:** menu appears directly under the icon of whichever column was clicked (not always under column 0, not at the cursor), and dismisses normally on outside click / Esc.

---

## M4 — Populate the menu with placeholder actions

**Goal:** build the menu structure to match the reference screenshot — Sort Ascending, Sort Descending, a "Number Filters" submenu (stub for now), search box placeholder, checklist placeholder, "Clear Filter From …", OK/Cancel — each wired to a print identifying `(action_name, column_index)`.

**New concepts to flag:** `QMenu.addMenu(...)` for the "Number Filters" submenu; `QWidgetAction` if you want to embed a real search box / checklist widget directly inside the menu rather than a separate dialog.

**Watch out for:** the same lambda-default-argument gotcha you already ran into with the units combos (`lambda _, idx=i: ...`) — every action needs to capture *its own* column index correctly, not whichever column was last iterated.

**Definition of done:** every action prints the right `(action, column_index)` pair no matter which column's icon was clicked.

---

## M5 — Introduce the proxy model (pass-through, no real filtering yet)

**Goal:** add a `QSortFilterProxyModel` subclass, set it up between `PandasTableModel` and the view (`self.table.setModel(proxy)` instead of the model directly), with `filterAcceptsRow` always returning `True` for now. Optionally flip on `setSortingEnabled(True)` here too, since it's nearly free once the proxy exists.

**New concepts to flag:** `QSortFilterProxyModel`, `setSourceModel(...)`, and (good to know exists, not needed yet) `mapToSource()`/`mapFromSource()` for later work that needs to reason about "which underlying `view.df` row is visually at row *r*".

**⚠️ Decision point — resolve before this milestone:** `CustomTableView` currently exposes `self.table_model` directly, and `FilterableTable._sync_units_table_column_widths()` / `refresh_display()` call into it (`self.table.table_model.columnCount()`, `.refresh_display()`). Once a proxy sits in front of it, decide: does `self.table.table_model` keep referring to the *source* `PandasTableModel` specifically (with a separate attribute for the proxy), or does calling code switch to going through the proxy? Column indices are unaffected by row-filtering either way, so this is purely about which object each existing call site should talk to.

**Definition of done:** table looks and behaves identically to before the proxy was introduced — this milestone should be invisible to the user if done right.

---

## M6 — One hardcoded test filter, to prove the whole chain

**Goal:** wire exactly one menu action to a fixed, hardcoded filter (e.g. "hide rows where column 0's stored value < some constant") to validate: menu click → proxy stores that criterion → `filterAcceptsRow` uses it → rows actually appear/disappear.

**New concepts to flag:** overriding `filterAcceptsRow(source_row, source_parent)`, calling `invalidateFilter()` after criteria change to force the proxy to re-evaluate every row.

**Definition of done:** clicking that one test action visibly hides matching rows; triggering it again (or a "clear" version) restores them. Prove this end-to-end before generalizing — it's much easier to debug one hardcoded path than a generic one.

---

## M7 — Generalize filter storage across all columns

**Goal:** design a per-column filter-criteria store inside the proxy (conceptually `dict[column_index] -> filter_spec`), and rewrite `filterAcceptsRow` to check *every* column with an active entry — a row passes only if it satisfies all of them.

**⚠️ Decision points to resolve before/during this milestone:**
1. What does a `filter_spec` look like for a numeric-operator filter vs. a checklist filter? (Conceptually two different "shapes" of criteria — e.g. an operator + threshold(s) vs. a set of allowed values — `filterAcceptsRow` needs to know which kind it's looking at for each column.)
2. **Important one:** should numeric filters compare against the *displayed* value (unit-converted, possibly decimal-rounded, i.e. what `PandasTableModel.data()` currently returns) or the *underlying SI-stored* value in `view.df`? This matters a lot given your existing unit-conversion layer — a user typing "> 100" while viewing in `ft` should almost certainly not be silently compared against the stored metres value. Worth deciding explicitly rather than discovering it by accident.

---

## M8 — Real "Number Filters" submenu

**Goal:** build the operator picker (Equals, Greater Than, Less Than, Between, …) with a small input dialog for the threshold value(s), writing into the M7 filter-spec structure.

---

## M9 — Real search box + checklist

**Goal:** populate the checklist from the column's unique values, wire "(Select All)"/individual checkboxes, implement the search box narrowing the visible checklist entries, and OK/Cancel semantics (edits inside the popup shouldn't touch the proxy's real state until OK is pressed).

**Decision worth flagging for later polish (not required for a first pass):** should the checklist show *all* unique values in that column, or only values still reachable given other columns' currently-active filters (Excel's cascading behavior)? The simple version (all values) is a reasonable first target.

---

## M10 — "Clear Filter From …"

**Goal:** wire this action to removing that column's entry from the filter-spec dict and calling `invalidateFilter()`.

---

## M11 — Filter-active icon state

**Goal:** in `paintSection()`, ask the proxy "does column *i* have an active filter entry?" and pick between the two icon variants accordingly (mirrors Excel's grey-outline vs. filled-blue funnel).

---

## M12 — Polish / edge cases

Revisit once the core loop works end-to-end:

- What happens to active filters when the column selection changes on the sidebar tree (`load_from_view` rebuilds `view.df`/`view.column_specs`)? Should filters persist by column name across a rebuild, or reset?
- Interaction with sorting (M5) — does sorting still make sense combined with active filters? (It should, for free, via the proxy — but worth a manual check.)
- Interaction with the decimal-rounding controls, if numeric filters ended up comparing against displayed/rounded values (see M7 decision #2) — rounding changes shouldn't silently change which rows are included.
- Cascading checklist values (deferred from M9).
