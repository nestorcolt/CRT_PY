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

from colt_rigging_tool.ui.widgets import buttons
from colt_rigging_tool.ui import css
#
import os
import sys


reload(buttons)
reload(css)

###############################################################
# GLOBALS:

###################################################################################################


class FaceTab(qw.QFrame):

    def __init__(self):
        super(FaceTab, self).__init__()
        self.setStyleSheet(css.cssTabsBackground)

###################################################################################################
