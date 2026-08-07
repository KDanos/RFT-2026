from PyQt6.QtWidgets import QButtonGroup, QFrame, QRadioButton,  QSpinBox, QTableWidget, QVBoxLayout,QHBoxLayout, QCheckBox
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from qtpy.QtWidgets import QLabel

from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from utilities import print_current_location_function
from ui.widgets import UnitsComboBox
from ui.filterable_table.custom_table_view import CustomTableView


class FilterableTable(QFrame):
    #Custom Signals
    column_unit_change = pyqtSignal(int, str, str) #column index, column header and new unit

    def __init__(
            self, 
            parent:QObject,
            project:ProjectDataManager, 
            analysis:AnalysisObject, 
            view:AnalysisView
            )->None:
        super().__init__(parent)

        self.project = project
        self.analysis = analysis
        self.view = view
        self.arithmetic_ops_src_model:str = "full"
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------
    def _build_ui(self)->None:

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        #Create the widgets frame on top
        self.widgets_frame = QFrame(self)
        self.main_layout.addWidget(self.widgets_frame)
        self.widgets_layout = QHBoxLayout(self.widgets_frame)
        
        # Define number of decimals to view
        self.decimals_container = QHBoxLayout()
        self.decimals_check_box = QCheckBox("Round decimals")
        self.decimals_check_box.setCheckState(Qt.CheckState.Checked)
        self.decimal_limit_spin = QSpinBox()
        self.decimal_limit_spin.setValue(1)
        self.decimal_limit_spin.setMaximum(10000)
        self.decimal_limit_spin.setEnabled(True)
        self.decimals_container.addWidget(self.decimals_check_box)
        self.decimals_container.addWidget(self.decimal_limit_spin)
        self.widgets_layout.addLayout(self.decimals_container)
        self.widgets_layout.addStretch()# pushes everything to the left
        
        # Ensure manual typing works in the decimals spinbox
        self.decimal_limit_spin.setReadOnly(False)
        self.decimal_limit_spin.lineEdit().setReadOnly(False)
        self.decimal_limit_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.decimal_limit_spin.setKeyboardTracking(False)
        
        # Add a toggle for the user to select filtering on visible or view data
        self.filtering_radio_layout= QVBoxLayout()
        
        self.filter_options_label = QLabel("Apply arithmetic operations to:")
        self.filter_options_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filtering_radio_layout.addWidget(self.filter_options_label)
        
        self.filtered_dataset_radio = QRadioButton("Filtered Dataset",self.widgets_frame)
        self.full_dataset_radio = QRadioButton("Full Dataset",self.widgets_frame)
        self.filtered_dataset_radio.setChecked(True)
        self.filter_options_group = QButtonGroup(self)
        self.filter_options_group.addButton(self.filtered_dataset_radio)
        self.filter_options_group.addButton(self.full_dataset_radio)
        self.filter_options_group.buttonClicked.connect(self._on_radio_button_change)
        
        self.radio_btn_layout = QHBoxLayout()
        self.radio_btn_layout.addWidget(self.full_dataset_radio)
        self.radio_btn_layout.addWidget(self.filtered_dataset_radio)
        self.filtering_radio_layout.addLayout(self.radio_btn_layout)

        self.widgets_layout.addLayout(self.filtering_radio_layout)

        #Create the table frame at the bottom and ad the tableview
        self.table_frame= QFrame(self)      
        self.table_layout = QVBoxLayout(self.table_frame)
        self.table_layout.setContentsMargins(0,0,0,0)
        self.table_layout.setSpacing(0)
        self.main_layout.addWidget(self.table_frame)       

        #Create the table itself
        self.table = CustomTableView(
                self, 
                self.project, 
                self.analysis, 
                self.view, 
                self.decimals_check_box,
                self.decimal_limit_spin)
        
        self.table_layout.addWidget(self.table,1)
    
    def _connect_signals(self):
        self.decimal_limit_spin.valueChanged.connect(self.refresh_display)
        self.decimals_check_box.toggled.connect(self.refresh_display)
        self.table.horizontalHeader().sectionResized.connect(self._resize_units_column)
    
    def _create_or_update_units_combos(self)->None:
        
        #Used only in update, rather than create on load.
        if hasattr(self, "units_table"):
            self.table_layout.removeWidget(self.units_table)
            self.units_table.deleteLater()
        
        self.units_table = QTableWidget(self.table_frame)
        column_count = self.view.df.shape[1]
        self.units_table.setColumnCount(column_count)
        self.units_table.setRowCount(1)
        self.units_table.setVerticalHeaderLabels([""])
        self.units_table.horizontalHeader().hide()
        
        for i in range(column_count):
            quantity_key = self.view.column_specs[i].quantity_key
            units_combo = UnitsComboBox(quantity_key, self.project)
            #Connect to a function to initiate the update in changing the units
            units_combo.currentIndexChanged.connect(lambda _, idx = i: self._on_units_change(idx))
            self.units_table.setCellWidget(0,i,units_combo)
            #Update the column_specs to reflect the units of the units_combo
            spec = self.view.column_specs[i]
            self.view.column_specs[i] = ColumnSpec(spec.name, spec.quantity_key, units_combo.currentText())
        self.table_layout.insertWidget(0,self.units_table)
        
        #Ensure the units table takes as little vertical space as possible and no scrolling appears
        self.units_table.resizeRowsToContents()
        row_height = self.units_table.rowHeight(0)
        frame = 2* self.units_table.frameWidth()
        self.units_table.setFixedHeight(row_height + frame)
        self.units_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.units_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _sync_units_table_column_widths(self)->None:
        data_cols = self.table.table_model.columnCount()
        units_cols = self.units_table.columnCount()
        sync_cols = min(data_cols, units_cols)
        
        for i in range(sync_cols):
            column_width = self.table.columnWidth(i)
            self.units_table.setColumnWidth(i,column_width)
        
        v_header_width = self.table.verticalHeader().width()
        self.units_table.verticalHeader().setFixedWidth(v_header_width)
       
    def _resize_units_column(self,idx:int)->None:  
        if not hasattr(self, "units_table"): #guard for initial load. No units_table is available when this function is called on load.
            return     
        column_width = self.table.columnWidth(idx)
        self.units_table.setColumnWidth(idx, column_width)

    def _on_units_change(self,idx:int)->None:
        combo = self.sender()
        if not isinstance(combo, UnitsComboBox):
            return
        
        spec = self.view.column_specs[idx]
        new_unit = combo.currentText()
        self.view.column_specs[idx] = ColumnSpec(spec.name, spec.quantity_key, new_unit)
        self.refresh_display()
        self.column_unit_change.emit(idx, spec.name, new_unit)

    def _on_radio_button_change(self, button:QRadioButton)->None:
        use_filtered = button is self.filtered_dataset_radio
        self.table.proxy_model.use_filtered_rows_for_stats = use_filtered
        self.arithmetic_ops_src_model = "filtered" if use_filtered else "full"
    
    #--------Public API--------
    def load_from_view(self)->None:
        self.table.load_from_view()
        self._create_or_update_units_combos()
        self._sync_units_table_column_widths()
    
    def refresh_display(self)->None:
        self.table.table_model.refresh_display()
        self.table.resizeColumnsToContents()
        self._sync_units_table_column_widths()

