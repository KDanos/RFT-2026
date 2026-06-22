
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QTreeWidgetItem
from qtpy.QtWidgets import QMenu, QMessageBox, QTreeWidget

from project import AnalysisObject, AnalysisView
from utilities.global_functions import show_dataframe_table

# from ui.widgets import AnalysesTree 


def on_all_analyses_tree_context_menu(tree:QTreeWidget, position:QPoint)->None:
    item = tree.itemAt(position)
    if item is None: # to ensure that the menu is only build on non-whitespace
        return

    # Create 3 drop down menus, depending on the position of the tree
    menu_analysis = QMenu(tree)
    menu_all_views = QMenu(tree)
    menu_single_view = QMenu (tree)

    if item.parent() is None:
        menu = menu_analysis
        menu_actions = create_analysis_menu_actions(tree, item)
    elif item.text(0)=="Analysis Views:":
        menu = menu_all_views
        menu_actions = create_all_views_menu_actions(tree, item)
    elif item.parent().text(0)=="Analysis Views:":
        menu = menu_single_view
        menu_actions = create_single_view_menu_actions(tree,item)
    else:
        return
    
    for action in menu_actions:
        menu.addAction(action)
    menu.exec(tree.viewport().mapToGlobal(position))

def create_analysis_menu_actions(tree,item)->list[QAction]:
    list_of_actions = []
    # Rename
    rename_analysis_action = QAction("Rename",tree)
    rename_analysis_action.triggered.connect(lambda: rename_analysis(item, tree))
    list_of_actions.append(rename_analysis_action)

    # Delete
    delete_analysis_action = QAction("Delete",tree)
    delete_analysis_action.triggered.connect(lambda: delete_analysis(item, tree))
    list_of_actions.append(delete_analysis_action)

    # Show Data
    show_data_table_action= QAction("Show Data", tree)
    show_data_table_action.triggered.connect(lambda: show_data(item, tree))
    list_of_actions.append(show_data_table_action)

    list_of_actions.extend(create_all_views_menu_actions(tree, item, list_of_actions))
    return list_of_actions

def create_all_views_menu_actions(tree, item, list_of_actions=[])->list[QAction]:
    list_of_actions = []
    # Show All
    show_all_views_action = QAction("Show all views", tree)
    show_all_views_action.triggered.connect (lambda: show_all_views(item,tree))
    list_of_actions.append(show_all_views_action)
    
    # Hide All
    hide_all_views_action = QAction("Hide all views", tree)
    hide_all_views_action.triggered.connect(lambda: hide_all_views(item, tree))
    list_of_actions.append(hide_all_views_action)

    # Add a view
    add_view_action = QAction("Add a new view", tree)
    add_view_action.triggered.connect(lambda: add_a_view(item, tree))
    list_of_actions.append(add_view_action)

    return list_of_actions

def create_single_view_menu_actions(tree, item)->list[QAction]:
    list_of_actions = []
    # Rename
    rename_view_action = QAction("Rename",tree)
    rename_view_action.triggered.connect(lambda:rename_view(item, tree))
    list_of_actions.append(rename_view_action)

    # Delete
    delete_view_action = QAction("Delete",tree)
    delete_view_action.triggered.connect(lambda: delete_view(item,tree))
    list_of_actions.append(delete_view_action)

    # Show view
    show_single_view_action = QAction("Show", tree)
    show_single_view_action.triggered.connect (lambda: show_single_view(item,tree))
    list_of_actions.append(show_single_view_action)
    
    # Hide view
    hide_single_view_action = QAction("Hide", tree)
    hide_single_view_action.triggered.connect(lambda: hide_single_view(item,tree))
    list_of_actions.append(hide_single_view_action)

    return list_of_actions

# ---------------SLOTS---------------
def rename_analysis(item:QTreeWidgetItem, tree:QTreeWidget)->None:
    if item.parent() is not None:
        return
    tree.setCurrentItem(item,0) # focus on the row
    tree.editItem(item, 0)      # same as pressing F2

def delete_analysis(item:QTreeWidgetItem,tree:QTreeWidget)->None:
    if item.parent() is not None:
        return
    reply = QMessageBox.question(
        tree,
        "Delete Analysis", 
        f"Delete Analysis: {item.text(0)}?\nThis action is not reversible!",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )

    if reply != QMessageBox.StandardButton.Yes:
        return
    tree._delete_analysis(item)
        
def show_all_views(item:QTreeWidgetItem,tree:QTreeWidget)->None:

    # Drill to the top to get the analysis object
    while item.parent() is not None:
        item = item.parent()
    
    analysis = item.data(0, Qt.ItemDataRole.UserRole)
    for view in analysis.analysis_views:
        view.is_visible = True
   
    tree.project.mark_modified()
    tree.analysis_visibility_changed.emit()

def hide_all_views(item: QTreeWidget, tree: QTreeWidget)->None:
        # Drill to the top to get the analysis object
    while item.parent() is not None:
        item = item.parent()
    
    analysis = item.data(0, Qt.ItemDataRole.UserRole)
    for view in analysis.analysis_views:
        view.is_visible = False
   
    tree.project.mark_modified()
    tree.analysis_visibility_changed.emit()
    
def rename_view(item:QTreeWidgetItem, tree:QTreeWidget)->None:
    view = item.data(0,Qt.ItemDataRole.UserRole)
    if view is None or not isinstance(view, AnalysisView):
        return
    tree.setCurrentItem(item,0) # focus on the row
    tree.editItem(item, 0)      # same as pressing F2

def delete_view(item:QTreeWidgetItem, tree: QTreeWidget)->None:

    top_level_item = item
    # Drill to the top to identify the analysis
    while top_level_item.parent() is not None:
        top_level_item = top_level_item.parent()
    
    view = item.data(0,Qt.ItemDataRole.UserRole)
    if view is None:
        return
    
    analysis = top_level_item.data(0, Qt.ItemDataRole.UserRole)
    analysis.analysis_views.remove(view)
    tree.project.mark_modified()
    tree.analysis_visibility_changed.emit()

def show_single_view(item:QTreeWidgetItem, tree:QTreeWidget)->None:
    view = item.data(0,Qt.ItemDataRole.UserRole)
    if view is None:
        return
    view.is_visible=True
    tree.project.mark_modified()
    tree.analysis_visibility_changed.emit()   

def hide_single_view(item:QTreeWidgetItem, tree:QTreeWidget)->None:
    view = item.data(0,Qt.ItemDataRole.UserRole)
    if view is None:
        return
    view.is_visible=False
    tree.project.mark_modified()
    tree.analysis_visibility_changed.emit()   

def add_a_view(item:QTreeWidgetItem,tree:QTreeWidget)->None:
   
    while item.parent() is not None:
        item = item.parent()
    
    analysis = item.data(0, Qt.ItemDataRole.UserRole)
    tree.new_view_requested.emit(analysis)

def show_data(item:QTreeWidgetItem, tree:QTreeWidget)->None:
    obj = item.data(0, Qt.ItemDataRole.UserRole)
    if not isinstance(obj, AnalysisObject):
        return 
    
    df = obj.analysis_dataset.dataframe
    specs = obj.analysis_dataset.column_specs
    name = obj.analysis_dataset.name
    project = tree.project
    
    show_dataframe_table(df, specs, name, tree.parent, project)