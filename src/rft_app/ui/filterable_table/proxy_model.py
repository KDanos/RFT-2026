

from PyQt6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from ui.filterable_table.filter_specs import FilterSpecNumber


class ProxyFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None)->None:
        super().__init__(parent)
        self.active_filters:dict[int, FilterSpecNumber]={}
        # Access the Pandas Model 

    def filterAcceptsRow(self, source_row, source_parent:QModelIndex)->bool: 
        self.source_model = self.sourceModel()
        if len(self.active_filters)==0:
            return True

        for col,spec in self.active_filters.items():
            cell = self.source_model.data(    #please explain to me the syntac and function of this command
                self.source_model.index(source_row, col),
                Qt.ItemDataRole.DisplayRole
            )
            try:
                cell_value = float(cell) 
            except(TypeError, ValueError): # i pressume these catch scenarios where the cell is non numeric? Thats the typeError. is the valueError to catch none values?
                return False 

            if spec.operator == "<":
                if not (cell_value<spec.value):
                    return False
        return True 
       