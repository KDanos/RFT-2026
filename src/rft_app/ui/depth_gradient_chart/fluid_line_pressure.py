from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QInputDialog, QMenu
import pyqtgraph as pg

from model.fluid_model import Fluid, STANDARD_FLUIDS
from project import AnalysisObject, AnalysisView, ProjectDataManager
from ui.depth_gradient_chart.line_annot import LineAnnot
from ui.main_window.project_signals import ProjectSignals
from units import convert_from_normalised_to_user_units
from utilities.global_functions import limit_decimals_str

if TYPE_CHECKING:
    from ui.analysis_view import AnalysisViewWidget
    from ui.depth_gradient_chart.fluid_line_xs_pressure import FluidLineXsPressure


class FluidLinePressure(LineAnnot):
    # Inherited variables (declared here for readability / typing; set by bases)

    # Project
    # LineAnnot
    parent_chart: pg.PlotWidget
    project: ProjectDataManager
    view: AnalysisView
    analysis: AnalysisObject
    signals: ProjectSignals

    # Module
    # LineAnnot
    color: QColor | str
    style: Qt.PenStyle
    pen: object
    starting_point: tuple[float, float] | None
    end_point: tuple[float, float] | None
    is_visible: bool
    id: str
    syncing_peer: bool
    view_widget: AnalysisViewWidget | None
    x_quantity_key: str
    y_quantity_key: str
    x_unit: str
    y_unit: str

    # Initialisation Methods
    # LineAnnot
    """
    (_build_ui)
    (_set_handle_pen_options)
    (_define_menu_actions)
    (_connect_signals)
    (extract_units_and_quantities)
    """

    def __init__(
        self,
        parent: pg.PlotWidget,
        fluid: Fluid,
        signals: ProjectSignals,
        ) -> None:
        color = next(
            (ft.color for ft in STANDARD_FLUIDS.values()
             if ft.label == fluid.type or ft.key == fluid.type),
            "black",
            )
        start = (fluid.plotting_pressure_min_si, fluid.plotting_depth_min_si)
        end = (fluid.plotting_pressure_max_si, fluid.plotting_depth_max_si)
        super().__init__(
            parent=parent,
            signals=signals,
            starting_point=start,
            end_point=end,
            points_are_si=True,
            color=color,
            style=Qt.PenStyle.SolidLine,
            )

        # Set project variables

        # Set module variables
        self.fluid: Fluid = fluid

        # Initialisation methods
        self.toggle_editable()

    #--------Private UI--------

    def _activate_fluid(self) -> None:
        active_fluid_combo = self.view_widget.graphical_sidebar.active_fluid_combo
        idx = active_fluid_combo.findText(self.fluid.name)
        if idx >= 0:
            active_fluid_combo.setCurrentIndex(idx)

    def _connect_signals(self) -> None:
        # Line Movement
        self.sigRegionChanged.connect(self._on_region_changing)
        self.sigRegionChangeStarted.connect(self._on_region_change_started)
        self.sigRegionChangeFinished.connect(self._on_region_change_finished)

        # Menu actions
        self.actionMakeFluidActive.triggered.connect(self._activate_fluid)
        self.actionMakeFluidEditable.triggered.connect(self._make_fluid_editable)
        self.actionRenameFluid.triggered.connect(self._rename_fluid)
        self.actionDuplicateFluid.triggered.connect(self._duplicate_fluid)
        self.actionDeleteFluid.triggered.connect(self._delete_fluid)

    def _define_menu_actions(self) -> None:
        self.actionMakeFluidActive = QAction("Make Active", self)
        self.actionMakeFluidEditable = QAction("Make Editable", self)
        self.actionRenameFluid = QAction("Rename", self)
        self.actionDuplicateFluid = QAction("Duplicate", self)
        self.actionDeleteFluid = QAction("Delete", self)

    def _delete_fluid(self) -> None:
        # Local import avoids circular import via ui.analysis_view.__init__
        from ui.analysis_view.fluid_actions import confirm_delete_fluid

        if not confirm_delete_fluid(self.parent_chart, self.analysis, self.fluid):
            return
        self.analysis.delete_fluid(self.fluid)
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _duplicate_fluid(self) -> None:
        new_fluid = self.analysis.duplicate_fluid(self.fluid, 100)
        self.view.sidebar.visible_fluids.append(new_fluid)
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _find_peer_fluid_line(self) -> FluidLinePressure | FluidLineXsPressure | None:
        other = self._other_depth_chart()
        if other is None:
            return None
        return next(
            (ln for ln in other.all_visible_fluids if ln.fluid is self.fluid),
            None,
            )

    def _make_fluid_editable(self) -> None:
        tree = self.view_widget.graphical_sidebar.visible_fluids_tree
        item = tree.findItems(self.fluid.name, Qt.MatchFlag.MatchExactly)[0]
        item.setCheckState(2, Qt.CheckState.Checked)

    def _on_region_change_finished(self, _roi: object) -> None:
        super()._on_region_change_finished(self)
        self.signals.fluids_changed.emit()

    def _on_region_change_started(self) -> None:
        super()._on_region_change_started(self)

    def _on_region_changing(self) -> None:
        # Guard to exit if this is initiated from the peer line
        if self.syncing_peer:
            return

        # Guard: view not ready yet (mapToView can be None mid-update)
        p0, p1 = self.listPoints()
        if self.mapToView(p0) is None or self.mapToView(p1) is None:
            return

        # Sync FluidLinePressure SI endpoints from the live ROI
        self._on_position_changed()

        # Convert the FluidLinePressure object to Fluid object attributes
        self.fluid.gradient_si = self.calculate_fluid_gradient_si()
        self.fluid.zero_pressure_depth_si = self.calculate_y_intercept_si()
        self.fluid.plotting_depth_min_si = min(self.starting_point[1], self.end_point[1])
        self.fluid.plotting_depth_max_si = max(self.starting_point[1], self.end_point[1])

        # Update other fluids contacts that use this fluid as a contact fluid (including its own)
        self.fluid.refresh_contacts_for_self()

        # Pass the information to the sidebar
        self.view_widget.graphical_sidebar.update_active_fluid_widgets()

        # Sync the peer fluid line
        self._sync_peer_fluid_line()

    def _rename_fluid(self) -> None:
        new_name, ok = QInputDialog.getText(
            self.parent_chart,
            f"Rename Fluid '{self.fluid.name}'",
            "New Name:",
            text=self.fluid.name,
            )
        if not ok:
            return

        self.analysis.rename_fluid(self.fluid, new_name.strip())
        self.signals.fluids_changed.emit()
        self.project.mark_modified()

    def _sync_peer_fluid_line(self) -> None:
        peer_line = self._find_peer_fluid_line()
        if peer_line is None:
            return

        # Avoid ping-ponging between syncing
        peer_line.syncing_peer = True
        try:
            peer_line.apply_endpoints_from_fluid()
        finally:
            peer_line.syncing_peer = False

    #--------Public API--------

    def apply_endpoints_from_fluid(self) -> None:
        f = self.fluid
        self._apply_si_endpoints_and_refresh(
            (f.plotting_pressure_min_si, f.plotting_depth_min_si),
            (f.plotting_pressure_max_si, f.plotting_depth_max_si),
            )

    def build_menu(self) -> QMenu:
        menu = QMenu(self.parent_chart)
        menu.addAction(self.actionMakeFluidActive)
        if not self.fluid.is_editable:
            menu.addAction(self.actionMakeFluidEditable)
        menu.addAction(self.actionRenameFluid)
        menu.addAction(self.actionDuplicateFluid)
        menu.addAction(self.actionDeleteFluid)
        return menu

    def build_tip(self) -> str:
        unit = (
            self.view_widget.graphical_sidebar
            .active_fluid_gradient_unit.currentText()
            )
        gradient = convert_from_normalised_to_user_units(
            unit,
            "pressure_gradient",
            self.fluid.gradient_si,
            )
        return (
            f"{self.fluid.name}\n"
            f"Gradient: {limit_decimals_str(gradient)} ({unit})"
            )

    def setMouseHover(self, hover: bool) -> None:
        super().setMouseHover(hover)
        self.toggle_editable()

    def toggle_editable(self) -> None:
        self.translatable = self.fluid.is_editable
        for handle in self.getHandles():
            handle.setVisible(self.fluid.is_editable)
