import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow,QLabel
from ui.main_window import Ui_MainWindow
from ui.widgets.data_loader import DataLoaderDialog


class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('resources/images/CY_LOGO_RGB.jpg'))
        self.setupUi(self)
        
        # Define the ratio between the project panel and analysis panel
        self.mainSplitter.setSizes([1000,5000])

        #Connect the data loader to the menu action
        self.actionLoadData.triggered.connect(self.loadData)
    
    def loadData(self):
        self.data_load_window = DataLoaderDialog()


if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
