from PyQt6.QtWidgets import QTreeWidget, QWidget


from project import AnalysisObject


class AnalysisTree(QTreeWidget):
    def __init__(self,
                parent:QWidget| None = None,
                analysis:AnalysisObject|None = None 
                )->None:
        super().__init__(parent)