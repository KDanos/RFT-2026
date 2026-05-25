

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QVBoxLayout, QWidget,QHBoxLayout
from qtpy.QtWidgets import QFrame, QPushButton



class AnalysisWidget(QWidget):
    def __init__(self, parent:QWidget|None = None)->None:
        super().__init__(parent)

        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_vertical_splitter = QSplitter()

        #Widget Frame
        widget_frame = QFrame(self)
        widget_layout = QVBoxLayout(widget_frame)
        btn1 = QPushButton("placeholder 1")
        btn2 = QPushButton("placeholder 2")
        widget_layout.addWidget(btn1)
        widget_layout.addWidget(btn2)
        
        #Main Frame
        main_frame = QFrame(self)
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_splitter = QSplitter(Qt.Orientation.Vertical)
        main_frame_layout.addWidget(main_frame_splitter)

        #Tabular Frame
        tabular_frame = QFrame(main_frame_splitter)
        
        #Graphical Frame
        graphical_frame = QFrame(main_frame_splitter)
        
        #Add frames to the main panel layout
        main_frame_splitter.addWidget(graphical_frame)
        main_frame_splitter.addWidget(tabular_frame)

        #Add the frames to main splitter
        main_vertical_splitter.addWidget(widget_frame)
        main_vertical_splitter.addWidget(main_frame)
        main_vertical_splitter.setSizes([1000,5000])
        main_layout.addWidget(main_vertical_splitter)