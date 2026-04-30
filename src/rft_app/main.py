import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow,QLabel
from ui.main_window import Ui_MainWindow


class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle ("RFT/RCI Interpreter")
        self.setGeometry(1200, 400, 600,400)
        self.setWindowIcon(QIcon('resources/images/CY_LOGO_RGB.jpg'))
        self.setCentralWidget(QLabel("Lets get coding"))
        self.setupUi(self)

if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
