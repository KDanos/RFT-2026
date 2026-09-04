from enum import Enum

from PyQt6.QtWidgets import QComboBox


class NumberFilters(Enum):
    EQUALS = ("Equals", "==", "operator")
    DOESNOTEQUAL = ("Does Not Equal", "!=", "operator")
    GREATERTHAN = ("Greater Than", ">", "operator")
    GREATERTHANOREQUALTO = ("Greater Than Or Equal To", ">=", "operator")
    LESSTHAN = ("Less Than", "<", "operator")
    LESSTHANOREQUALTO = ("Less Than Or Equal To", "<=", "operator")

    BETWEEN = ("Between", "between", "operator")
    TOP10 = ("Top 10", "top10", "special")
    BOTTOM10 = ("Bottom 10", "bottom10", "special")
    ABOVEAVERAGE = ("Above Average", "above_average", "special")
    BELOWAVERAGE = ("Below Average", "below_average", "special")

    def __init__(self, label: str, symbol: str, kind: str) -> None:
        self.label = label
        self.symbol = symbol
        self.kind = kind


class TextFilters(Enum):
    EQUALS = ("Equals")
    DOESNOTEQUAL = ("Does Not Equal")
    BEGINSWITH = ("Begins With")
    ENDSWITH = ("Ends With")
    CONTAINS = ("Contains")
    DOESNOTCONTAIN = ("Does Not Contain")

    def __init__(self, label: str) -> None:
        self.label = label


class NumberFilterCombo(QComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Set project variables
        # (none)

        # Set module variables
        # (none)

        # Initialisation methods
        self._create_list_of_filters()

    #--------Private UI--------

    def _create_list_of_filters(self) -> None:
        for entry in NumberFilters:
            self.addItem(entry.label, entry)

    #--------Public API--------
    # No public methods: callers use standard QComboBox API.


class TextFilterCombo(QComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Set project variables
        # (none)

        # Set module variables
        # (none)

        # Initialisation methods
        self._create_list_of_filters()

    #--------Private UI--------

    def _create_list_of_filters(self) -> None:
        for entry in TextFilters:
            self.addItem(entry.label, entry)

    #--------Public API--------
    # No public methods: callers use standard QComboBox API.
