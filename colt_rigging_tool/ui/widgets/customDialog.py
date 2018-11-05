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

class MainDialog(qw.QDialog):
    background = QBrush(QColor(16, 160, 207, 150))
    stripe = QBrush(QColor(34, 34, 34, 250))
    penTick = QPen(QColor(200, 200, 200), 12, qc.Qt.SolidLine)

    multy = 220
    col1 = QColor(1 * multy, 1 * multy, 1 * multy, 100)
    multy = 200
    col2 = QColor(1 * multy, 1 * multy, 1 * multy, 50)
    multy = 100
    col3 = QColor(1 * multy, 1 * multy, 1 * multy, 100)

    def __init__(self, *args, **kwargs):
        qw.QDialog.__init__(self, *args, **kwargs)

        label = qw.QLabel('Colt Rigging Tool', parent=self)

        label.setFixedWidth(500)
        label.setFixedHeight(40)

        label.setStyleSheet("""background: transparent;
                               font-family: calibri;
                               font-size: 40px;
                               font-weight: 600;
                               width: 500px;
                               padding-top:0px;
                               letter-spacing: 10px;
                               word-spacing: 300px;
                               """)

        label.move(35, 62)
        # label.setIndent(50)

    def paintEvent(self, event):

        painter = qg.QPainter(self)
        option = qw.QStyleOption()
        option.initFrom(self)

        painter.setRenderHint(qg.QPainter.Antialiasing)

        x = option.rect.x()
        y = option.rect.y()

        height = option.rect.height()
        width = option.rect.width()

        # fill background
        painter.fillRect(x, y, width, height, self.background)

        gradient = QRadialGradient(float(width / 2), float(height / 2), float(height))

        gradient.setColorAt(0.0, self.col1)
        gradient.setColorAt(0.5, self.col2)
        gradient.setColorAt(1.0, self.col3)

        painter.fillRect(x, y, width, height, gradient)

        # path line
        line_path = qg.QPainterPath()

        line_path.moveTo(0, 176)
        line_path.lineTo(width, 128)

        self.penTick.setCapStyle(qc.Qt.RoundCap)
        painter.setPen(self.penTick)
        painter.drawPath(line_path)

        # fill stripe
        painter.rotate(-5)
        painter.translate(float(50) * -1, float(-200))
        painter.fillRect(x, y / 2, width * 2, (height - height / 2), self.stripe)
