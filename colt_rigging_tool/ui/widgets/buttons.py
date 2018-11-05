from Qt import __binding__
from Qt import QtWidgets as qw
from Qt import QtCore as qc
from Qt import QtGui as qg

#
if __binding__ in ('PySide2', 'PyQt5'):
    # print('Qt5 binding available')
    from PySide2.QtGui import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient

elif __binding__ in ('PySide', 'PyQt4'):
    # print('Qt4 binding available.')
    from PySide.QtGui import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient

else:
    print('No Qt binding available.')


###############################################################

class CloseButton(qw.QPushButton):

    _pen_point = QPen(QColor(34, 34, 34, 250), 8, qc.Qt.SolidLine)
    _pen_hover = QPen(QColor(225, 0, 0, 100), 9, qc.Qt.SolidLine)
    _pen_TickPressed = QPen(QColor(10, 10, 10), 3, qc.Qt.SolidLine)

    MAINBRUSH = QPen(QColor(200, 200, 200, 25), 16, qc.Qt.SolidLine)
    BRUSHHOVER = QPen(QColor(200, 200, 200, 40), 17, qc.Qt.SolidLine)

    def __init__(self, *args, **kwargs):
        super(CloseButton, self).__init__(*args, **kwargs)

        self.setStyleSheet("background: transparent;")
        self.setFixedSize(30, 30)

    def paintEvent(self, event):
        painter = qg.QPainter(self)
        option = qw.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()

        height = option.rect.height()
        width = option.rect.width()

        radius = 50

        painter.setRenderHint(qg.QPainter.Antialiasing)

        # outter
        self.MAINBRUSH.setCapStyle(qc.Qt.RoundCap)
        painter.setPen(self.MAINBRUSH)
        painter.drawPoint((x + width / 2), (y + height / 2))

        # red dot
        self._pen_point.setCapStyle(qc.Qt.RoundCap)
        painter.setPen(self._pen_point)
        painter.drawPoint((x + width / 2), (y + height / 2))

        # painter.setBrush(self._brushClear)

        if self.isDown():
            pass

        elif self.underMouse():
            # outter
            self.BRUSHHOVER.setCapStyle(qc.Qt.RoundCap)
            painter.setPen(self.BRUSHHOVER)
            painter.drawPoint((x + width / 2), (y + height / 2))

            # red dot hover
            self._pen_hover.setCapStyle(qc.Qt.RoundCap)
            painter.setPen(self._pen_hover)
            painter.drawPoint((x + width / 2), (y + height / 2))

###################################################################################################


class Custom_button(qw.QPushButton):
    _pen_text = QPen(QColor(200, 200, 200, 250), 5, qc.Qt.SolidLine)
    _pen_textHover = QPen(QColor(34, 34, 34, 250), 5, qc.Qt.SolidLine)
    _pen_pressed = QPen(QColor(100, 0, 0, 200), 5, qc.Qt.SolidLine)

    _penBorder = QPen(QColor(200, 200, 200, 180), 2, qc.Qt.SolidLine)
    _penDisabled = QPen(QColor(200, 200, 200, 10), 2, qc.Qt.SolidLine)
    _brushClear = QBrush(QColor(0, 0, 0, 0))

    BRUSHHOVER = QBrush(QColor(250, 250, 250, 15))
    BRUSHPRESS = QBrush(QColor(45, 45, 45, 10))
    BRUSHDISABLED = QBrush(QColor(34, 34, 34, 100))

    _fontSize = 12
    _spacing = 2

    def __init__(self, borderRad=20, *args, **kwargs):
        super(Custom_button, self).__init__(*args, **kwargs)
        self.setStyleSheet("background: transparent;")

        self.radius = borderRad
        font = qg.QFont()
        font.setPointSize(self._fontSize)
        font.setFamily('Calibri')
        font.setLetterSpacing(QFont.AbsoluteSpacing, float(self._spacing))
        font.setBold(True)
        self.setFont(font)
        self.fontMetrics = qg.QFontMetrics(font)

    def paintEvent(self, event):
        painter = qg.QPainter(self)
        option = qw.QStyleOption()
        option.initFrom(self)

        x = option.rect.x() + 1
        y = option.rect.y() + 2
        height = option.rect.height() - 5
        width = option.rect.width() - 2

        painter.setRenderHint(qg.QPainter.Antialiasing)

        #################################
        # draw TEXT
        #
        alignment = (qc.Qt.AlignHCenter | qc.Qt.AlignVCenter)
        text = self.text()
        font = self.font()

        text_width = self.fontMetrics.width(text)
        text_height = font.pointSize()

        textPath = qg.QPainterPath()
        textPath.addText(x, y, font, text)

        penHover = self._pen_textHover
        penText = self._pen_text
        penpress = self._pen_pressed

        path = qg.QPainterPath()
        path.addRoundedRect(qc.QRectF(x, y, width, height), self.radius, self.radius)

        painter.fillPath(path, self.BRUSHPRESS)
        painter.setPen(self._penBorder)
        painter.drawPath(path)

        painter.fillRect(x, y, width, height, self._brushClear)

        penText.setCapStyle(qc.Qt.RoundCap)
        penText.setStyle(qc.Qt.SolidLine)
        painter.setPen(penText)
        painter.drawText(x + 1, y, width + 2, height, alignment, text)

        if self.isDown():
            painter.fillPath(path, self.BRUSHPRESS)
            painter.setPen(penpress)
            penpress.setCapStyle(qc.Qt.RoundCap)
            penpress.setStyle(qc.Qt.SolidLine)
            painter.drawText(x + 1, y, width + 2, height, alignment, text)

        elif self.underMouse():
            painter.setPen(penHover)
            penHover.setCapStyle(qc.Qt.RoundCap)
            penHover.setStyle(qc.Qt.SolidLine)
            painter.fillPath(path, self.BRUSHHOVER)
            painter.drawText(x + 1, y, width + 2, height, alignment, text)

        if not self.isEnabled():
            painter.setPen(self._penDisabled)
            self._penDisabled.setCapStyle(qc.Qt.RoundCap)
            self._penDisabled.setStyle(qc.Qt.SolidLine)
            painter.drawRoundedRect(qc.QRectF(x, y, width, height), self.radius, self.radius)
            painter.setPen(self._penDisabled)

            painter.fillPath(path, self.BRUSHDISABLED)
            painter.drawText(x + 1, y, width + 2, height, alignment, text)

        painter.end()

###################################################################################################
