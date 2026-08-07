
import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window.main_window import MainWindowKD
from utilities.development_functions import DevReloadMixin


class MainWindow(DevReloadMixin, MainWindowKD):
    """App main window.

    Dev-only: inherits DevReloadMixin (A+F reloads the process).
    Remove DevReloadMixin from the bases before shipping a production build.
    """

    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
