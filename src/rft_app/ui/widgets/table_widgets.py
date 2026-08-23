from PyQt6 import QtWidgets

from project import ProjectDataManager

from units import STANDARD_QUANTITIES

class UnitsComboBox(QtWidgets.QComboBox):
    def __init__(self,
                quantity_key:str,
                project:ProjectDataManager
                )->None:
        super().__init__()
        #Set the initial units list
        self.update_units_list(quantity_key)
        self.set_default_unit(project)

    def update_units_list(self, quantity_key:str)->None:
        self.quantity_key = quantity_key
        self.quantity_object = STANDARD_QUANTITIES.get(quantity_key)
        self.clear()
        if self.quantity_object is None:
            return
        self.addItems(self.quantity_object.units)
        
    def set_default_unit(self,project:ProjectDataManager=None)->None:
        if project is None:
            return
        default_unit = project.current_unit_system.units_by_quantity.get(self.quantity_key,"")
        if not default_unit:
            return
        idx = self.findText(default_unit)
        if idx >= 0:
            self.setCurrentIndex(idx)



        


    
