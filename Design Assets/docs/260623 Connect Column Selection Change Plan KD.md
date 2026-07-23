The data_tree is populated with the data from the AnalysisObject, the
analysis.analysis_dataset.datafame. The workflow is:

-the AnalysisView.df should reflect only the checked tree items.

-the table should be updated to reflect the updated AnalysisView.df

Therefore on item change, the steps to be taken are:

1\. capture the prefered unit selection of the table. Create a tempory
list of column spec, to pass in the create_dataframe_table function,
when updating the table, so that the table units do not revert to
project default

2\. the AnalyisView.df is updated

3\. table view in tabular frame is updated

4\. graphical view in graphical frame is also updated (pass for now)

For step 1, i will create a column_spec attribute on the Analysisview
object. I will also create a update_column_spec method

a\) it will default to analysis_object.analysis_datset.column_specs on
AnalysisView object creation

b\) the update_column_spec will be a method of the TabularFrame class

c\) the update_column_spec method will be called from the the
AnalysisViewWidget

for step 2:

a\) i will create a update_view_dataframe method, which will live in the
AnalysisViewWidget

b\) it will be called from the AnalysisViewWidget

for step 3:

a\) i will create an update_table method, which will live in the
TabularFrame

b\) it will be called from the AnalysisViewWidget

In order to call these methods from the AnalysisViewWidget,:

i\) i need to create a custom signal in ViewSidebar view_df_changed

ii\) the view_df_changed signal will be emitted whenever an itemchanged
is triggered in the self.data_tree

iii\) the view_df_changed signal will be picked up by the
AnalysisViewWidget
self.tabular_frame.data_tree.view_df_changed.connect(\_on_column_selection_changed)

iv\) the method \_on_column_selection_change will live in the
AnalysisViewWidget and will call:

-update_column_spec in TabularFrame

-update_view_dataframe in AnalysisViewWidget

-update_table in tabular frame

-update analyses_tree the main window-somehow make it to not update the
workspace tabs

-mark the project as modified

How does that plan sound to you?

**What's solid**

- **AnalysisView.df as the view's working dataframe** (subset
  of analysis_dataset.dataframe) --- correct.

- **Custom signal from ViewSidebar** --- correct pattern;
  keeps DataframeTree dumb and AnalysisViewWidget as orchestrator.

- **Capture units before table rebuild** ---
  necessary; create_dataframe_table defaults combos from project unless
  you restore spec.unit.

- **mark_modified() without refresh_tabs_from_project()** --- correct;
  full tab rebuild would destroy in-memory UI state.

------------------------------------------------------------------------

**Fixes to the plan**

**1. Signal wiring (step iii is wrong)**

The tree lives on **ViewSidebar**, not TabularFrame:

self.widget_frame = ViewSidebar(\...) *\# data_tree is here*

tabular_frame = TabularFrame(\...) *\# local var today --- see below*

Connect like:

self.widget_frame.view_df_changed.connect(self.\_on_column_selection_changed)

Not self.tabular_frame.data_tree\....

Also: \_connect_signals() exists in view_sidebar.py but is **never
called** from \_build_ui() --- wire that up.

------------------------------------------------------------------------

**2. Store self.tabular_frame on AnalysisViewWidget**

Right now tabular_frame is a local variable in \_build_ui, so you can't
call update_table later. Use:

self.tabular_frame = TabularFrame(\...)

Same for self.graphical_frame when you need it.

------------------------------------------------------------------------

**3. Split "capture units" vs "update column specs"**

  -------------------------------------------------------------------------------------------------
  **Responsibility**               **Better home**                             **Why**
  -------------------------------- ------------------------------------------- --------------------
  Read checked column names from   ViewSidebar.get_checked_columns()           Sidebar owns the
  tree                                                                         tree

  Read current unit per column     TabularFrame.capture_units_by_column()      Table owns combos
  from combos                                                                  

  Merge                            AnalysisViewWidget or AnalysisView method   Model update belongs
  into AnalysisView.column_specs                                               at
                                                                               orchestrator/model
                                                                               layer
  -------------------------------------------------------------------------------------------------

Putting **update_column_specs only on TabularFrame** mixes view and
model. Cleaner flow:

def \_on_column_selection_changed(self):

checked = self.widget_frame.get_checked_column_names()

units = self.tabular_frame.capture_units_by_column() *\# before rebuild*

self.\_update_view_column_specs(checked, units) *\# writes
view.column_specs*

self.\_update_view_dataframe(checked) *\# writes view.df*

self.tabular_frame.update_table(self.view, self.project)

self.project.mark_modified()

column_specs on AnalysisView is a good idea --- store **only specs for
columns in view.df**, each with the chosen unit.

**4. update_view_dataframe --- filter from dataset, don't invent data**

Source of truth for raw values:

full_df = self.analysis.analysis_dataset.dataframe

checked_names = \... *\# from tree*

self.analysis_view_obj.df = full_df\[checked_names\].copy()

Match specs by column name/index against analysis_dataset.column_specs.

On **first creation**, initialize:

- view.df = full dataset copy (or your default subset)

- view.column_specs = copy of matching ColumnSpecs from analysis_dataset

And **sync tree checkboxes** to view.df.columns on load (otherwise
everything starts unchecked while the table shows all columns).

------------------------------------------------------------------------

**5. update_table --- full rebuild is OK for now, but design it
carefully**

create_table_view_frame returns a whole QFrame with internal closures
(update_column_values, rounding). For update_table:

1.  Capture units (+ optional decimal settings) from old frame.

2.  Remove old widget from layout (takeAt / deleteLater).

3.  Build new frame with view.df and view.column_specs.

4.  Re-apply units: after build, set each combo
    from spec.unit (today UnitsComboBox uses project default --- you may
    need setCurrentText(spec.unit) if spec.unit is set).

Longer term, refactor create_table_view_frame into
a **class** (TableViewFrame) that holds table, update_column_values,
and set_dataframe(df, specs) --- avoids rebuilding the whole widget tree
on every checkbox click.

------------------------------------------------------------------------

**6. Don't refresh analyses tree / workspace for column toggles**

- **Do:** self.project.mark_modified()

- **Don't:** refresh_tabs_from_project(), refresh_all_analyses_tree() unless
  you need sidebar labels to change

Nothing in your column-selection path should
emit analysis_renamed / analysis_visibility_changed (those are wired to
workspace refresh in main_window).

------------------------------------------------------------------------

**Suggested orchestration (one handler)**

itemChanged on data_treeViewSidebar filters + emit
view_df_changedAnalysisViewWidget.\_on_column_selection_changedUpdate
view.df + view.column_specsTabularFrame.update_tableGraphicalFrame -
later

------------------------------------------------------------------------

**AnalysisView model addition**

\@dataclass

class AnalysisView:

name: str = \"\"

analysis_object: AnalysisObject = None

is_visible: bool = True

df: pd.DataFrame = None

column_specs: list\[ColumnSpec\] = field(default_factory=list)

On default view creation (create_default_analysis_view), set
both df and column_specs from analysis_dataset.

------------------------------------------------------------------------

**Small gaps to plan for**

1.  **At least one column checked** --- guard against empty view.df.

2.  **Depth/pressure columns** --- if depth/pressure must always stay,
    enforce in tree or in update_view_dataframe.

3.  **Unit changes without tree change** --- unit combo changes should
    also update view.column_specs\[\].unit and optionally emit the same
    refresh path (or a separate display_settings_changed signal).

4.  **itemChanged filter** --- only react when item.parent() is
    columns_item and column == 0.

------------------------------------------------------------------------

**Verdict**

The plan is **sound** if you:

1.  Put the signal on **ViewSidebar**, connect
    from **AnalysisViewWidget**.

2.  Keep **AnalysisViewWidget as orchestrator**; model updates
    on AnalysisView, UI capture on sidebar/tabular.

3.  Store **self.tabular_frame** (and call \_connect_signals()).

4.  Sync tree checks ↔ view.df on init.

5.  Preserve units via **column_specs\[\].unit** before rebuild.

6.  Only **mark_modified()** --- no workspace/tree refresh.

I'd rename view_df_changed → column_selection_changed (clearer), but the
name is up to you.

Switch to Agent mode if you want this wired up in the codebase step by
step.
