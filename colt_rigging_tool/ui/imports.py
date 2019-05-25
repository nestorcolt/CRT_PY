# -*- coding: utf-8 -*-
from Qt import __binding__
from Qt import QtWidgets as qw
from Qt import QtCore as qc
from Qt import QtGui as qg

#
if __binding__ in ('PySide2', 'PyQt5'):
    print('Qt5 binding available')
    import shiboken2 as shi
    from PySide2.QtWidgets import QPen, QColor, QBrush, QLinearGradient, QFont, QRadialGradient

elif __binding__ in ('PySide', 'PyQt4'):
    print('Qt4 binding available.')
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
import os
import sys

###############################################################
