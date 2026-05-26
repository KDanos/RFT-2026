
from tkinter import Toplevel
from typing import Iterable
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
import pandas as pd


def unique_name(
    name:str="",
    existing: Iterable[str]|None=None
    )->str:
    
    """ Create a name as unique identifier
        Returns a string that is not included in iterable list"""
    
    existing = existing or ()
    taken = set (existing)
    n = (name or "").strip()
    
    #Check if the desired name is not use and apply it   
    if n and n not in taken:
        return n

    #Create naming options with the smallest possible index and the prefered name, and check if it is free
    i = 0
    candidate = f"{n}_{i}"
    while candidate in taken:
        i +=1
        candidate = f"{n}_{i}"
    return candidate
    
def is_numeric(value)-> bool: 
    if value is None:
        return False
    if isinstance(value,float) and pd.isna(value):
        return False
    if isinstance(value,(int,float)):
        return True
    if not isinstance(value,str):
        return False
    try:
        float(value.strip())
        return True
    except ValueError:
        return False
    
def get_tree_top_level_item_by_name(tree:QTreeWidget, name:str)->QTreeWidgetItem:
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        if item.text(0)==name:
            return item
    return None
    
def get_tree_item_by_name(tree:QTreeWidget, top_level_item:QTreeWidgetItem, name:str)->QTreeWidgetItem:

    it = QTreeWidgetItemIterator(top_level_item)
    while node := it.value():
        if node.text(0)==name:
            return node
        it += 1
    return None