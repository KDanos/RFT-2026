"""
Central Type of units for the project
Create two classes, QuanityType and UnitSystem
"""


from dataclasses import dataclass
from typing import Dict, FrozenSet, Tuple


@dataclass (frozen = True)
class QuantityType:
    key:str
    label:str
    units:Tuple[str,...]
    symbols:Tuple[str,...]
 
STANDARD_QUANTITIES: Dict[str, QuantityType]={
   "density": QuantityType(
        key="density",
        label="Density",
        units=("kg/m³", "g/cm³", "lb/ft³"),
        symbols=("ρ",),
    ),
    "energy": QuantityType(
        key="energy",
        label="Energy",
        units=("BTU", "J", "cal", "hp-hr"),
        symbols=("E",),
    ),
    "force": QuantityType(
        key="force",
        label="Force",
        units=("lbf", "N", "dyne"),
        symbols=("F",),
    ),
    "length": QuantityType(
        key="length",
        label="Length",
        units=("m", "cm", "mm", "ft", "in", "mile"),
        symbols=("L",),
    ),
    "mass": QuantityType(
        key="mass",
        label="Mass",
        units=("kg", "g", "lbm", "lb", "ton"),
        symbols=("m",),
    ),
    "permeability": QuantityType(
        key="permeability",
        label="Permeability",
        units=("m²", "D", "mD"),
        symbols=("k",),
    ),
    "pressure": QuantityType(
        key="pressure",
        label="Pressure",
        units=("Pa", "bar", "psi", "kPa", "atm"),
        symbols=("P",),
    ),
    "temperature": QuantityType(
        key="temperature",
        label="Temperature",
        units=("K", "°C", "°F", "°R"),
        symbols=("T",),
    ),
    "viscosity": QuantityType(
        key="viscosity",
        label="Viscosity",
        units=("Pa·s", "P", "cP", "mPa·s"),
        symbols=("μ",),
    ),
    "volume_gas": QuantityType(
        key="volume_gas",
        label="Volume (Gas)",
        units=("m³", "cm³", "scf"),
        symbols=("V",),
    ),
    "volume_liquid": QuantityType(
        key="volume_liquid",
        label="Volume (Liquid)",
        units=("m³", "cm³", "bbl", "Imp gal"),
        symbols=("V",),
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
        "volume_liquid": "m³",
        "volume_gas": "m³",
        "permeability": "m²",
        "viscosity": "Pa·s",
    },
)

METRIC_UNITs = UnitSystem(
    key="metric_cgs",
    label="Metric",
    units_by_quantity={
        "length": "cm",
        "mass": "g",
        "temperature": "°C",
        "pressure": "bar",
        "density": "g/cm³",
        "volume_liquid": "cm³",
        "volume_gas": "cm³",
        "permeability": "D",
        "viscosity": "P",
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
        "volume_liquid": "bbl",
        "volume_gas": "scf",
        "permeability": "mD",
        "viscosity": "cP",
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
        "volume_liquid": "Imp gal",
        "volume_gas": "scf",
        "permeability": "mD",
        "viscosity": "cP",
    },
)
