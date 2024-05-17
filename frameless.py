import sys
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
)


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super(CustomTitleBar, self).__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Customize as needed
        self.title = QLabel("Custom Title Bar")
        self.title.setFixedHeight(30)
        self.btnClose = QPushButton("X")
        self.btnMinimize = QPushButton("-")

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.btnMinimize)
        self.layout.addWidget(self.btnClose)

        self.btnClose.clicked.connect(parent.close)
        self.btnMinimize.clicked.connect(parent.showMinimized)

        self.setLayout(self.layout)
        self.start = QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            end = self.mapToGlobal(event.pos())
            movement = end - self.start
            self.parent().move(self.parent().pos() + movement)
            self.start = end


class CustomWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 400, 300)

        self.vbox = QVBoxLayout()
        self.titleBar = CustomTitleBar(self)
        self.vbox.addWidget(self.titleBar)
        self.vbox.addStretch(-1)
        self.setLayout(self.vbox)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomWindow()
    window.show()
    sys.exit(app.exec_())
