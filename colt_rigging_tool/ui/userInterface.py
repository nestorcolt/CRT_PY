# -*- coding: utf-8 -*-
from colt_rigging_tool import include_module
include_module.loadModule()


#
from colt_rigging_tool.Qt import __binding__
from colt_rigging_tool.Qt import QtWidgets as qw
from colt_rigging_tool.Qt import QtCore as qc
from colt_rigging_tool.Qt import QtGui as qg

#
if __binding__ in ('PySide2', 'PyQt5'):
    # print('Qt5 binding available')
    import shiboken2 as shi
    from PySide2.QtGui import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient

elif __binding__ in ('PySide', 'PyQt4'):
    # print('Qt4 binding available.')
    import shiboken as shi
    from PySide.QtGui import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient

else:
    print('No Qt binding available.')

#
import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMaya as om
import maya.OpenMayaUI as mui
#
from colt_rigging_tool.ui.widgets import customDialog
from colt_rigging_tool.ui.widgets import buttons
from colt_rigging_tool.ui.tabs import bodyTab
from colt_rigging_tool.ui.tabs import faceTab
from colt_rigging_tool.ui.tabs import meshTab
from colt_rigging_tool.ui import css
#
import os
import sys

reload(customDialog)
reload(buttons)
reload(bodyTab)
reload(faceTab)
reload(meshTab)
reload(css)

###############################################################
# GLOBALS:
TOOL_GLOBAL = None
UI_OBJECT = 'Colt_rigging_tool'

# this is for the borderless dialog
X = 0
X2 = 8  # !!!!
Y = 0
Y2 = 30  # !!!!

###################################################################################################


def getMayaWindow():
    mainWinPtr = mui.MQtUtil.mainWindow()
    return shi.wrapInstance(long(mainWinPtr), qw.QWidget)

#---------------------------------------------------------------------------------#
# delete ANY maya child with given object name to mantain clean the memory


def deleteFromGlobal(windowObject):

    mayaMainWindowPtr = mui.MQtUtil.mainWindow()
    mayaMainWindow = shi.wrapInstance(long(mayaMainWindowPtr), qw.QMainWindow)  # Important that it's QMainWindow, and not QWidget
    # Go through main window's children to find any previous instances
    for obj in mayaMainWindow.children():
        if isinstance(obj, qw.QDialog):
            if obj.objectName() == windowObject:
                print(obj.objectName())
                obj.setParent(None)
                obj.deleteLater()

                print('Object Deleted...', obj.objectName())

                del(obj)
                global TOOL_GLOBAL
                TOOL_GLOBAL = None

#---------------------------------------------------------------------------------#


class Colt_rigging_tool(customDialog.MainDialog):
    leftClick = False

    def __init__(self, parent=getMayaWindow()):
        super(Colt_rigging_tool, self).__init__(parent)

        # moves the dialog to the desired location on screen to testing purposes(must delete at the end or center to screen)
        self.move(1080, 140)
        self.setObjectName(UI_OBJECT)
        self.setMinimumSize(550, 750)
        self.setWindowTitle('Colt Character Rigging Tool')

        self.setLayout(qw.QVBoxLayout())

        closeButton = buttons.CloseButton()

        topLayout = qw.QHBoxLayout()

        topLayout.setAlignment(qc.Qt.AlignTop | qc.Qt.AlignRight)
        topLayout.addWidget(closeButton)

        self.layout().addLayout(topLayout)

        mainWidget = qw.QFrame()
        mainWidget.setFixedHeight(550)
        mainWidget.setSizePolicy(qw.QSizePolicy.Minimum, qw.QSizePolicy.Expanding)
        self.layout().addWidget(mainWidget)

        #####################
        # tab container
        #
        self.tabWidget = qw.QTabWidget()
        self.tabWidget.setContentsMargins(0, 0, 0, 0)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setStyleSheet(css.TABSCSS)
        self.tabWidget.setObjectName('tabWidget_riggingTool')

        tabs_layout = qw.QVBoxLayout(mainWidget)
        tabs_layout.addWidget(self.tabWidget)

        ##############################################################
        # Exporter tabs
        #

        self.body_tab = bodyTab.BodyTab()
        self.tabWidget.addTab(self.body_tab, '- Body ')

        self.face_tab = faceTab.FaceTab()
        self.tabWidget.addTab(self.face_tab, '- Facial ')

        self.mesh_tab = meshTab.MeshTab()
        self.tabWidget.addTab(self.mesh_tab, '- Mesh ')

        # connct some signals
        #
        closeButton.clicked.connect(lambda: self.close())

    #####################################################################################

    def resizeEvent(self, event):

        pixmap = qg.QPixmap(self.size())
        pixmap.fill(qc.Qt.transparent)
        painter = qg.QPainter(pixmap)
        painter.setBrush(qc.Qt.black)
        painter.drawRoundedRect(pixmap.rect(), 20, 20)
        painter.end()

        self.setMask(pixmap.mask())

    def mouseMoveEvent(self, event):
        super(Colt_rigging_tool, self).mouseMoveEvent(event)
        if self.leftClick == True:
            self.move(event.globalPos().x() - X - X2, event.globalPos().y() - Y - Y2)
            event.accept()

    def mousePressEvent(self, event):
        super(Colt_rigging_tool, self).mousePressEvent(event)
        if event.button() == qc.Qt.LeftButton:
            self.leftClick = True
            global X, Y
            X = event.pos().x()
            Y = event.pos().y()
            event.accept()

    def mouseReleaseEvent(self, event):
        super(Colt_rigging_tool, self).mouseReleaseEvent(event)
        self.leftClick = False

    def showEvent(self, event):

        event.accept()
        return True

    def closeEvent(self, event):
        deleteFromGlobal(self.objectName())
        global TOOL_GLOBAL
        TOOL_GLOBAL = None

#################################################################################################################


def load_riggingTool():
    # clean the memory and erase any instance of UI
    deleteFromGlobal(UI_OBJECT)

    global TOOL_GLOBAL
    if TOOL_GLOBAL is None:

        TOOL_GLOBAL = Colt_rigging_tool()
        TOOL_GLOBAL.setAttribute(qc.Qt.WA_DeleteOnClose)
        TOOL_GLOBAL.show()


#################################################################################################################
#
if __name__ == '__main__':
    load_riggingTool()
