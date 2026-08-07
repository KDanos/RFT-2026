

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





