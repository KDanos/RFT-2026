

from typing import List
from dataclasses import dataclass, field
import datetime


@dataclass(frozen=True)
class ColumnSpec:
    """Metadata for a single column of an imported DataFrame

    Stored alongside the DataFrame (not inside it). The DataFrame holds only alpha-numeric or empty values. 
    Columnspec records what those values mean (Quantiy) and in which units they were imported
    """
    name:str
    quantity_key:str
    unit: str

