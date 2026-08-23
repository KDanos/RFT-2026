# Units module

The units package has two modules. Keep **catalogue / UI strings** in `units_manager.py` and **numeric conversion** in `units_normalisation.py`.

## 1. `units_manager.py`

- **`QuantityType`** / **`STANDARD_QUANTITIES`**: quantity keys (`length`, `volume_gas`, …), human labels, **unit strings shown in combos** (`units` tuple), and optional symbols.
- **`UnitSystem`** / **`SI_UNITS`**, **`METRIC_UNITS`**, **`FIELD_UNITS`**, **`IMPERIAL_UNITS`**: default **display** unit per quantity when the user picks a unit system for the project (not every combo option).
- **`BUILT_IN_UNIT_SYSTEMS`**: tuple of those presets for the UI.

Non-numeric quantities (`text`, `well`) have empty `units` and are not converted with Pint.
Column skip on import uses a UI-only `"Ignore"` option in the project data loader (not a `STANDARD_QUANTITIES` entry).

## 2. `units_normalisation.py`

- **`SI_STORAGE_BY_QUANTITY`**: canonical **storage** unit label per quantity (written to `ColumnSpec.unit` after import). Numeric data in the project DataFrame is stored in these units.
- **`APP_UNIT_TO_PINT`**: maps **combo / app strings** → Pint-parseable expressions (`"ft"` → `"foot"`, `"D"` → `"darcy"`, `"m³"` → `"meter**3"`).
- **`UNITS_ADDITIONAL_TO_PINT`**: custom units Pint does not ship (or not with your definition). Each entry is `name → (base_pint_unit, multiplier)`; `_build_registry()` calls `registry.define(...)` (Pint ≥ 0.24) and **`APP_UNIT_TO_PINT.setdefault(name, name)`** when the combo label equals the registry name.
- **`UREG`**: single shared `UnitRegistry` (built at import).
- **`normalise_from_user_units(user_unit, quantity_type, value)`**: import direction (user unit → SI storage).
- **`convert_from_normalised_to_user_units(user_output_unit, quantity_type, value)`**: display direction (storage → user unit).

Reference only (not wired): `bobs_pint_unit_manager.py`.

---

## Data flow

```text
Import (data loader):
  quantity_combo → quantity_key
  units_combo    → user_unit
  → normalise_from_user_units(...)
  → DataFrame values in SI storage; ColumnSpec.unit = identify_si_storage_unit(quantity_key)

Display (tables / plots / analysis):
  project unit system or chosen unit → user_output_unit
  → convert_from_normalised_to_user_units(...)
```

---

## Adding a **new quantity** (e.g. `flowrate_gas`)

1. **`units_manager.py` — `STANDARD_QUANTITIES`**  
   Add a `QuantityType` with `key`, `label`, `units=(...)`, `symbols=(...)`.  
   List every unit string the import UI may offer for that quantity.

2. **`units_manager.py` — each `UnitSystem` in `BUILT_IN_UNIT_SYSTEMS`**  
   Add the same `quantity_key` to `units_by_quantity` in **`SI_UNITS`**, **`METRIC_UNITS`**, **`FIELD_UNITS`**, and **`IMPERIAL_UNITS`** (use `""` if not applicable).  
   Include **`energy`** and **`force`** in `SI_UNITS` if you add those quantities (they exist in storage but were missing from SI presets).

3. **`units_normalisation.py` — `SI_STORAGE_BY_QUANTITY`**  
   Set the SI storage label (e.g. `"length"` → `"m"`). Use `""` for non-Pint quantities.

4. **`units_normalisation.py` — `APP_UNIT_TO_PINT`**  
   Add a row for **every** string in the new `QuantityType.units` tuple where the app label ≠ Pint name (same as existing quantities).

5. **Pint registry**  
   If any new unit is not in default Pint (or needs a custom definition), add it to **`UNITS_ADDITIONAL_TO_PINT`** in **dependency order** (e.g. `scf` before `mscf`).  
   If the combo string equals the registry name (`"bcf"` → `"bcf"`), you do **not** need a duplicate line in `APP_UNIT_TO_PINT` — `setdefault` runs at import.

6. **Verify in REPL** (from project root, `sys.path` includes `src`):

   ```python
   from rft_app.units.units_normalisation import (
       UREG, app_unit_to_pint,
       normalise_from_user_units, convert_from_normalised_to_user_units,
   )
   normalise_from_user_units("ft", "length", 5000)
   convert_from_normalised_to_user_units("ft", "length", 1524)
   ```

7. **Wire the data loader** (`data_loader_project.py`): after building the DataFrame and column specs, normalise numeric columns and set each spec’s `.unit` to `identify_si_storage_unit(quantity_key)`.

---

## Adding **new units** to an **existing** quantity (e.g. `mscf` on `volume_gas`)

1. **`units_manager.py` — `STANDARD_QUANTITIES`**  
   Add the string to that quantity’s `units` tuple (exact spelling used in the combo).

2. **`APP_UNIT_TO_PINT`** — only if the label differs from the Pint/registry name  
   Examples: `"D"` → `"darcy"`, `"ft"` → `"foot"`.  
   Skip if the label is the same as the registry name and you use **`UNITS_ADDITIONAL_TO_PINT`** (auto `setdefault`).

3. **`UNITS_ADDITIONAL_TO_PINT`** — if Pint does not know the unit  
   Example: `"mscf": ("scf", 1e3)` after `"scf"` is defined.  
   Use [Pint defining units](https://pint.readthedocs.io/en/stable/advanced/defining.html) and `registry.define("name = multiplier * base")` via the table.

4. **Unit systems** — optional  
   Update `FIELD_UNITS` / etc. only if the new unit should be a **project default**, not merely an import option.

5. **REPL** — `app_unit_to_pint("new_unit")` and `UREG.Quantity(1, "new_unit").to("meter**3")` (or the storage unit for that quantity).

You do **not** change `SI_STORAGE_BY_QUANTITY` when adding units to an existing quantity (storage unit stays e.g. `m³` for `volume_gas`).

---

## Quick reference

| Location | Purpose |
|----------|---------|
| `STANDARD_QUANTITIES[].units` | Combo options in data loader |
| `UnitSystem.units_by_quantity` | Default display unit per quantity |
| `SI_STORAGE_BY_QUANTITY` | Stored unit label + normalisation target |
| `APP_UNIT_TO_PINT` | App string → Pint (required for aliases) |
| `UNITS_ADDITIONAL_TO_PINT` | Custom registry definitions + auto map when name matches |

## Common mistakes

- Putting only the registry definition without adding the string to **`QuantityType.units`** (combo never shows it).
- Forgetting **`"D"` / `"mD"`** style aliases in `APP_UNIT_TO_PINT` (registry has `darcy`, UI shows `D`).
- Using `define_unit` — removed in Pint 0.24; use **`registry.define(...)`** (already wrapped in `_add_new_unit_to_pint_registry`).
- Defining `mscf` before `scf` in `UNITS_ADDITIONAL_TO_PINT` (order matters when chaining off `scf`).
