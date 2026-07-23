from PyQt6.QtCore import QObject

import inspect


def print_current_location_function(obj:QObject)->None:
    """Debugging function to return the name of the function and parent class that has been activated.
        If the same print call is written in the function whose name one wants returned, 
        then the expression in the first placeholder of the string literal should be {inspect.currentframe().f_code.co_name}, 
        without the '.f_back' attribute """
    print (f"You have entered the function {inspect.currentframe().f_back.f_code.co_name} inside the class {obj.__class__.__name__}")