from Qt import __binding__
from Qt import QtWidgets as qw
from Qt import QtCore as qc
from Qt import QtGui as qg
#
QTSIGNAL = None

#
if __binding__ in ('PySide2', 'PyQt5'):
    # print('Qt5 binding available')
    from PySide2.QtGui import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient


elif __binding__ in ('PySide', 'PyQt4'):
    # print('Qt4 binding available.')
    from PySide.QtGui import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient
    from PySide.QtCore import QObject, SIGNAL

    QTSIGNAL = SIGNAL

else:
    print('No Qt binding available.')

from colt_rigging_tool.ui import css
reload(css)

###############################################################


class CustomSpinBox(qw.QSpinBox):

    # Added a signal
    # changedValue = QTSIGNAL('int')

    def __init__(self, *args, **kwargs):
        super(CustomSpinBox, self).__init__(*args, **kwargs)
        self.setStyleSheet(css.QSpinCSS)
        font = qg.QFont('Calibri', 8)
        self.setFont(font)
        self.lineEditChild = self.findChild(qw.QLineEdit)

        # self.connect(self, pyqtSignal('valueChanged(int)'), qc.SLOT('onSpinBoxValueChanged(int)'), qc.Qt.QueuedConnection)
        # self.valueChanged.connect(self.printStatus)

        self.lineEditChild.installEventFilter(self)
        self.setAccelerated(True)
        self.drag_origin = None

        self.timerShot = qc.QTimer()
        self.timerShot.timeout.connect(self.deselectWidget)

    def printStatus(self):
        print(self.value())

    def deselectWidget(self):
        self.lineEditChild.deselect()
        self.lineEditChild.clearFocus()

    def get_is_dragging(self):
        # are we the widget that is also the active mouseGrabber?
        return self.mouseGrabber() == self

    ### Dragging Handling Methods ################################################
    def do_drag_start(self):
        # Record position
        # Grab mouse
        self.drag_origin = qg.QCursor().pos()
        self.grabMouse()

    def do_drag_update(self):
        # Transpose the motion into values as a delta off of the recorded click position
        curPos = qg.QCursor().pos()
        offsetVal = self.drag_origin.y() - curPos.y()
        self.setValue(offsetVal)

    def do_drag_end(self):
        self.releaseMouse()
        # Restore position
        # Reset drag origin value
        self.drag_origin = None

    def eventFilter(self, obj, event):
        if obj == self.lineEditChild:
            if event.type() == qc.QEvent.Leave:
                self.timerShot.start(3500)
                event.accept()
                return True

        return False

    ### Mouse Override Methods ################################################
    def mousePressEvent(self, event):

        if qc.Qt.LeftButton:
            self.do_drag_start()
            self.timerShot.start(3500)
        elif self.get_is_dragging() and qc.Qt.RightButton:
            # Cancel the drag
            self.do_drag_end()
            self.timerShot.start(3500)
        else:
            super(CustomSpinBox, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.get_is_dragging():
            self.do_drag_update()
        else:
            super(CustomSpinBox, self).mouseReleaseEvent(event)

    def mouseReleaseEvent(self, event):
        if self.get_is_dragging() and qc.Qt.LeftButton:
            self.do_drag_end()
        else:
            super(CustomSpinBox, self).mouseReleaseEvent(event)

########################################################


class CustomDoubleSpinBox(qw.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super(CustomDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setStyleSheet(css.QSpinCSS_2)
        font = qw.QFont('Calibri', 8)
        self.setFont(font)
        self.setSingleStep(0.10)

        self.lineEditChild = self.findChild(qw.QLineEdit)
        self.connect(self, qc.SIGNAL('valueChanged(int)'), qc.SLOT('onSpinBoxValueChanged(int)'), qc.Qt.QueuedConnection)

        self.lineEditChild.installEventFilter(self)
        self.setAccelerated(True)
        self.drag_origin = None

        self.timerShot = qc.QTimer()
        self.timerShot.setInterval(3000)
        self.timerShot.timeout.connect(self.deselectWidget)

    def deselectWidget(self):
        self.lineEditChild.deselect()
        self.lineEditChild.clearFocus()

    def get_is_dragging(self):
        # are we the widget that is also the active mouseGrabber?
        return self.mouseGrabber() == self

    ### Dragging Handling Methods ################################################
    def do_drag_start(self):
        # Record position
        # Grab mouse
        self.drag_origin = qw.QCursor().pos()
        self.grabMouse()

    def do_drag_update(self):
        # Transpose the motion into values as a delta off of the recorded click position
        curPos = qw.QCursor().pos()
        offsetVal = self.drag_origin.y() - curPos.y()
        self.setValue(offsetVal)

    def do_drag_end(self):
        self.releaseMouse()
        # Restore position
        # Reset drag origin value
        self.drag_origin = None

    def eventFilter(self, obj, event):
        if obj == self.lineEditChild:
            if event.type() == qc.QEvent.Leave:
                self.timerShot.start()
                event.accept()
                return True

        return False

    ### Mouse Override Methods ################################################
    def mousePressEvent(self, event):
        if qc.Qt.LeftButton:
            self.do_drag_start()
        elif self.get_is_dragging() and qc.Qt.RightButton:
            # Cancel the drag
            self.do_drag_end()
        else:
            super(CustomDoubleSpinBox, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.get_is_dragging():
            self.do_drag_update()
        else:
            super(CustomDoubleSpinBox, self).mouseReleaseEvent(event)

    def mouseReleaseEvent(self, event):
        if self.get_is_dragging() and qc.Qt.LeftButton:
            self.do_drag_end()
        else:
            super(CustomDoubleSpinBox, self).mouseReleaseEvent(event)

#################################################################################################
#
#


class CustomSpinBox_02(CustomSpinBox):
    def __init__(self):
        super(CustomSpinBox_02, self).__init__()
        self.setStyleSheet(css.QSpinCSS_03)
