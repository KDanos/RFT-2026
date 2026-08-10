

from dataclasses import dataclass
import math
from typing import Protocol

class FilterSpec(Protocol):
    """Anything used in active_filters must provide this.
    Used in type hints, to avoid listing all possible filter specs in the list of hints"""
    def pass_filter(self, cell_value: str) -> bool: ...


@dataclass
class NumberClause:
    operator:str
    value: float|int
    value_b: float|int | None = None # only for 'between' operator

@dataclass
class TextClause:
    label:str
    text:str

@dataclass
class FilterSpecNumber():
    clause1:NumberClause
    connector:str | None = None # and / or 
    clause2:NumberClause | None = None

    def pass_filter(self,cell_value:str)->bool:
        # Skip any rows that do not contain numbers
        try:
            number = float(cell_value) 
        except(TypeError, ValueError): 
            return False 
        
        # Check for clause 1 
        clause_1_result = self._test_a_clause(self.clause1, number)
        
        # Check for clause 2
        if self.clause2 is None:
            return clause_1_result
        clause_2_result = self._test_a_clause(self.clause2, number)
        
        #Final spec result
        if self.connector == "or":
            return clause_1_result or clause_2_result
        return clause_1_result and clause_2_result

    def _test_a_clause (self, clause:NumberClause, number:float|int)->bool:
        
        # Check and execute if the filter is a simple mathematical comparison
        if clause.operator in ['<','<=','>','>=','==','!=']:
            return self._check_filter_operator(clause.operator, clause.value, number)
        
        # Check and execute if the filter is a 'between' comparison
        if clause.operator == "between":
            return clause.value<= number <= clause.value_b

        return True 

    def _check_filter_operator(self, symbol:str, filter_value:float|int, number:float|int)->bool:
        
        if symbol == "<":
            if not (number < filter_value):
                return False
        elif symbol == "<=":
            if not (number <= filter_value):
                return False
        elif symbol == ">":
            if not (number > filter_value):
                return False
        elif symbol == ">=":
            if not (number >= filter_value):
                return False
        elif symbol == "==":
            if not math.isclose(number, filter_value, rel_tol=1e-9, abs_tol=1e-6):
                return False
        elif symbol == "!=":
            if math.isclose(number, filter_value, rel_tol=1e-9, abs_tol=1e-6):
                return False
        return True

@dataclass 
class FilterSpecNumberSpecial():
    operator:str
    value:float|int

    def pass_filter(self, cell_value:str)->bool:
        # Skip any rows that do not contain numbers
        try:
            number = float(cell_value) 
        except(TypeError, ValueError): 
            return False 
        
        if self.operator == "Top 10":
            return number >= self.value
        if self.operator == "Bottom 10":
            return number <= self.value
        if self.operator == "Below Average":
            return number <= self.value
        if self.operator == "Above Average":
            return number >= self.value        
        return True

@dataclass
class FilterSpecValues:
    values:set[str|float] #SI numbers or text strings from tree UserRole

    def pass_filter(self, cell_value:str)->bool:
        #Fast path = exact membership (works for text and identical floats)
        if cell_value in self.values:
            return True
        
         #Blank /NaN
        if cell_value is None or (isinstance(cell_value, float) and math.isnan(cell_value)):
            return "" in self.values or any(
                (isinstance(v, float) and math.isnan(v)) or v=="" for v in self.values
            )

        #Numeric Comparison
        try:
            number = float(cell_value)
        except (TypeError, ValueError):
            return str(cell_value) in {str(v) for v in self.values}

        for v in self.values:
            try:
                if math.isclose(number, float(v), rel_tol = 1e-9, abs_tol=1e-6):
                    return True
            except (TypeError, ValueError):
                continue
        return False

@dataclass
class FilterSpecText():
    clause1:TextClause
    connector:str | None = None # and / or 
    clause2:TextClause | None = None

    def pass_filter(self, cell_string:str)-> bool:
        clause1_result =  self.test_a_clause(self.clause1, cell_string)
        
        if not self.clause2:
            return clause1_result
        else:
            clause2_result = self.test_a_clause(self.clause2, cell_string)
            if self.connector == "or":
                return clause1_result or clause2_result
            else: return clause1_result and clause2_result


    def test_a_clause(self, clause:TextClause, cell_string: str)->bool:
        needle = str(clause.text).strip().casefold()
        check = clause.label
        if cell_string is None or (isinstance(cell_string, float) and math.isnan(cell_string)):
            haystack = ""
        else:
            haystack = str(cell_string).strip().casefold()
        
        
        if check == "Equals":
            return needle == haystack

        if check =="Does Not Equal":
            return needle != haystack

        if check == "Begins With":
            return haystack.startswith(needle)
        
        if check == "Ends With":
            return haystack.endswith(needle)

        if check == "Contains":
            return needle in haystack

        if check == "Does Not Contain":
            return not needle in haystack

        return False


def _serialize_scalar(value: float | int | str) -> float | int | str | None:
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _deserialize_scalar(value: float | int | str | None) -> float | int | str:
    if value is None:
        return float("nan")
    return value


def _number_clause_to_dict(clause: NumberClause) -> dict:
    return {
        "operator": clause.operator,
        "value": clause.value,
        "value_b": clause.value_b,
    }


def _number_clause_from_dict(data: dict) -> NumberClause:
    return NumberClause(
        operator=data["operator"],
        value=data["value"],
        value_b=data.get("value_b"),
    )


def _text_clause_to_dict(clause: TextClause) -> dict:
    return {"label": clause.label, "text": clause.text}


def _text_clause_from_dict(data: dict) -> TextClause:
    return TextClause(label=data["label"], text=data["text"])


def filter_spec_to_dict(spec: FilterSpec) -> dict:
    if isinstance(spec, FilterSpecNumber):
        return {
            "type": "number",
            "clause1": _number_clause_to_dict(spec.clause1),
            "connector": spec.connector,
            "clause2": _number_clause_to_dict(spec.clause2) if spec.clause2 else None,
        }
    if isinstance(spec, FilterSpecNumberSpecial):
        return {
            "type": "number_special",
            "operator": spec.operator,
            "value": spec.value,
        }
    if isinstance(spec, FilterSpecValues):
        return {
            "type": "values",
            "values": [_serialize_scalar(v) for v in spec.values],
        }
    if isinstance(spec, FilterSpecText):
        return {
            "type": "text",
            "clause1": _text_clause_to_dict(spec.clause1),
            "connector": spec.connector,
            "clause2": _text_clause_to_dict(spec.clause2) if spec.clause2 else None,
        }
    raise TypeError(f"Unsupported filter spec type: {type(spec)!r}")


def filter_spec_from_dict(data: dict) -> FilterSpec:
    spec_type = data["type"]
    if spec_type == "number":
        clause2 = data.get("clause2")
        return FilterSpecNumber(
            clause1=_number_clause_from_dict(data["clause1"]),
            connector=data.get("connector"),
            clause2=_number_clause_from_dict(clause2) if clause2 else None,
        )
    if spec_type == "number_special":
        return FilterSpecNumberSpecial(
            operator=data["operator"],
            value=data["value"],
        )
    if spec_type == "values":
        return FilterSpecValues(
            values={_deserialize_scalar(v) for v in data["values"]},
        )
    if spec_type == "text":
        clause2 = data.get("clause2")
        return FilterSpecText(
            clause1=_text_clause_from_dict(data["clause1"]),
            connector=data.get("connector"),
            clause2=_text_clause_from_dict(clause2) if clause2 else None,
        )
    raise ValueError(f"Unknown filter spec type: {spec_type!r}")

