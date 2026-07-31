from enum import Enum
from PyQt6.QtWidgets import QComboBox

class NumberFilters(Enum):
    EQUALS = ("Equals","==","operator")
    DOESNOTEQUAL = ("Does Not Equal", "!=", "operator")
    GREATERTHAN = ("Greater Than", ">", "operator")
    GREATERTHANOREQUALTO = ("Greater Than Or Equal To", ">=", "operator")
    LESSTHAN = ("Less Than", "<", "operator")
    LESSTHANOREQUALTO = ("Less Than Or Equal To", "<=", "operator")
    
    BETWEEN = ("Between", "between", "special")
    TOP10 = ("Top 10", "top10", "special")
    ABOVEAVERAGE = ("Above Average", "above_average", "special")
    BELOWAVERAGE = ("Below Average", "below_average", "special")
    CUSTOMFILTER = ("Custom Filter", "custom", "special")

    def __init__(self, label:str, symbol:str, kind:str)->None:
        self.label = label
        self.symbol = symbol
        self.kind = kind

class NumberFilterCombo(QComboBox):
    def __init__(self,parent = None):
        super().__init__(parent)
        self._create_list_of_filters()

    def _create_list_of_filters(self)->None:
        # number_filter_list = [(entry.label, entry.symbol) for entry in NumberFilters]
        for entry in NumberFilters:
            self.addItem(entry.label, entry)

class TextFilterCombo(QComboBox):
    def __init__(self,parent = None):
        super().__init__(parent)

class AlphanumericFilterCombo(QComboBox):
    def __init__(self,parent = None):
        super().__init__(parent)