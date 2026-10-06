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
    """An interpreted fluid in the reservoir."""

    name: str
    type: str
    gradient_si: float # in unints of pressure/lenght, i.e. inverse of line slope
    zero_pressure_depth_si: float 
    bottom_contact:FluidContact

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
    top_fluid: Fluid| None = None
    bottom_fluid:Fluid | None = None
    exists:bool = False
    type: str | None = None
    depth: float | None = None
    pressure:float | None = None

    def contact_type(self)-> str|None:
        if self.bottom_fluid is not None:
            for key, pair in STANDARD_CONTACTS.items():
                if (self.top_fluid.type, self.bottom_fluid.type) == (pair[0].label, pair[1].label):
                    return key
        return None

    def set_contact_data(self)->None:
        if not self.exists: 
            return 
        
        if not self.bottom_fluid:
            self.exists = False
            return 
        
        # y = m1.x + c1, where 1 is the top fluid and 2 is the bottom fluid
        # m is the gradient of the line is length/pressure, i.e. 1/fluid_gradient
        # c is the y intercept, i.e. the zero pressure depth 

        try: 
            m1 = 1/self.top_fluid.gradient_si
            m2 = 1/self.bottom_fluid.gradient_si
            c1 = self.top_fluid.zero_pressure_depth_si
            c2 = self.bottom_fluid.zero_pressure_depth_si

            # x = (c2-c1)/(m1-m2)
            contact_pressure_si = (c2-c1)/(m1-m2)
            
            # y  = mx +c
            contact_depth_si = 1/self.top_fluid.gradient_si*contact_pressure_si+self.top_fluid.zero_pressure_depth_si
            contact_depth_si_verification = 1/self.bottom_fluid.gradient_si*contact_pressure_si+self.bottom_fluid.zero_pressure_depth_si

            self.exist = True
            self.depth = contact_depth_si
            self.pressure = contact_pressure_si
        except: 
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
        upper_psi_ft=0.55,
    ),
    "other": FluidType(
        key="other",
        label="Other",
        color="black",
    ),
}

STANDARD_CONTACTS:dict[str, tuple[FluidType, FluidType]]= {
    "OWC":(STANDARD_FLUIDS["oil"], STANDARD_FLUIDS["water"]) ,
    "GWC":(STANDARD_FLUIDS["gas"], STANDARD_FLUIDS["water"]) ,
    "GOC":(STANDARD_FLUIDS["gas"], STANDARD_FLUIDS["oil"]) ,
}

def guess_fluid_type_from_psi_ft(psi_ft: float) -> FluidType:
    for fluid in STANDARD_FLUIDS.values():
        if fluid.lower_psi_ft is None or fluid.upper_psi_ft is None:
            continue
        if fluid.lower_psi_ft <= psi_ft < fluid.upper_psi_ft:
            return fluid
    return STANDARD_FLUIDS["other"]
