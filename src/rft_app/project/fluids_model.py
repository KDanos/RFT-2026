"""
Standard fluid types for the project (catalog), aligned with units_manager.STANDARD_QUANTITIES.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from units import convert_from_normalised_to_user_units

if TYPE_CHECKING:
    from project import ProjectDataManager


@dataclass
class Fluid:
    """An interpreted fluid in the reservoir"""
    name: str
    type: str
    gradient_si: float | None = None
    zero_pressure_depth_si: float | None = None
    contact_fluid: Fluid | None = None
    contact_type: str | None = None
    contact_depth_si: float | None = None
    contact_pressure_si: float | None = None

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
        upper_psi_ft=0.55,
    ),
    "other": FluidType(
        key="other",
        label="Other",
        color="black",
    ),
}


def guess_fluid_type_from_psi_ft(psi_ft: float) -> FluidType:
    for fluid in STANDARD_FLUIDS.values():
        if fluid.lower_psi_ft is None or fluid.upper_psi_ft is None:
            continue
        if fluid.lower_psi_ft <= psi_ft < fluid.upper_psi_ft:
            return fluid
    return STANDARD_FLUIDS["other"]
