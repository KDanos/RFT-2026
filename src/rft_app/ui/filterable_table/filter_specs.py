

from dataclasses import dataclass


@dataclass
class FilterSpecNumber():
    value: float|int
    operator:str