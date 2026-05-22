"""
Pint-backed unit normalisation for the RFT project.

Design
------
- **Storage (DataFrame + ColumnSpec)**: numeric columns are kept in a **canonical**
  unit per ``quantity_key`` (SI-style internal representation).
- **Display / analysis**: convert magnitudes to the user's preferred unit (e.g. from
  ``UnitSystem.units_by_quantity``) with ``storage_to_display`` / ``series_storage_to_display``.

This module does **not** replace ``units_manager.py``: that file remains the catalogue
of quantity keys, labels, and combo-box unit strings. This module performs the
**numerical** conversions using Pint.

Integration sketch (data loader)
-------------------------------
After building ``imported_column_specs`` and before ``accept()``::

    from units.bobs_pint_unit_manager import (
        normalize_imported_dataframe,
        specs_with_storage_units,
    )
    df, specs = normalize_imported_dataframe(df, specs)
    # specs now have .unit set to the canonical storage label per column

For tables/plots::

    from units.bobs_pint_unit_manager import storage_to_display, get_preferred_app_unit
    target = get_preferred_app_unit("pressure", project.current_unit_system)
    v_display = storage_to_display(v_storage, "pressure", target)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterable

import pint

if TYPE_CHECKING:
    import pandas as pd

# ---------------------------------------------------------------------------
# Quantity keys that are never run through Pint (no dimension / non-numeric)
# ---------------------------------------------------------------------------
NON_PINT_QUANTITIES: frozenset[str] = frozenset(
    {"undefined", "ignore", "text", "well"}
)

# Canonical **Pint** unit string per quantity (internal storage).
# These must be mutually dimensionally consistent with every ``APP_UNIT_TO_PINT`` mapping.
CANONICAL_PINT_UNIT: dict[str, str] = {
    "length": "meter",
    "mass": "kilogram",
    "temperature": "kelvin",
    "pressure": "pascal",
    "density": "kilogram / meter**3",
    "volume_liquid": "meter**3",
    "volume_gas": "meter**3",
    "permeability": "meter**2",
    "viscosity": "pascal * second",
    "mobility": "meter**2 / pascal / second",
    "energy": "joule",
    "force": "newton",
}

# Human-facing unit string written to ``ColumnSpec.unit`` after normalisation.
# Kept aligned with ``SI_UNITS`` in ``units_manager.py`` so trees and reports stay consistent.
STORAGE_COLUMN_SPEC_UNIT: dict[str, str] = {
    "length": "m",
    "mass": "kg",
    "temperature": "K",
    "pressure": "Pa",
    "density": "kg/m³",
    "volume_liquid": "m³",
    "volume_gas": "m³",
    "permeability": "m²",
    "viscosity": "Pa·s",
    "mobility": "m²/(Pa.s)",
    "energy": "J",
    "force": "N",
}

# Map UI / ``units_manager`` strings to expressions Pint can parse.
APP_UNIT_TO_PINT: dict[str, str] = {
    # length
    "m": "meter",
    "cm": "centimeter",
    "mm": "millimeter",
    "ft": "foot",
    "in": "inch",
    "mile": "mile",
    # mass
    "kg": "kilogram",
    "g": "gram",
    "lbm": "lb",
    "lb": "lb",
    "ton": "metric_ton",
    # temperature
    "K": "kelvin",
    "°C": "degC",
    "°F": "degF",
    "°R": "rankine",
    # pressure
    "Pa": "pascal",
    "bar": "bar",
    "psi": "psi",
    "kPa": "kilopascal",
    "atm": "atm",
    # density
    "kg/m³": "kilogram / meter**3",
    "g/cm³": "gram / centimeter**3",
    "lb/ft³": "lb / foot**3",
    # volume
    "m³": "meter**3",
    "cm³": "centimeter**3",
    "bbl": "barrel",
    "Imp gal": "imperial_gallon",
    "scf": "scf",  # registered as ft**3 below (simplified)
    # permeability
    "m²": "meter**2",
    "D": "darcy",
    "mD": "millidarcy",
    # viscosity
    "Pa·s": "pascal * second",
    "P": "poise",
    "cP": "centipoise",
    "mPa·s": "millipascal * second",
    # mobility
    "m²/(Pa.s)": "meter**2 / (pascal * second)",
    "D/P": "darcy / poise",
    "mD/cP": "millidarcy / centipoise",
    # energy
    "J": "joule",
    "BTU": "Btu",
    "cal": "calorie",
    "hp-hr": "horsepower * hour",
    # force
    "N": "newton",
    "lbf": "pound_force",
    "dyne": "dyne",
}


def _build_registry() -> pint.UnitRegistry:
    ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
    # Simplified "standard cubic foot" — refine for reservoir engineering if needed.
    try:  # noqa: SIM105
        _ = ureg.Unit("scf")
    except pint.errors.UndefinedUnitError:
        ureg.define_unit("scf = foot**3")
    # Darcy if missing (SI bridge)
    try:
        _ = ureg.Unit("darcy")
    except pint.errors.UndefinedUnitError:
        ureg.define_unit("darcy = 9.869233e-13 * meter**2")
    try:
        _ = ureg.Unit("millidarcy")
    except pint.errors.UndefinedUnitError:
        ureg.define_unit("millidarcy = 1e-3 * darcy")

    return ureg


UREG: pint.UnitRegistry = _build_registry()


def app_unit_to_pint(app_unit: str) -> str:
    """Translate a string from the UI / ``units_manager`` to a Pint-parseable unit."""
    key = app_unit.strip()
    if key in APP_UNIT_TO_PINT:
        return APP_UNIT_TO_PINT[key]
    # Fallback: normalize Unicode multiplication / superscripts for simple expressions.
    normalized = (
        key.replace("·", " * ")
        .replace("²", "**2")
        .replace("³", "**3")
    )
    return normalized


def get_storage_pint_unit(quantity_key: str) -> str:
    if quantity_key not in CANONICAL_PINT_UNIT:
        raise KeyError(f"Unknown quantity for Pint storage: {quantity_key!r}")
    return CANONICAL_PINT_UNIT[quantity_key]


def get_column_spec_unit_after_normalize(quantity_key: str) -> str:
    """Unit string to store on ``ColumnSpec.unit`` after import normalisation."""
    if quantity_key in NON_PINT_QUANTITIES:
        return ""
    return STORAGE_COLUMN_SPEC_UNIT.get(quantity_key, get_storage_pint_unit(quantity_key))


def get_preferred_app_unit(quantity_key: str, unit_system: object | None) -> str:
    """Default display unit string for ``quantity_key`` from a ``UnitSystem`` preset."""
    if unit_system is None or quantity_key in NON_PINT_QUANTITIES:
        return ""
    return getattr(unit_system, "units_by_quantity", {}).get(quantity_key, "")


def needs_pint(quantity_key: str) -> bool:
    return quantity_key not in NON_PINT_QUANTITIES and quantity_key in CANONICAL_PINT_UNIT


def normalize_scalar(
    value: float | int,
    from_app_unit: str,
    quantity_key: str,
    *,
    ureg: pint.UnitRegistry = UREG,
) -> float:
    """Convert one numeric value from import units to canonical storage units."""
    if not needs_pint(quantity_key):
        return float(value)
    if from_app_unit is None or str(from_app_unit).strip() == "":
        raise ValueError(f"Missing source unit for quantity {quantity_key!r}")
    src = app_unit_to_pint(from_app_unit)
    dst = get_storage_pint_unit(quantity_key)
    q = ureg.Quantity(float(value), src)
    return float(q.to(dst).magnitude)


def storage_to_display(
    value: float | int,
    quantity_key: str,
    to_app_unit: str,
    *,
    ureg: pint.UnitRegistry = UREG,
) -> float:
    """Convert from canonical storage magnitude to a user-preferred unit."""
    if not needs_pint(quantity_key):
        return float(value)
    if not to_app_unit or not str(to_app_unit).strip():
        return float(value)
    src = get_storage_pint_unit(quantity_key)
    dst = app_unit_to_pint(to_app_unit)
    q = ureg.Quantity(float(value), src)
    return float(q.to(dst).magnitude)


def display_to_storage(
    value: float | int,
    quantity_key: str,
    from_app_unit: str,
    *,
    ureg: pint.UnitRegistry = UREG,
) -> float:
    """Convert a user-entered value in display units back to canonical storage."""
    if not needs_pint(quantity_key):
        return float(value)
    if not from_app_unit or not str(from_app_unit).strip():
        raise ValueError(f"Missing display unit for quantity {quantity_key!r}")
    src = app_unit_to_pint(from_app_unit)
    dst = get_storage_pint_unit(quantity_key)
    q = ureg.Quantity(float(value), src)
    return float(q.to(dst).magnitude)


def _maybe_float(x: object) -> float | None:
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str) and not x.strip():
        return None
    try:
        return float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def series_normalize_to_storage(
    series: pd.Series,
    from_app_unit: str,
    quantity_key: str,
    *,
    ureg: pint.UnitRegistry = UREG,
) -> pd.Series:
    """Vector-friendly normalisation: only numeric cells are converted; rest unchanged."""
    import pandas as pd

    if not needs_pint(quantity_key):
        return series.copy()

    out = series.copy()
    mask = series.map(_maybe_float).notna()
    if not mask.any():
        return out
    numeric = series[mask].map(lambda v: normalize_scalar(float(v), from_app_unit, quantity_key, ureg=ureg))
    out.loc[mask] = numeric
    return out


def series_storage_to_display(
    series: pd.Series,
    quantity_key: str,
    to_app_unit: str,
    *,
    ureg: pint.UnitRegistry = UREG,
) -> pd.Series:
    import pandas as pd

    if not needs_pint(quantity_key) or not to_app_unit or not str(to_app_unit).strip():
        return series.copy()

    out = series.copy()
    mask = series.map(_maybe_float).notna()
    if not mask.any():
        return out
    numeric = series[mask].map(
        lambda v: storage_to_display(float(v), quantity_key, to_app_unit, ureg=ureg)
    )
    out.loc[mask] = numeric
    return out


def specs_with_storage_units(specs: Iterable) -> list:
    """
    Return a new list of ColumnSpec-like objects with ``unit`` set to the canonical
    storage label. Requires ``ColumnSpec`` from ``project.models`` (name, quantity_key, unit).

    If specs are immutable dataclasses, caller should use ``replace()`` — this helper
    imports ColumnSpec and rebuilds instances.
    """
    from project.models import ColumnSpec

    new_specs: list[ColumnSpec] = []
    for spec in specs:
        qk = spec.quantity_key
        unit_label = spec.unit
        if needs_pint(qk):
            unit_label = get_column_spec_unit_after_normalize(qk)
        new_specs.append(ColumnSpec(spec.name, qk, unit_label))
    return new_specs


def normalize_imported_dataframe(
    df: "pd.DataFrame",
    column_specs: list,
    *,
    ureg: pint.UnitRegistry = UREG,
) -> tuple["pd.DataFrame", list]:
    """
    Normalise every Pint-backed column in ``df`` using parallel ``column_specs``.

    The original **user** unit for each column is read from ``spec.unit`` before it is
    overwritten; after this call, returned specs use storage units from
    ``STORAGE_COLUMN_SPEC_UNIT``.
    """
    from project.models import ColumnSpec

    if len(column_specs) != len(df.columns):
        raise ValueError(
            f"column_specs length {len(column_specs)} != {len(df.columns)} DataFrame columns"
        )

    out_df = df.copy()
    meta_specs: list = []
    for col_name, spec in zip(df.columns, column_specs, strict=True):
        qk = spec.quantity_key
        src_unit = spec.unit
        if col_name in out_df.columns and needs_pint(qk):
            out_df[col_name] = series_normalize_to_storage(
                out_df[col_name], src_unit, qk, ureg=ureg
            )

        if needs_pint(qk):
            meta_specs.append(
                ColumnSpec(spec.name, qk, get_column_spec_unit_after_normalize(qk))
            )
        else:
            meta_specs.append(ColumnSpec(spec.name, qk, spec.unit))

    return out_df, meta_specs


__all__ = [
    "APP_UNIT_TO_PINT",
    "CANONICAL_PINT_UNIT",
    "NON_PINT_QUANTITIES",
    "STORAGE_COLUMN_SPEC_UNIT",
    "UREG",
    "app_unit_to_pint",
    "display_to_storage",
    "get_column_spec_unit_after_normalize",
    "get_preferred_app_unit",
    "get_storage_pint_unit",
    "needs_pint",
    "normalize_imported_dataframe",
    "normalize_scalar",
    "series_normalize_to_storage",
    "series_storage_to_display",
    "specs_with_storage_units",
    "storage_to_display",
]
