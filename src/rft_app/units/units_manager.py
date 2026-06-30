"""
Central Type of units for the project
Create two classes, QuanityType and UnitSystem
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from project.manager import ProjectDataManager

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass (frozen = True)
class QuantityType:
    key:str
    label:str
    units:Tuple[str,...]
    symbols:Tuple[str,...]
    is_numeric:bool = False
 
STANDARD_QUANTITIES: Dict[str, QuantityType]={
    "undefined": QuantityType(
        key = "undefined",
        label = "Undefined",
        units = (),
        symbols = (), 
        is_numeric = False,
    ),
    "ignore": QuantityType(
        key = "ignore",
        label = "Ignore",
        units = (),
        symbols = (),
        is_numeric = False,
    ),
   "density": QuantityType(
        key="density",
        label="Density",
        units=("kg/m³", "g/cm³", "lb/ft³"),
        symbols=("ρ",),
        is_numeric = True,
    ),
    "energy": QuantityType(
        key="energy",
        label="Energy",
        units=("BTU", "J", "cal", "hp-hr"),
        symbols=("E",),
        is_numeric = True,
    ),
    "force": QuantityType(
        key="force",
        label="Force",
        units=("lbf", "N", "dyne"),
        symbols=("F",),
        is_numeric = True,
    ),
    "length": QuantityType(
        key="length",
        label="Length",
        units=("m", "cm", "mm", "ft", "in", "mile"),
        symbols=("L",),
        is_numeric = True,
    ),
    "mass": QuantityType(
        key="mass",
        label="Mass",
        units=("kg", "g", "lbm", "lb", "ton"),
        symbols=("m",),
        is_numeric = True,
    ),
    "permeability": QuantityType(
        key="permeability",
        label="Permeability",
        units=("m²", "D", "mD"),
        symbols=("k",),
        is_numeric = True,
    ),
    "pressure": QuantityType(
        key="pressure",
        label="Pressure",
        units=("Pa", "bar", "psi", "kPa", "atm"),
        symbols=("P",),
        is_numeric = True,
    ),
    "temperature": QuantityType(
        key="temperature",
        label="Temperature",
        units=("K", "°C", "°F", "°R"),
        symbols=("T",),
        is_numeric = True,
    ),
    "viscosity": QuantityType(
        key="viscosity",
        label="Viscosity",
        units=("Pa·s", "P", "cP", "mPa·s"),
        symbols=("μ",),
        is_numeric = True,
    ),
    "volume_gas": QuantityType(
        key="volume_gas",
        label="Volume (Gas)",
        units=("m³", "cm³", "scf", "mscf", "mmscf", "bcf", "bcm"),
        symbols=("V",),
        is_numeric = True,
    ),
    "volume_liquid": QuantityType(
        key="volume_liquid",
        label="Volume (Liquid)",
        units=("m³", "cm³", "bbl", "Imp gal"),
        symbols=("V",),
        is_numeric = True,
    ),
    "mobility": QuantityType(
        key = "mobility",
        label = "Mobility",
        units = ("m²/(Pa.s)","D/P","mD/cP"),
        symbols = ("λ",),
        is_numeric = True,
    ),
    "text": QuantityType(
        key = "text",
        label = "Text",
        units = (),
        symbols = (),
        is_numeric = False,
    ),
    "well": QuantityType(
        key="well",
        label="Well",
        units=(),
        symbols=(),
        is_numeric = False,
    ),
}

@dataclass(frozen=True)
class UnitSystem:
    key: str
    label:str
    units_by_quantity: Dict[str,str]

SI_UNITS = UnitSystem(
    key="si",
    label="SI",
    units_by_quantity={
        "length": "m",
        "mass": "kg",
        "temperature": "K",
        "pressure": "Pa",
        "density": "kg/m³",
        "energy": "J",
        "force": "N",
        "volume_liquid": "m³",
        "volume_gas": "m³",
        "permeability": "m²",
        "viscosity": "Pa·s",
        "undefined": "",
        "ignore": "",
        "mobility": "m²/(Pa.s)",
        "text": "",
        "well": "",
    },
)

METRIC_UNITS = UnitSystem(
    key="metric_cgs",
    label="Metric",
    units_by_quantity={
        "length": "cm",
        "mass": "g",
        "temperature": "°C",
        "pressure": "bar",
        "density": "g/cm³",
        "energy": "cal",
        "force": "N",
        "volume_liquid": "cm³",
        "volume_gas": "cm³",
        "permeability": "D",
        "viscosity": "P",
        "undefined": "",
        "ignore": "",
        "mobility": "D/P",
        "text": "",
        "well":"",
    },
)

FIELD_UNITS = UnitSystem(
    key="field_us_oilfield",
    label="Field (US Oilfield)",
    units_by_quantity={
        "length": "ft",
        "mass": "lbm",
        "temperature": "°F",
        "pressure": "psi",
        "density": "lb/ft³",
        "energy": "BTU",
        "force": "lbf",
        "volume_liquid": "bbl",
        "volume_gas": "scf",
        "permeability": "mD",
        "viscosity": "cP",
        "undefined": "",
        "ignore": "",
        "mobility": "mD/cP",
        "text": "",
        "well":"",
    },
)

IMPERIAL_UNITS = UnitSystem(
    key="imperial_uk",
    label="Imperial (UK)",
    units_by_quantity={
        "length": "ft",
        "mass": "lb",
        "temperature": "°F",
        "pressure": "psi",
        "density": "lb/ft³",
        "energy": "BTU",
        "force": "lbf",
        "volume_liquid": "Imp gal",
        "volume_gas": "scf",
        "permeability": "mD",
        "viscosity": "cP",
        "undefined": "",
        "ignore": "",
        "mobility": "mD/cP",
        "text": "",
        "well":"",
    },
)

BUILT_IN_UNIT_SYSTEMS: Tuple[UnitSystem,...]= (
    SI_UNITS,
    METRIC_UNITS,
    FIELD_UNITS,
    IMPERIAL_UNITS
)

def get_project_default_units (project:ProjectDataManager, quantity_key:str)->str:
        if project is None: 
            return ""
        return project.current_unit_system.units_by_quantity.get (quantity_key,"")