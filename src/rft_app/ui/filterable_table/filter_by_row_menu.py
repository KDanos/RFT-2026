from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QFrame, QLineEdit, QMenu, QPushButton, 
                            QWidgetAction, QVBoxLayout, QHBoxLayout)
from qtpy.QtWidgets import QDialog

from ui.filterable_table.proxy_model import ProxyFilterModel
from ui.filterable_table.filter_combos import NumberFilters
from ui.filterable_table.filter_window import FilteringWindow

class FilterByRowMenu(QMenu):
    def __init__(
            self, 
            column_index:int, 
            column_name:str, 
            proxy_model:ProxyFilterModel
            )->None:
        super().__init__()
        self.column_index = column_index
        self.column_name = column_name
        self.proxy_model = proxy_model
        self._build_ui()
        self._connect_actions_to_slots()
        
    def _build_ui(self):
        self._define_main_menu_actions()
        self._define_number_filter_actions()
        self._define_text_filter_actions()
        self._define_menus()
        self._build_number_filter_menu_options()
        self._build_text_filter_menu_options()
        self._build_main_menu_options()

    def _define_menus(self)->None:
        self.number_filter_menu = QMenu("Number Filters", self)
        self.text_filter_menu = QMenu("Text Filters", self)
    
    def _build_main_menu_options(self)->None:
        self.addAction(self.actionSortSmallesttoLargest)
        self.addAction(self.actionSortLargestoSmallest)
        self.addSeparator()
        self.addAction(self.clearFilter)
        self.addMenu(self.number_filter_menu)
        self.addMenu(self.text_filter_menu)
        self.addSeparator()
        self.tree_widget_action = self._create_filtering_tree_widget()
        self.addAction(self.tree_widget_action)
        
    def _build_number_filter_menu_options(self)->None:
        self.number_filter_menu.addAction(self.actionNumberEquals)
        self.number_filter_menu.addAction(self.actionNumberDoesNotEqual)
        self.number_filter_menu.addSeparator()
        self.number_filter_menu.addAction(self.actionGreaterThan)
        self.number_filter_menu.addAction(self.actionGreaterThanOrEqualTo)
        self.number_filter_menu.addAction(self.actionLessThan)
        self.number_filter_menu.addAction(self.actionLessThanOrEqualTo)
        self.number_filter_menu.addAction(self.actionBetween)
        self.number_filter_menu.addSeparator()
        self.number_filter_menu.addAction(self.actionTop10)
        self.number_filter_menu.addAction(self.actionAboveAverage)
        self.number_filter_menu.addAction(self.actionBelowAverage)
        self.number_filter_menu.addSeparator()
        self.number_filter_menu.addAction(self.actionCustomNumberFilter)
    
    def _build_text_filter_menu_options(self)->None:
        self.text_filter_menu.addAction(self.actionTextEquals)
        self.text_filter_menu.addAction(self.actionTextDoesNotEqual)
        self.text_filter_menu.addSeparator()
        self.text_filter_menu.addAction(self.actionBeginsWith)
        self.text_filter_menu.addAction(self.actionEndsWith)
        self.text_filter_menu.addSeparator()
        self.text_filter_menu.addAction(self.actionContains)
        self.text_filter_menu.addAction(self.actionDoesNotContain)
        self.text_filter_menu.addSeparator()
        self.text_filter_menu.addAction(self.actionCustomTextFilter)

    def _define_main_menu_actions(self)->None:
        self.actionSortSmallesttoLargest= QAction("Sort Smallest to Largest",self)
        self.actionSortLargestoSmallest = QAction("Sort Largest to Smallest",self)
        self.clearFilter = QAction("Clear Filter", self)

    def _define_number_filter_actions(self)->None:
        self.actionNumberEquals = QAction("Equals...", self)
        self.actionNumberEquals.setData(NumberFilters.EQUALS)
        
        self.actionNumberDoesNotEqual = QAction("Does Not Equal...", self)
        self.actionNumberDoesNotEqual.setData(NumberFilters.DOESNOTEQUAL)
        
        self.actionGreaterThan = QAction("Greater Than...", self)
        self.actionGreaterThan.setData(NumberFilters.GREATERTHAN)

        self.actionGreaterThanOrEqualTo = QAction("Greater Than Or Equal to...", self)
        self.actionGreaterThanOrEqualTo.setData(NumberFilters.GREATERTHANOREQUALTO)

        self.actionLessThan = QAction("Less Than...", self)
        self.actionLessThan.setData(NumberFilters.LESSTHAN)

        self.actionLessThanOrEqualTo = QAction("Less Than Or Equal To...", self)
        self.actionLessThanOrEqualTo.setData(NumberFilters.LESSTHANOREQUALTO)

        self.actionBetween = QAction("Between...", self)


        self.actionTop10 = QAction("Top 10...", self)


        self.actionAboveAverage = QAction("Above Average...", self)
        

        self.actionBelowAverage = QAction("Below Average...", self)
        

        self.actionCustomNumberFilter = QAction("Custom Filter...", self)

    def _define_text_filter_actions(self)->None:
        self.actionTextEquals = QAction("Equals...", self)
        self.actionTextDoesNotEqual = QAction("Does Not Equal...", self)
        self.actionBeginsWith = QAction("Begins With...", self)
        self.actionEndsWith = QAction("Ends With...", self)
        self.actionContains = QAction("Contains...", self)
        self.actionDoesNotContain = QAction("Does Not Contain...", self)
        self.actionCustomTextFilter = QAction("Custom Filter...", self)

    def _create_filtering_tree_widget(self)->QWidgetAction:
        panel = QFrame(self)
        main_layout = QVBoxLayout(panel) 
        main_layout.setContentsMargins(0,0,0,0)
        
        search_bar = QLineEdit(panel)
        search_bar.setPlaceholderText("Search")
        tree_frame = QFrame(panel)

        main_layout.addWidget(search_bar)
        main_layout.addWidget(tree_frame)

        #Add the ok and cancel buttons
        ok_btn = QPushButton("OK", panel)
        ok_btn.clicked.connect(self._on_clicked_ok)
        cancel_btn=QPushButton("Cancel", panel)
        cancel_btn.clicked.connect(self._on_clicked_cancel)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        main_layout.addLayout(buttons_layout)
        action = QWidgetAction(self)
        action.setDefaultWidget(panel)
        return action

    def _connect_actions_to_slots(self):
        for action in self.actions():
            action.triggered.connect(lambda checked=False, a=action:self._on_action(a.text())) #why do i need the checked = False argument after lambda? Where does that come from?
        for action in self.number_filter_menu.actions():
            action.triggered.connect(lambda checked = False, action=action : self._launch_number_filtering_window(action))
        for action in self.text_filter_menu.actions():
            action.triggered.connect(lambda checked=False, a=action:self._on_action(a.text()))

    def _on_action(self, action_name:str)->None:
        print(action_name, self.column_index)

    def _on_clicked_ok(self):
        print ("OK has been selected")

    def _on_clicked_cancel(self):
        print ("Cancel has been selected")

    def _launch_number_filtering_window(self, action:QAction)->None:
        
        filter_name = action.data().label if action.data() else ""
        
        #is a gate required here if filter_name = "", to return
        window = FilteringWindow(self, self.column_name, filter_name)
        if window.exec() == QDialog.DialogCode.Accepted:
            new_spec = window.result_spec
            self.proxy_model.active_filters[self.column_index]=new_spec
            # Command the proxy model to re-run the filterAcceptsRow method
            self.proxy_model.invalidateFilter() 
        
    