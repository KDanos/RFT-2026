
import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window.main_window import MainWindowKD
from utilities.development_functions import DevReloadMixin


class MainWindow(DevReloadMixin, MainWindowKD):

    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
