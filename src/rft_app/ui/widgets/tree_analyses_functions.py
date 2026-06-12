
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QAction
from qtpy.QtWidgets import QMenu, QMessageBox, QTreeWidget
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
    rename_analysis_action.triggered.connect(rename_analysis)
    list_of_actions.append(rename_analysis_action)

    # Delete
    delete_analysis_action = QAction("Delete",tree)
    delete_analysis_action.triggered.connect(delete_analysis)
    list_of_actions.append(delete_analysis_action)

    return list_of_actions

def create_all_views_menu_actions(tree, item)->list[QAction]:
    list_of_actions = []
    # Show All
    show_all_views_action = QAction("Show All", tree)
    show_all_views_action.triggered.connect (show_all_views)
    list_of_actions.append(show_all_views_action)
    
    # Hide All
    hide_all_views_action = QAction("Hide All", tree)
    hide_all_views_action.triggered.connect(hide_all_views)
    list_of_actions.append(hide_all_views_action)

    return list_of_actions

def create_single_view_menu_actions(tree, item)->list[QAction]:
    list_of_actions = []
    # Rename
    rename_view_action = QAction("Rename",tree)
    rename_view_action.triggered.connect(rename_view)
    list_of_actions.append(rename_view_action)

    # Delete
    delete_view_action = QAction("Delete",tree)
    delete_view_action.triggered.connect(delete_view)
    list_of_actions.append(delete_view_action)

    # Show view
    show_single_view_action = QAction("Show", tree)
    show_single_view_action.triggered.connect (show_single_view)
    list_of_actions.append(show_single_view_action)
    
    # Hide view
    hide_single_view_action = QAction("Hie", tree)
    hide_single_view_action.triggered.connect(hide_single_view)
    list_of_actions.append(hide_single_view_action)

    return list_of_actions

# ---------------SLOTS---------------
def rename_analysis()->None:
    QMessageBox.information("Menu items", "Rename Analysis")

def delete_analysis()->None:
    QMessageBox.information("Menu items", "Delete Analysis")

def show_all_views()->None:
    QMessageBox.information("Menu items", "Show all")

def hide_all_views()->None:
    QMessageBox.information("Menu items", "Hide all")

def rename_view()->None:
    QMessageBox.information("Menu items", "Rename view")

def delete_view()->None:
    QMessageBox.information("Menu items", "Delete View")

def show_single_view()->None:
    QMessageBox.information("Menu items", "Show View")

def hide_single_view()->None:
    QMessageBox.information("Menu items", "Hide View")