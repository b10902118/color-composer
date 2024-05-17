# (c) Teigigutesiegel, 2021
# used code from https://gist.github.com/sjdv1982/75899d10e6983b878f63083e3c47b39b, copyright (c) 2017 Sjoerd de Vries
from PyQt5.QtWidgets import (
    QWidget,
    QSlider,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QLabel,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, QLineF, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QConicalGradient,
    QRadialGradient,
    QMouseEvent,
    QPen,
    QPixmap,
    QImage,
)

import math
import numpy as np
from PIL import Image

BG_COLOR = "#202020"
HALLOW = "#707070"


def pil_image_to_qpixmap(self, pil_image):
    # Convert the PIL Image to a QImage
    pil_image = pil_image.convert("RGB")
    data = np.array(pil_image)
    qimage = QImage(
        data, data.shape[1], data.shape[0], data.strides[0], QImage.Format_RGB888
    )

    # Convert the QImage to a QPixmap
    qpixmap = QPixmap.fromImage(qimage)

    return qpixmap


def qpixmap_to_pil_image(self, qpixmap):
    # Convert the QPixmap to a QImage
    qimage = qpixmap.toImage()

    # Convert the QImage to a PIL Image
    width = qimage.width()
    height = qimage.height()
    bytes_per_line = qimage.bytesPerLine()
    data = qimage.bits().asstring(height * bytes_per_line)
    pil_image = Image.frombytes("RGB", (width, height), data)

    return pil_image


class ColorCircle(QWidget):
    currentColorChanged = pyqtSignal(QColor)

    def __init__(
        self, parent=None, startupcolor: list = [255, 255, 255], margin=10
    ) -> None:
        super().__init__(parent=parent)
        self.radius = 0
        self.selected_color = QColor(
            startupcolor[0], startupcolor[1], startupcolor[2], 1
        )
        self.angle = 0
        # self.x = 0.5
        # self.y = 0.5
        # self.h = self.selected_color.hueF()
        # self.s = self.selected_color.saturationF()
        self.v = self.selected_color.valueF()
        self.margin = margin

        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)
        self.setStyleSheet(f"QWidget {{ background-color: {BG_COLOR}; }}")

    def resizeEvent(self, ev: QResizeEvent) -> None:
        size = min(self.width(), self.height()) - self.margin * 2
        self.radius = size / 2
        self.square = QRect(0, 0, size, size)
        self.square.moveCenter(self.rect().center())

    def paintEvent(self, ev: QPaintEvent) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        p = QPainter(self)
        p.setViewport(
            self.margin,
            self.margin,
            self.width() - 2 * self.margin,
            self.height() - 2 * self.margin,
        )
        hsv_grad = QConicalGradient(center, 0)
        for deg in range(360):
            col = QColor.fromHsvF(deg / 360, 1, self.v)
            hsv_grad.setColorAt(deg / 360, col)

        val_grad = QRadialGradient(center, self.radius)
        val_grad.setColorAt(0.0, QColor.fromHsvF(0.0, 0.0, self.v, 1.0))
        val_grad.setColorAt(1.0, Qt.transparent)

        p.setPen(Qt.transparent)
        p.setBrush(hsv_grad)
        p.drawEllipse(self.square)
        p.setBrush(val_grad)
        p.drawEllipse(self.square)

        # p.setPen(Qt.black)
        # p.setBrush(self.selected_color)
        # line = QLineF.fromPolar(self.radius * self.s, 360 * self.h + 90)
        # line.translate(self.rect().center())
        # p.drawEllipse(line.p2(), 10, 10)

        # make it ring by adding smaller circle
        inner_radius = self.radius - 30
        inner_square = QRectF(0, 0, 2 * inner_radius, 2 * inner_radius)
        inner_square.moveCenter(center)
        p.setBrush(QColor(BG_COLOR))
        # p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.drawEllipse(inner_square)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Template sectors
        # sector_radius = inner_radius - 1
        # sector_square = QRectF(0, 0, 2 * sector_radius, 2 * sector_radius)
        # sector_square.moveCenter(center)
        p.setBrush(QColor(HALLOW))  # Set the color of the sector
        # Span angle in 16ths of a degree (90 degrees)
        p.drawPie(inner_square, -int(self.angle * 16), 10 * 16)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def recalc(self) -> None:
        # self.selected_color.setHsvF(self.h, self.s, self.v)
        # self.currentColorChanged.emit(self.selected_color)
        self.repaint()

    # def map_color(self, x: int, y: int) -> QColor:
    #    line = QLineF(QPointF(self.rect().center()), QPointF(x, y))
    #    s = min(1.0, line.length() / self.radius)
    #    h = (line.angle() - 90) / 360 % 1.0
    #    return h, s, self.v

    def processMouseEvent(self, ev: QMouseEvent) -> None:
        x = ev.x() - self.rect().center().x()
        y = ev.y() - self.rect().center().y()
        theta = math.atan2(y, x)

        # Convert theta from radians to degrees and normalize to [0, 360)
        # not sure why need negative
        self.angle = (math.degrees(theta) + 360) % 360
        self.recalc()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        self.processMouseEvent(ev)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.processMouseEvent(ev)

    def setHue(self, hue: float) -> None:
        if 0 <= hue <= 1:
            self.h = float(hue)
            self.recalc()
        else:
            raise TypeError("Value must be between 0.0 and 1.0")

    def setSaturation(self, saturation: float) -> None:
        if 0 <= saturation <= 1:
            self.s = float(saturation)
            self.recalc()
        else:
            raise TypeError("Value must be between 0.0 and 1.0")

    def setValue(self, value: float) -> None:
        if 0 <= value <= 1:
            self.v = float(value)
            self.recalc()
        else:
            raise TypeError("Value must be between 0.0 and 1.0")

    def setColor(self, color: QColor) -> None:
        self.h = color.hueF()
        self.s = color.saturationF()
        self.v = color.valueF()
        self.recalc()

    def getHue(self) -> float:
        return self.h

    def getSaturation(self) -> float:
        return self.s

    def getValue(self) -> float:
        return self.v

    def getColor(self) -> QColor:
        return self.selected_color


class PhotoDisplayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        # Create a QLabel to display the image
        self.photo = QLabel()
        self.layout.addWidget(self.photo)

        # Create a button to load an image
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.browse_file)
        self.layout.addWidget(self.load_button)

    def browse_file(self):
        # Open a file dialog and get the selected file
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "",
            "Image files (*.jpg *.gif *.png)",
        )

        # Load and display the image
        self.load_image(file)

    def load_image(self, file):
        # Load and display the image
        pixmap = QPixmap(file)
        self.photo.setPixmap(pixmap)


class ColorCircleDialog(QWidget):
    currentColorChanged = pyqtSignal(QColor)

    def __init__(
        self, parent=None, width: int = 500, startupcolor: list = [255, 255, 255]
    ) -> None:
        super().__init__(parent=parent)
        self.resize(width, width)

        mainlay = QHBoxLayout()

        # Add the photo widget to the left side of the main layout
        photo = PhotoDisplayer()  # Replace this with your photo widget
        mainlay.addWidget(photo)
        # Create the right side layout
        rightlay = QVBoxLayout()

        # Add the ColorCircle widget to the right side layout
        wid = ColorCircle(self, startupcolor=startupcolor)
        wid.currentColorChanged.connect(lambda x: self.currentColorChanged.emit(x))
        rightlay.addWidget(wid)

        # Add another widget to the right side layout
        other_widget = QLabel()  # Replace this with your other widget
        rightlay.addWidget(other_widget)

        # Add the right side layout to the main layout
        mainlay.addLayout(rightlay)

        mainlay.setStretch(0, 3)
        mainlay.setStretch(1, 1)
        self.setLayout(mainlay)
        # wid.setMaximumSize(300, 300)
        # mainlay.addStretch(1)
        # mainlay.addWidget(wid)

        # fader = QSlider()
        # fader.setMinimum(0)
        # fader.setMaximum(511)
        # fader.setValue(511)
        # fader.valueChanged.connect(lambda x: wid.setValue(x / 511))
        # mainlay.addWidget(fader)

        self.setStyleSheet(f"QWidget {{ background-color: {BG_COLOR}; }}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = ColorCircleDialog()
    window.currentColorChanged.connect(lambda x: print(x.red(), x.green(), x.blue()))
    window.showMaximized()
    window.show()
    sys.exit(app.exec_())
