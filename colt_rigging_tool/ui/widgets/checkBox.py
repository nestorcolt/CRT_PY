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
class CustomCheck(qw.QCheckBox):

    _pen_text = QPen(QColor(200, 200, 200, 225), 1, qc.Qt.SolidLine)
    _pen_Shadow = QPen(QColor(9, 10, 12), 1, qc.Qt.SolidLine)
    _pen_border = QPen(QColor(9, 10, 12, 100), 2, qc.Qt.SolidLine)
    _pen_clear = QPen(QColor(0, 0, 0, 0), 1, qc.Qt.SolidLine)

    _penText_disable = QPen(QColor(102, 107, 110), 1, qc.Qt.SolidLine)
    _penShadow_disable = QPen(QColor(0, 0, 0), 1, qc.Qt.SolidLine)

    _brushClear = QBrush(QColor(0, 0, 0, 0))
    _brushBorder = QBrush(QColor(34, 34, 34, 250))
    _brushActive = QBrush(QColor(250, 250, 250, 200))
    _brushUnderMouse = QBrush(QColor(250, 250, 250, 50))

    # extras
    _spacing = 5

    def __init__(self, *args, **kwargs):
        super(CustomCheck, self).__init__(*args, **kwargs)

        font = qg.QFont()
        font.setPointSize(12)
        font.setFamily('Calibri')
        self.setFont(font)
        self.setFixedHeight(27)
        font.setLetterSpacing(QFont.AbsoluteSpacing, float(self._spacing))

        self.fontMetrics = qg.QFontMetrics(font)
        self.radius = 5

    ###################################################################################################

    def paintEvent(self, event):

        painter = qg.QPainter(self)
        option = qw.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height() - 1
        width = option.rect.width() - 1

        painter.setRenderHint(qg.QPainter.Antialiasing)
        painter.setRenderHint(qg.QPainter.TextAntialiasing)

        alignment = (qc.Qt.AlignVCenter)

        text = self.text()

        painter.setPen(self._pen_border)
        painter.setBrush(self._brushBorder)
        rounded = painter.drawRoundedRect(qc.QRect(x + 5, y + 8, 12, 12), 2, 2)

        # text values
        x_text = x + 25

        if self.isEnabled():
            painter.setPen(self._pen_text)
            painter.drawText(x_text, y, width, height, alignment, text)

        else:
            painter.setPen(self._penText_disable)
            painter.drawText(x, y, width, height, alignment, text)

        painter.setPen(self._pen_clear)

        if self.checkState():
            painter.setBrush(self._brushActive)
            rounded = painter.drawRoundedRect(qc.QRect(x + 6, y + 9, 10, 10), 2, 2)

        if self.underMouse():
            painter.setBrush(self._brushUnderMouse)
            rounded = painter.drawRoundedRect(qc.QRect(x + 6, y + 9, 10, 10), 2, 2)

#-----------------------------------------------------------------------------------------------------#
