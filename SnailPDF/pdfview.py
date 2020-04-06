import fitz
from PIL import Image, ImageQt

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from PySide2.QtCore import Qt

from SnailPDF import util


class EmptyPage(fitz.Page):
    """Sentry page for empty page, as fitz.Page doesn't have a default constructor
    """
    def __init__(self):
        pass

    def bound(self):
        return fitz.Rect(0, 0, 1, 1)

    def __del__(self):
        pass


EMPTY_PAGE = EmptyPage()


def render_fitz_page(
    page: fitz.Page, zoom: float, pixel_ratio: float, clip: fitz.Rect = None
) -> QtGui.QPixmap:
    scale_ratio = zoom * pixel_ratio
    pix = page.getPixmap(matrix=fitz.Matrix(scale_ratio, scale_ratio), clip=clip)
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    img = ImageQt.ImageQt(img)
    img.setDevicePixelRatio(pixel_ratio)
    return img


def centered_coord(
    bound_size: QtCore.QSize, content_size: QtCore.QSize
) -> QtCore.QPoint:
    margin_size = (bound_size - content_size) / 2
    x = margin_size.width()
    y = margin_size.height()
    return QtCore.QPoint(x, y)


class PDFPageView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page: fitz.Page = EMPTY_PAGE
        self.preview_page: fitz.Page = EMPTY_PAGE
        self.zoom_level: float = 1.0

    def set_zoom_level(self, value: float):
        self.zoom_level = value

    def set_page(self, page):
        self.page = page
        self.preview_page = EMPTY_PAGE
        self.zoom_to_fit_page()

    def set_preview_page(self, page):
        self.preview_page = page

    def zoom_to_fit_page(self):
        page_width = self.page.bound().width
        page_height = self.page.bound().height
        bound_width = self.size().width()
        bound_height = self.size().height()

        scale_factor = (
            min(bound_height / page_height, bound_width / page_width)
            if bound_height > 0 and bound_width > 0
            else 1.0
        )
        self.set_zoom_level(scale_factor)

    def resizeEvent(self, event: QtGui.QResizeEvent):  # Override
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent):  # Override
        if event.rect().width() < 1 or event.rect().height() < 1:
            return
        with util.q_painter(self) as p:
            if self.page is EMPTY_PAGE:
                p.fillRect(event.rect(), Qt.darkGray)
                return

            p.fillRect(event.rect(), Qt.black)
            img = render_fitz_page(self.page, self.zoom_level, self.devicePixelRatio())
            layout_size: QtCore.QSize = img.size() / img.devicePixelRatio()
            coordinate = centered_coord(event.rect().size(), layout_size)
            p.drawImage(coordinate, img)

            if self.preview_page is EMPTY_PAGE:
                return

            img = render_fitz_page(
                self.preview_page,
                self.zoom_level,
                self.devicePixelRatio(),
                clip=fitz.Rect(0, 0, self.page.bound().width, self.page.bound().height // 3),
            )
            p.drawImage(coordinate, img)

            # Draw Shadow under preview
            preview_layout_height: QtCore.QSize = img.size().height() / img.devicePixelRatio()
            grad = QtGui.QLinearGradient(
                coordinate.x(),
                preview_layout_height,
                coordinate.x(),
                preview_layout_height + 30,
            )
            grad.setColorAt(0.0, QtGui.QColor(0, 0, 0, 155))
            grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
            p.fillRect(
                coordinate.x(),
                preview_layout_height,
                layout_size.width(),
                30,
                grad
            )



class PDFView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(paren=)