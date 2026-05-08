
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

from ui.main_window_KD import MainWindowKD


class MainWindow(MainWindowKD):
    def __init__(self):
        super().__init__()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())