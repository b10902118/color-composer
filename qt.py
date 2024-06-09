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
    QFrame,
    QRubberBand,
    QStyleOptionRubberBand,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, QLineF, pyqtSignal, QPoint, QSize
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
    QIcon,
    QPalette,
)

import math
import numpy as np
from PIL import Image
from PIL.ImageQt import toqpixmap
from harmony import find_best_template, binary_partition, shift_color

BG_COLOR = "#202020"
HALLOW = "#707070"


def pil_image_to_qpixmap(pil_image):
    # Convert the PIL Image to a QImage
    pil_image = pil_image.convert("RGB")
    data = np.array(pil_image)
    qimage = QImage(
        data, data.shape[1], data.shape[0], data.strides[0], QImage.Format_RGB888
    )

    # Convert the QImage to a QPixmap
    qpixmap = QPixmap.fromImage(qimage)

    return qpixmap


def qpixmap_to_pil_image(qpixmap):
    # Convert the QPixmap to a QImage
    qimage = qpixmap.toImage()

    # Convert the QImage to a PIL Image
    width = qimage.width()
    height = qimage.height()
    bytes_per_line = qimage.bytesPerLine()
    data = qimage.bits().asstring(height * bytes_per_line)
    pil_image = Image.frombytes("RGB", (width, height), data)

    return pil_image


class Sector:
    st: int
    sz: int

    def __init__(self, size, start):
        self.st = int(start / 256 * 360)
        self.sz = int(size / 256 * 360)


class Template:
    sectors: list[Sector]

    def __init__(self, sizes, starts) -> None:
        self.sectors = [Sector(size, start) for size, start in zip(sizes, starts)]


from harmony import template_params, template_params_dict
from harmony import Template as Htemplate

print(template_params_dict)


templates = {param[0]: Template(param[1], param[2]) for param in template_params}


def draw_template(target, type: str, inner_radius: int, p: QPainter = None):
    if not p:
        p = QPainter(target)
    inner_square = QRectF(0, 0, 2 * inner_radius, 2 * inner_radius)
    inner_square.moveCenter(target.center)
    p.setBrush(QColor(HALLOW))  # Set the color of the sector
    for sector in templates[type].sectors:
        p.drawPie(
            inner_square,
            int((-getattr(target, "angle", 0) + sector.st) * 16),  # TODO must angle
            sector.sz * 16,
        )


class ColorCircle(QWidget):
    currentColorChanged = pyqtSignal(QColor)
    center: QPointF

    def __init__(
        self, parent=None, startupcolor: list = [255, 255, 255], margin=10
    ) -> None:
        super().__init__(parent=parent)
        self.radius = 0
        self.selected_color = QColor(
            startupcolor[0], startupcolor[1], startupcolor[2], 1
        )
        self.v = self.selected_color.valueF()

        self.margin = margin
        self.angle = 0
        # self.center = QPointF(self.width() / 2, self.height() / 2)
        self.center = self.rect().center()
        self.currentSector = None

        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)
        self.setStyleSheet(f"QWidget {{ background-color: {BG_COLOR}; }}")

    def paintEvent(self, ev: QPaintEvent) -> None:
        p = QPainter(self)
        p.setPen(Qt.transparent)  # no frame
        p.setViewport(
            self.margin,
            self.margin,
            self.width() - 2 * self.margin,
            self.height() - 2 * self.margin,
        )

        inner_radius = self.radius - 30

        def draw_circle(color, radius):
            square = QRectF(0, 0, 2 * radius, 2 * radius)
            square.moveCenter(self.center)

            p.setBrush(color)
            p.drawEllipse(square)

        def draw_hue_circle():
            hsv_grad = QConicalGradient(self.center, 0)
            for deg in range(360):
                col = QColor.fromHsvF(deg / 360, 1, self.v)
                hsv_grad.setColorAt(deg / 360, col)

            val_grad = QRadialGradient(self.center, self.radius)
            val_grad.setColorAt(0.0, QColor.fromHsvF(0.0, 0.0, self.v, 1.0))
            val_grad.setColorAt(1.0, Qt.transparent)

            draw_circle(hsv_grad, self.radius)
            draw_circle(val_grad, self.radius)
            # make it ring by adding smaller circle
            draw_circle(QColor(BG_COLOR), inner_radius)

            # p.setCompositionMode(QPainter.CompositionMode_SourceOver)

        draw_hue_circle()
        if self.currentSector:
            draw_template(self, self.currentSector, inner_radius, p)

    def resizeEvent(self, ev: QResizeEvent) -> None:
        size = min(self.width(), self.height()) - self.margin * 2
        self.center = self.rect().center()
        self.radius = size / 2
        self.square = QRect(0, 0, size, size)
        self.square.moveCenter(self.center)

    def processMouseEvent(self, ev: QMouseEvent) -> None:
        x = ev.x() - self.rect().center().x()
        y = ev.y() - self.rect().center().y()
        theta = math.atan2(y, x)

        # Convert theta from radians to degrees and normalize to [0, 360)
        # not sure why need negative
        self.angle = (math.degrees(theta) + 360) % 360
        print(self.angle)
        self.repaint()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        self.processMouseEvent(ev)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.processMouseEvent(ev)

    def changeSector(self, sector):
        self.currentSector = sector
        self.update()


class CustomRubberBand(QRubberBand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set pen and brush for custom color
        pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)  # Red border with 2px width
        # brush = QBrush(QColor(255, 0, 0, 50))  # Red with 50% opacity
        painter.setPen(pen)
        # painter.setBrush(brush)

        painter.drawRect(self.rect())


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)  # Set alignment to center
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.selected = False
        self.subx = 0
        self.suby = 0
        self.subw = 0
        self.subh = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        pixmap = self.pixmap()
        if self.rubberBand.isVisible() and pixmap is not None:
            rect = self.rubberBand.geometry()
            # aligned center
            pw = pixmap.width()
            ph = pixmap.height()
            ox = self.width() / 2 - pw / 2
            oy = self.height() / 2 - ph / 2
            ex = ox + pw
            ey = oy + ph
            rx = rect.x()
            ry = rect.y()
            rex = rx + rect.width()
            rey = ry + rect.height()
            # print(f"Selection rectangle: {rect}")
            self.subx = int(min(max(rx, ox), ex) - ox)
            self.suby = int(min(max(ry, oy), ey) - oy)
            self.subw = int(min(max(rex, ox), ex) - ox - self.subx)
            self.subh = int(min(max(rey, oy), ey) - oy - self.suby)
            if self.subw > 0 and self.subh > 0:
                self.selected = True
            else:
                self.selected = False
            print(
                f"Selection rectangle: {self.subx} {self.suby} {self.subw} {self.subh}"
            )


class PhotoDisplayer(QWidget):
    def __init__(self, colorCircle: ColorCircle, parent=None):
        super().__init__(parent)
        self.colorCircle = colorCircle
        self.pil_image = None

        self.layout = QVBoxLayout(self)

        # Create a QLabel to display the image
        self.photo = ImageLabel()
        self.layout.addWidget(self.photo)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        # Create a button to load an image
        self.load_button = QPushButton("Load")
        self.load_button.setStyleSheet(
            f"background-color: {HALLOW}; font-weight: bold;"
        )
        self.load_button.clicked.connect(self.browse_file)
        self.button_layout.addWidget(self.load_button)

        # Create a button to optimize the image
        self.optimize_button = QPushButton("Optimize")
        self.optimize_button.setStyleSheet(
            f"background-color: {HALLOW}; font-weight: bold;"
        )
        self.optimize_button.clicked.connect(self.optimize_image)
        self.button_layout.addWidget(self.optimize_button)

        # Create a button to save the image
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(
            f"background-color: {HALLOW}; font-weight: bold;"
        )
        self.save_button.clicked.connect(self.save_image)
        self.button_layout.addWidget(self.save_button)

        # self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

    def save_image(self):
        if self.pil_image is None:
            self.warning("No image loaded")
            return
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "All Files (*);;JPEG Files (*.jpeg);;PNG Files (*.png)",
            options=options,
        )
        if file_name:
            self.pil_image.save(file_name)

    # def mousePressEvent(self, event):
    #    if event.button() == Qt.LeftButton:
    #        self.origin = QPoint(event.pos())
    #        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
    #        self.rubberBand.show()

    # def mouseMoveEvent(self, event):
    #    if not self.origin.isNull():
    #        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    # def mouseReleaseEvent(self, event):
    #    if event.button() == Qt.LeftButton:
    #        # self.rubberBand.hide()
    #        # Here you can get the final selection rectangle
    #        rect = self.rubberBand.geometry()
    #        print(f"Selection rectangle: {rect}")

    def browse_file(self):
        # Open a file dialog and get the selected file
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "",
            "Image files (*.jpg *.gif *.png)",
        )

        if not file:
            return
        # Load and display the image
        self.pil_image = Image.open(file)
        self.display_image()

    def display_image(self):
        pixmap = pil_image_to_qpixmap(self.pil_image)
        # Display the QPixmap
        self.photo.setPixmap(pixmap)

    def setColorWheel(self, t, angle):
        self.colorCircle.currentSector = t
        self.colorCircle.angle = angle
        self.colorCircle.repaint()

    def warning(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText("<b><FONT COLOR='#f0f0f0'>" + message + "</FONT></b>")
        msg_box.setStyleSheet(
            """
        QPushButton {
            color: white;
            font-weight: bold;
            background-color: #505050;
        }
    """
        )
        msg_box.exec_()

    def optimize_image(self):
        # Convert the PIL Image to a NumPy array and convert to HSV
        if self.pil_image is None:
            self.warning("No image loaded")
            return
        hsv = np.array(self.pil_image.convert("HSV"))
        # only crop the subimage
        if self.photo.selected:
            sub_hsv = hsv[
                self.photo.suby : self.photo.suby + self.photo.subh,
                self.photo.subx : self.photo.subx + self.photo.subw,
            ]
            arr_shape = sub_hsv.shape
        else:
            sub_hsv = hsv
            arr_shape = hsv.shape
        H, S, V = np.reshape(sub_hsv, (-1, 3)).T.astype(np.int32)

        # Find the best harmonic template
        if self.colorCircle.currentSector is None:
            best_template = find_best_template(H, S)
            print(f"Best harmonic template: {best_template.name} {best_template.alpha}")
        else:
            print(
                *template_params_dict[self.colorCircle.currentSector],
                int((-self.colorCircle.angle / 360 * 256) % 256),
                self.colorCircle.angle,
            )
            best_template = Htemplate(
                *template_params_dict[self.colorCircle.currentSector],
                int((-self.colorCircle.angle / 360 * 256) % 256),
            )

        # Partition the hues and shift the colors
        partition = binary_partition(H, best_template)
        nH = shift_color(H, partition, best_template)

        # Convert the harmonized hues back to HSV
        new_hsv = np.reshape(
            np.stack([nH, S, V]).T,
            arr_shape,
        )

        if self.photo.selected:
            hsv[
                self.photo.suby : self.photo.suby + self.photo.subh,
                self.photo.subx : self.photo.subx + self.photo.subw,
            ] = new_hsv
        else:
            hsv = new_hsv
        # Convert the harmonized image back to a PIL Image and display it
        self.pil_image = Image.fromarray(hsv.astype(np.uint8), mode="HSV").convert(
            "RGB"
        )
        qpixmap = pil_image_to_qpixmap(self.pil_image)
        self.photo.setPixmap(qpixmap)
        self.photo.rubberBand.hide()
        self.photo.selected = False
        print("done")
        self.setColorWheel(best_template.name, int(-best_template.alpha / 256 * 360))


class SectorButton(QPushButton):
    margin = 2

    def __init__(self, type, parent=None):
        super().__init__(parent)
        # self.setFixedSize(120, 120)
        self.type = type
        self.center = self.rect().center()
        size = min(self.width(), self.height())
        self.radius = size / 2
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QColor(HALLOW))
        square = QRectF(0, 0, self.radius * 2, self.radius * 2)
        square.moveCenter(self.center)
        p.drawRect(square)
        p.setPen(QColor(BG_COLOR))
        small_square = QRectF(
            self.margin,
            self.margin,
            self.radius * 2 - self.margin,
            self.radius * 2 - self.margin,
        )
        square.moveCenter(self.center)
        p.drawRect(small_square)
        if self.type is not None:
            draw_template(self, self.type, self.radius, p)

    def resizeEvent(self, event):
        self.setIconSize(self.size())
        self.center = self.rect().center()
        size = min(self.width(), self.height()) - self.margin * 2
        self.radius = size / 2


class SevenButtonWidget(QWidget):
    def __init__(self, colorCircle: ColorCircle, parent=None):
        super().__init__()

        # Create the layout
        layout = QVBoxLayout()

        # Create two rows of buttons
        for r in [["i", "V", "L", "I"], ["T", "Y", "X", None]]:
            row = QHBoxLayout()
            for t in r:  # 4 buttons in the first row
                button = SectorButton(t)
                button.clicked.connect(lambda _, t=t: colorCircle.changeSector(t))
                row.addWidget(button)

            layout.addLayout(row)

        # Set the layout
        self.setLayout(layout)
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)


class MainWindow(QWidget):
    currentColorChanged = pyqtSignal(QColor)

    def __init__(
        self, parent=None, width: int = 500, startupcolor: list = [255, 255, 255]
    ) -> None:
        super().__init__(parent=parent)
        self.resize(width, width)

        mainlay = QHBoxLayout()

        colorCircle = ColorCircle(self, startupcolor=startupcolor)
        photo = PhotoDisplayer(colorCircle)  # Replace this with your photo widget
        # Add the photo widget to the left side of the main layout
        mainlay.addWidget(photo)
        # Create the right side layout
        rightlay = QVBoxLayout()

        # Add the ColorCircle widget to the right side layout
        rightlay.addWidget(colorCircle)

        # Add another widget to the right side layout
        SectorButtons = SevenButtonWidget(
            colorCircle
        )  # Replace this with your other widget
        rightlay.addWidget(SectorButtons)

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
        self.setWindowIcon(QIcon("./icon.jpg"))
        self.setWindowTitle("Color Composer")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = MainWindow()
    # window.currentColorChanged.connect(lambda x: print(x.red(), x.green(), x.blue()))
    window.showMaximized()
    window.show()
    sys.exit(app.exec_())
