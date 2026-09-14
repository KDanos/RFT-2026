from PyQt6.QtWidgets import QMenu


class DepthMenuChart(QMenu):
    def __init__(self):
        super().__init__()

        self.addAction("a test")