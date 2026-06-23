from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox,QMenu, QTreeWidgetItem

from utilities import show_dataframe_table_dialog, show_log_table


if TYPE_CHECKING:
    from .tree_all_datasets import AllDataSetsTree


def on_all_dataset_tree_context_menu(tree:AllDataSetsTree,position:QPoint):

    item =tree.itemAt(position)
    if item is None: #to ensure that menu is only build on non-white space
        return


    if item.parent() is not None: #apply drop down menu only to top level items
        return
    
    #Create the drop down menu
    menu_actions = create_actions(tree, item)
    menu = QMenu(tree)
    for action in menu_actions:
        menu.addAction(action)
    
    menu.exec(tree.viewport().mapToGlobal(position))
    
def create_actions(tree,item)->list[QAction]:
    list_of_actions = []

    # Rename
    rename_action = QAction("Rename",tree)
    rename_action.triggered.connect(lambda _checked = False, item = item, tree = tree:rename_item(item, tree))
    list_of_actions.append(rename_action)
    
    #Delete
    delete_action = QAction("Delete", tree)
    delete_action.triggered.connect(lambda _checked =False, item = item, tree = tree: delete_item(item, tree))
    list_of_actions.append(delete_action)

    #Show import log
    show_import_log_action = QAction("Show Import log", tree)
    show_import_log_action.triggered.connect(lambda: show_import_log(item,tree))
    list_of_actions.append(show_import_log_action)

    #Show Data
    show_dataframe_action = QAction("Show Data", tree)
    show_dataframe_action.triggered.connect(lambda: show_data_table(item, tree))
    list_of_actions.append(show_dataframe_action)
    
    return list_of_actions

def rename_item(item:QTreeWidgetItem, tree:AllDataSetsTree)->None:
    if item.parent() is not None:
        return
    tree.setCurrentItem(item, 0)    #focus on the row
    tree.editItem(item,0)           #open inline editor (like F2)  

def delete_item(item:QTreeWidgetItem, tree:AllDataSetsTree)->None:
    if item.parent() is not None:#only remove top level items for now
        return
    
    confirmation =  QMessageBox.question(
                    tree, 
                    "Delete Function", f"""Please confirmt deletion of {item.text(0)}. 
                    \n This action is not reversible""",
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,) #default to No   
    if confirmation != QMessageBox.StandardButton.Yes:
        return
    tree._delete_dataset(item)

def show_import_log(item:QTreeWidgetItem, tree:AllDataSetsTree)->None:
    dataset = item.data(0, Qt.ItemDataRole.UserRole)
    name = dataset.name
    show_log_table(dataset, name, tree)

def show_data_table(item:QTreeWidgetItem, tree:AllDataSetsTree)-> None:
    dataset = item.data(0,Qt.ItemDataRole.UserRole)
    df= dataset.dataframe
    column_specs = dataset.column_specs
    title = dataset.name
    project= tree.project
    show_dataframe_table_dialog(df, column_specs, title, tree,project)
        