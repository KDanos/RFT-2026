from __future__ import annotations

import inspect
import os
import sys

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtGui import QKeyEvent


def print_current_location_function(obj: QObject) -> None:
    """Debugging function to return the name of the function and parent class that has been activated.
        If the same print call is written in the function whose name one wants returned,
        then the expression in the first placeholder of the string literal should be {inspect.currentframe().f_code.co_name},
        without the '.f_back' attribute """
    print(
        f"You have entered the function {inspect.currentframe().f_back.f_code.co_name} "
        f"inside the class {obj.__class__.__name__}"
    )

def reload_app(entry_script: str | None = None) -> None:
    """Dev-only: replace this process with a fresh run of the entry script.

    Used so UI/code changes appear without closing the app manually.
    Delete this module's reload helpers (and any mixin usage) before production.

    Args:
        entry_script: Absolute path to the script to relaunch (usually main.py).
            Defaults to ``sys.argv[0]`` when the app was started as ``python main.py``.
    """
    python = sys.executable
    script_path = os.path.abspath(entry_script or sys.argv[0])
    os.execl(python, python, script_path)

class DevReloadMixin:
    """Dev-only mixin: hold A+F together to restart the app.

    Mix into the main window during development, e.g.
    ``class MainWindow(DevReloadMixin, MainWindowKD)``.

    Delete this class (and drop it from the main window bases) before production.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keys_down: set[int] = set()

    def keyPressEvent(self, event: QKeyEvent):
        """Dev-only: record pressed keys; A+F together reloads the app."""
        if event.isAutoRepeat():
            return
        self._keys_down.add(event.key())
        if Qt.Key.Key_A in self._keys_down and Qt.Key.Key_F in self._keys_down:
            reload_app()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        """Dev-only: clear released keys from the A+F chord tracker."""
        if event.isAutoRepeat():
            return
        self._keys_down.discard(event.key())
        super().keyReleaseEvent(event)
