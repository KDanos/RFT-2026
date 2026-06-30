from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget
from qtpy.QtCore import QSignalBlocker

from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from utilities import create_table_view_frame
class TabularFrame(QFrame):
    column_unit_change = pyqtSignal(int, str, str) #column index, column header and new unit
    
    def __init__(self,
                parent:QWidget|None = None,
                project:ProjectDataManager|None= None,
                analysis: AnalysisObject|None = None, 
                view:AnalysisView|None= None,
                )->None:
        super().__init__(parent)
        
        self.project = project
        self.analysis = analysis

        self.view = view
        if analysis:
            self.dataset= analysis.analysis_dataset

        self._build_ui()

    
    #--------Public API--------

    def update_table(self):
        if hasattr(self, "table_frame"):    
            self.main_layout.removeWidget(self.table_frame)
            self.table_frame.setParent(None)
            self.table_frame.deleteLater()
        
        self._create_table()

    #--------Private UI--------

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self._create_table()

    def _update_table_units_combo_from_specs(self)->None:
        for c, spec in enumerate(self.view.column_specs):
            if not spec.unit:
                continue
            units_combo = self.table.cellWidget(0,c)
            idx = units_combo.findText(spec.unit)
            if idx >= 0:
                with QSignalBlocker(units_combo):
                    units_combo.setCurrentIndex(idx)

    def _link_table_units_combo_with_signal(self)->None:
        for c in range(self.table.columnCount()):
            widget = self.table.cellWidget(0,c)
            if widget is None:
                continue   
            widget.currentIndexChanged.connect(
                lambda _index, col=c:self.column_unit_change.emit(
                    col, 
                    self.table.horizontalHeaderItem(col).text(), 
                    self.table.cellWidget(0,col).currentText())
                    )

    def _create_table(self)->None:
        self.table_frame, self.table, update_columns_values = create_table_view_frame(
                                            self.view.df,
                                            self.view.column_specs, 
                                            self, 
                                            self.project )
        self.main_layout.addWidget(self.table_frame)
        self._update_table_units_combo_from_specs()
        self._link_table_units_combo_with_signal()
