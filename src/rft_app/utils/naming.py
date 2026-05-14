
from typing import Iterable


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
    

    