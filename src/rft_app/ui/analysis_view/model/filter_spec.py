from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class FilterOperator(StrEnum):
    """Row-filter operators for analysis view table filtering."""

    GT = ">"
    LT = "<"
    EQ = "=="
    GEQ = ">="
    LEQ = "<="
    NEQ = "!="
    BETWEEN = "between"
    IN = "in"


@dataclass(frozen=True)
class FilterSpec:
    """One row-filter rule on a single column of view.df.

    value:
      - scalar for >, <, ==, >=, <=, !=
      - sequence of allowed values for in
      - lower bound when operator is between
    value2:
      - upper bound when operator is between
    """

    column_name: str
    operator: FilterOperator
    value: Any = None
    value2: Any = None
