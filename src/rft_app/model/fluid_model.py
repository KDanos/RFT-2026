"""
Standard fluid types for the project (catalog), aligned with units_manager.STANDARD_QUANTITIES.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from units import convert_from_normalised_to_user_units

if TYPE_CHECKING:
    from model.data_models import AnalysisObject
    from project.manager import ProjectDataManager


@dataclass
class Fluid:
    """An interpreted fluid in the reservoir."""

    name: str
    type: str
    gradient_si: float  # pressure/length, i.e. inverse of line slope
    zero_pressure_depth_si: float
    bottom_contact: FluidContact
    plotting_depth_min_si: float
    plotting_depth_max_si: float
    analysis_object: AnalysisObject | None = None
    is_editable: bool = False

    #--------Public API--------

    @property
    def plotting_pressure_max_si(self) -> float:
        """pressure = gradient * (depth - zero pressure depth)"""
        gradient = self.gradient_si
        depth = self.plotting_depth_max_si
        zpd = self.zero_pressure_depth_si
        return gradient * (depth - zpd)

    @property
    def plotting_pressure_min_si(self) -> float:
        """pressure = gradient * (depth - zero pressure depth)"""
        gradient = self.gradient_si
        depth = self.plotting_depth_min_si
        zpd = self.zero_pressure_depth_si
        return gradient * (depth - zpd)

    def refresh_contacts_for_self(self) -> None:
        self.bottom_contact.set_contact_data()
        if self.analysis_object is None:
            return
        for f in self.analysis_object.fluids:
            if f is self:
                continue
            if self is f.bottom_contact.bottom_fluid:
                f.bottom_contact.set_contact_data()

    def update_gradient_and_zpd_from_2_pressure_depth_points(
        self,
        starting_point: tuple[float, float],
        end_point: tuple[float, float],
        ) -> None:
        """Points must be passed in as (pressure, depth)."""
        dp = starting_point[0] - end_point[0]
        dz = starting_point[1] - end_point[1]
        if dz == 0:
            return
        gradient = dp / dz
        zpd = starting_point[1] - starting_point[0] / gradient
        self.gradient_si = gradient
        self.zero_pressure_depth_si = zpd

    def update_zpd_on_gradient_change(self, depth: float, pressure: float) -> None:
        """Update ZPD so the fluid rotates about (pressure, depth) when gradient changes.

        y = mx + c, where y = depth, x = pressure, m = 1/gradient, c = zpd
        => zpd = depth - pressure / gradient
        """
        zpd = depth - (1 / self.gradient_si * pressure)
        self.zero_pressure_depth_si = zpd
        self.refresh_contacts_for_self()

    def values_in_project_units(
        self,
        project: ProjectDataManager,
        quantity_key: str,
        value_si: float | None,
        ) -> float | None:
        if value_si is None:
            return None
        user_unit = project.current_unit_system.units_by_quantity[quantity_key]
        return convert_from_normalised_to_user_units(user_unit, quantity_key, value_si)

@dataclass
class FluidContact:
    top_fluid: Fluid | None = None
    bottom_fluid: Fluid | None = None
    exists: bool = False
    type: str | None = None
    depth: float | None = None
    pressure: float | None = None

    #--------Public API--------

    def contact_type(self) -> str | None:
        if self.bottom_fluid is not None:
            for key, pair in STANDARD_CONTACTS.items():
                if (self.top_fluid.type, self.bottom_fluid.type) == (
                    pair[0].label,
                    pair[1].label,
                    ):
                    return key
        return None

    def set_contact_data(self) -> None:
        # Set the contact type
        self.type = self.contact_type()

        # Set the pressure, depth and depth intercepts
        if not self.bottom_fluid:
            self.exists = False
            self.depth = None
            self.pressure = None
            return

        # y = m1.x + c1, where 1 is the top fluid and 2 is the bottom fluid
        # m is the gradient of the line is length/pressure, i.e. 1/fluid_gradient
        # c is the y intercept, i.e. the zero pressure depth

        try:
            m1 = 1 / self.top_fluid.gradient_si
            m2 = 1 / self.bottom_fluid.gradient_si
            c1 = self.top_fluid.zero_pressure_depth_si
            c2 = self.bottom_fluid.zero_pressure_depth_si

            # x = (c2-c1)/(m1-m2)
            contact_pressure_si = (c2 - c1) / (m1 - m2)

            # y = mx + c
            contact_depth_si = (
                1 / self.top_fluid.gradient_si * contact_pressure_si
                + self.top_fluid.zero_pressure_depth_si
                )

            self.exists = True
            self.depth = contact_depth_si
            self.pressure = contact_pressure_si
        except Exception:
            self.exists = False
            self.depth = None
            self.pressure = None
            return


@dataclass(frozen=True)
class FluidType:
    key: str
    label: str
    color: str
    lower_psi_ft: float | None = None
    upper_psi_ft: float | None = None


STANDARD_FLUIDS: dict[str, FluidType] = {
    "gas": FluidType(
        key="gas",
        label="Gas",
        color="red",
        lower_psi_ft=0.08,
        upper_psi_ft=0.22,
        ),
    "oil": FluidType(
        key="oil",
        label="Oil",
        color="green",
        lower_psi_ft=0.22,
        upper_psi_ft=0.38,
        ),
    "water": FluidType(
        key="water",
        label="Water",
        color="blue",
        lower_psi_ft=0.38,
        upper_psi_ft=0.45,
        ),
    "mud": FluidType(
        key="mud",
        label="Drill Mud",
        color="brown",
        lower_psi_ft=0.45,
        upper_psi_ft=0.65,
        ),
    "other": FluidType(
        key="other",
        label="Other",
        color="purple",
        ),
}

STANDARD_CONTACTS: dict[str, tuple[FluidType, FluidType]] = {
    "OWC": (STANDARD_FLUIDS["oil"], STANDARD_FLUIDS["water"]),
    "GWC": (STANDARD_FLUIDS["gas"], STANDARD_FLUIDS["water"]),
    "GOC": (STANDARD_FLUIDS["gas"], STANDARD_FLUIDS["oil"]),
}


def guess_fluid_type_from_psi_ft(psi_ft: float) -> FluidType:
    for fluid in STANDARD_FLUIDS.values():
        if fluid.lower_psi_ft is None or fluid.upper_psi_ft is None:
            continue
        if fluid.lower_psi_ft <= psi_ft < fluid.upper_psi_ft:
            return fluid
    return STANDARD_FLUIDS["other"]
