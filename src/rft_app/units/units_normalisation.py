import pint


#Define the normalized unit for each quantity type: 
SI_STORAGE_BY_QUANTITY = {
    # Numeric — canonical SI storage (same labels as combos / ColumnSpec)
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
    # Non-Pint / no storage unit
    "undefined": "",
    "ignore": "",
    "text": "",
    "well": "",
}

#Identify the unit in which normalisation (in SI) will take place, based on the quantity type
def identify_si_storage_unit(quantity_key:str)->str:
    return SI_STORAGE_BY_QUANTITY.get(quantity_key,"")

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

#Function to convert the app units to pint units, using APP_UNIT_TO_PINT dictionary above
def app_unit_to_pint(app_unit:str)->str:
    key = app_unit.strip()
    if not key:
        raise ValueError("Empty unit string")
    if key in APP_UNIT_TO_PINT:
        return APP_UNIT_TO_PINT[key] 
    raise KeyError(f"Unknown app unit: {app_unit!r}")

#Developer defined dictionary of units that do no exist in pint and need to be added to the registry
UNITS_ADDITIONAL_TO_PINT:dict[str, tuple[str, float]]= {
    #List all the units that the project should be able to handle and are currently
    #not in the pint registry
    
    # Gas Volume:
    "scf":("foot**3",1),
    "mscf":("scf", 1e3),
    "mmscf":("scf", 1e6),
    "bcf":("scf", 1e9),
    "bcm":("meter**3", 1e9),
    #Permeability
    "darcy":("meter**2", 9.869233e-13),
    "millidarcy":("darcy", 1e-3),
}

#Function to add developer defined units to the pint registry
def _add_new_unit_to_pint_registry(
    key:str, 
    pint_unit:str, 
    multiplier:float,
    registry:pint.UnitRegistry
    )->None:
    
    try:
        _ = registry.Unit(key)
    except pint.errors.UndefinedUnitError:
        registry.define(f"{key} = {multiplier} * {pint_unit}")
    APP_UNIT_TO_PINT.setdefault(key,key)

#Function to loop through the UNITS_ADDITIONAL_TO_PINT and add them to the pint registry
def _build_registry()->pint.UnitRegistry:
    
    """One share Pint registry for the app, with oilfield units Pint does not ship."""
    ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
    
    #Update the registry to include the units defined in UNITS_ADDITIONAL_TO_PINT
    for key, (pint_unit, multiplier) in UNITS_ADDITIONAL_TO_PINT.items():
        _add_new_unit_to_pint_registry(key, pint_unit, multiplier, ureg)
    
    return ureg

#Create the registry instance
UREG: pint.UnitRegistry = _build_registry()

#Function to normalise a value to SI units for storage
def normalise_from_user_units (user_unit:str,quantity_type:str, value:float)->float:

    #Identify the SI unit for storage
    si_storage_unit = identify_si_storage_unit(quantity_type) #could be "m", for example ("length"->"m")
    if quantity_type not in SI_STORAGE_BY_QUANTITY:
        raise ValueError(f"""Unknown quantity_type {quantity_type!r} 
                        \n Please update the SI_STORAGE_BY_QUANTITY dictionary""")
    if not si_storage_unit:#error catcher in case that that float is returned with empty unit string (like "well", "text", etc.)
        return float(value)
    pint_storage_unit = app_unit_to_pint(si_storage_unit) #has to be "meter", for exampe ("m"->"meter")
    
    #Convert the user input unit to pint input unit
    pint_input_unit = app_unit_to_pint(user_unit) #convert from "ft" to "foot", for example ("ft"->"foot")

    #Make the converstion
    result = UREG.Quantity(value, pint_input_unit)
    #Extract and return the numeric element of the result
    si_value = float(result.to(pint_storage_unit).magnitude)
    return si_value

#Function to present normalised SI units to user selected unit
def convert_from_normalised_to_user_units(user_output_unit:str, quantity_type:str, value:float)->float:

    #Identify the SI unit for storage
    si_storage_unit = identify_si_storage_unit(quantity_type) #could be "m", for example ("length"->"m")
    if quantity_type not in SI_STORAGE_BY_QUANTITY:
        raise ValueError(f"""Unknown quantity_type {quantity_type!r} 
                        \n Please update the SI_STORAGE_BY_QUANTITY dictionary""")
    if not si_storage_unit:#error catcher in case that that float is returned with empty unit string (like "well", "text", etc.)
        return float(value)
    pint_storage_unit = app_unit_to_pint(si_storage_unit) #has to be "meter", for exampe ("m"->"meter")
    
    #Convert the user view unit to pint unit
    
    pint_output_unit = app_unit_to_pint(user_output_unit) #convert from "ft" to "foot", for example ("ft"->"foot")

    #Make the converstion
    result = UREG.Quantity(value, pint_storage_unit)
    #Extract and return the numeric element of the result
    display_value = float(result.to(pint_output_unit).magnitude)
    return display_value