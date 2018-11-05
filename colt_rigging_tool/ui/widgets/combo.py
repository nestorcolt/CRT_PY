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
#------------------------------------------------------------------------------------------------------------#

CCSCombo = """#QComboColt,
            QComboBox {
            border-radius: 4px;
            padding: 1px 10px 1px 10px;
            color: rgba(200,200,200,200);
            font-family: Calibri;
            font: bold 12px;
            padding-left: 10px;

        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;

            border-left-width: 1px;
            border-left-color: darkgray;
            border-left-style: solid; /* just a single line */
            border-top-right-radius: 4px; /* same radius as the QComboBox */
            border-bottom-right-radius: 4px
        }


        /* shift the arrow when popup is open */
        QComboBox::down-arrow:on {
            top: 1px;
            left: 1px
        }

        QComboBox QAbstractItemView {
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(53, 57, 60), stop:1 rgba(50, 50, 50,200));
            color : rgba(255,255,255,200);
            selection-background-color: rgba(255,255,255,40);
            selection-color: white;
            padding: 2px 2px 2px 10px;


        }

        QComboBox:!editable, QComboBox::drop-down:editable {
            background-color: rgba(34,34,34,100);
        }

        /* QComboBox gets the "on" state when the popup is open */
        QComboBox:!editable:on, QComboBox::drop-down:editable:on {
            background : qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(34, 34, 34,100), stop:1 rgba(34, 34, 34,5))
        }

        QComboBox:on { /* shift the text when the popup opens */
            padding-top: 2px;
            padding-left: 10px

        }"""

####################################################################################################################


class ComboColt(qw.QComboBox):
    def __init__(self):
        super(ComboColt, self).__init__()
        self.setObjectName('QComboColt')
        self.setStyleSheet(CCSCombo)

        self.addItem('bla')
        self.addItem('bla')
        self.addItem('bla')
        self.addItem('bla')
        self.addItem('bla')

        self.setEnabled(True)

    def showPopup(self):
        super(ComboColt, self).showPopup()
        popup = self.findChild(qw.QFrame)
        popup.setFixedWidth(182)
        popup.setStyleSheet('background:rgba(34,34,34);border-radius:0px;')
        popup.move(popup.x(), popup.y() + 1)
