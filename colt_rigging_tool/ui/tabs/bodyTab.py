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
from colt_rigging_tool.ui.widgets import combo
from colt_rigging_tool.ui.widgets import checkBox
from colt_rigging_tool.ui.widgets import spinBox
from colt_rigging_tool.ui import css
#
import os
import sys


reload(buttons)
reload(checkBox)
reload(combo)
reload(spinBox)
reload(css)

###############################################################
# GLOBALS:
DEFAULT_STYLE = """
QProgressBar{
    border: 0px;
    border-radius: 10px;
    text-align: center;
    font-size: 14px;
    font-weight: 400;
    color: rgba(34,34,34,200)
}

QProgressBar::chunk {
    background-color: rgba(240,240,240,125);
    width: 10px;
    margin: 1px;
    border: 0px;
    border-radius: 2px;
}
"""
###################################################################################################


class BodyTab(qw.QFrame):

    def __init__(self):
        super(BodyTab, self).__init__()

        self.setObjectName('bodyTab')
        self.setStyleSheet(css.cssTabsBackground)
        self.setContentsMargins(0, 0, 0, 0)

        layout = qw.QVBoxLayout()
        self.setLayout(layout)
        layout.setObjectName('bodyTab_layout')

        divArray = ['Structure', 'Spine', 'Arms', 'Legs', 'Autos']
        areasDic = {}

        for i in range(5):
            area = CustomFrameHolder()
            area.setObjectName(divArray[i])
            layout.addWidget(area)

            areasDic[area.objectName()] = area
            label = qw.QLabel(divArray[i] + '  ~')
            label.setStyleSheet('color:rgba(34, 34, 34, 250);')
            label.setParent(area)

        # Structure Area
        #
        StructureWidget = areasDic['Structure']
        StructureWidget.setContentsMargins(0, 0, 0, 0)
        StructureWidget.setMaximumHeight(75)

        StructureStack_lyt = qw.QStackedLayout()
        StructureStack_lyt.setStackingMode(qw.QStackedLayout.StackAll)

        StructureWidget.setLayout(StructureStack_lyt)

        StructureLabel = StructureWidget.findChildren(qw.QLabel)[0]
        StructureStack_lyt.insertWidget(0, StructureLabel)
        StructureLabel.setAlignment(qc.Qt.AlignLeft)

        StructureInnerWidget = qw.QWidget()
        StructureInnerWidget.setContentsMargins(10, 5, 10, 2)

        StructureStack_lyt.insertWidget(1, StructureInnerWidget)

        StructureLayout = qw.QHBoxLayout(StructureInnerWidget)
        StructureLayout.setObjectName('StructureLayout')

        verticalStructure_lyt = qw.QVBoxLayout()
        StructureLayout.addLayout(verticalStructure_lyt)

        # vertical layout structure
        grid_one = qw.QFormLayout()
        verticalStructure_lyt.addLayout(grid_one)

        char_name_lbl = qw.QLabel('Character Name:')
        main_geo = qw.QLineEdit()
        main_geo.setStyleSheet('background:rgba(34,34,34,80); font-family:calibri;border-radius: 4px;')
        main_geo.setSizePolicy(qw.QSizePolicy.Expanding, qw.QSizePolicy.Maximum)

        geo_name_lbl = qw.QLabel('Character Geo:')
        comboBoxGeo = combo.ComboColt()
        comboBoxGeo.setSizePolicy(qw.QSizePolicy.Expanding, qw.QSizePolicy.Maximum)

        grid_one.addRow(char_name_lbl, main_geo)
        grid_one.addRow(geo_name_lbl, comboBoxGeo)

        createSkel_btn = buttons.Custom_button(text='Init Rig Skeleton')
        createSkel_btn.setSizePolicy(qw.QSizePolicy.Maximum, qw.QSizePolicy.Maximum)

        createSkel_btn.setMinimumHeight(45)
        createSkel_btn.setMinimumWidth(150)

        StructureLayout.addWidget(createSkel_btn)
        StructureStack_lyt.setCurrentIndex(1)

        # Spine Area
        #
        spineWidget = areasDic['Spine']
        spineWidget.setMaximumHeight(75)
        spineWidget.setContentsMargins(0, 0, 0, 0)

        spineStack_lyt = qw.QStackedLayout()
        spineStack_lyt.setStackingMode(qw.QStackedLayout.StackAll)

        spineWidget.setLayout(spineStack_lyt)

        spineLabel = spineWidget.findChildren(qw.QLabel)[0]
        spineStack_lyt.insertWidget(0, spineLabel)
        spineLabel.setAlignment(qc.Qt.AlignLeft)

        spineInnerWidget = qw.QWidget()
        spineInnerWidget.setContentsMargins(0, 0, 0, 0)

        spineStack_lyt.insertWidget(1, spineInnerWidget)

        spineLayout = qw.QHBoxLayout(spineInnerWidget)
        spineLayout.setObjectName('spineLayout')
        spineStack_lyt.setCurrentIndex(1)
        spineLayout.setContentsMargins(80, 2, 40, 4)

        vert_1_lyt = qw.QVBoxLayout()
        vert_2_lyt = qw.QVBoxLayout()

        spine_std_chbox = checkBox.CustomCheck('STANDAR')
        spine_prm_chbox = checkBox.CustomCheck('PREMIUN')

        spine_calibrate_btn = buttons.Custom_button(text='Calibrate')
        spine_calibrate_btn.setMinimumWidth(150)
        spine_calibrate_btn.setMinimumHeight(40)

        # set calibrate to disable
        spine_calibrate_btn.setEnabled(False)

        spineLayout.addLayout(vert_1_lyt)
        spineLayout.addLayout(vert_2_lyt)

        cal_btn_lyt = qw.QHBoxLayout()
        cal_btn_lyt.setAlignment(qc.Qt.AlignHCenter)

        vert_1_lyt.addWidget(spine_std_chbox)
        vert_1_lyt.addWidget(spine_prm_chbox)
        vert_2_lyt.addWidget(qw.QLabel('* only available with Premiun setup'))
        vert_2_lyt.addLayout(cal_btn_lyt)
        cal_btn_lyt.addWidget(spine_calibrate_btn)

        # Arms Area
        #
        armsWidget = areasDic['Arms']
        armsWidget.setFixedHeight(100)
        armsWidget.setContentsMargins(0, 0, 0, 0)

        armsStack_lyt = qw.QStackedLayout()
        armsStack_lyt.setStackingMode(qw.QStackedLayout.StackAll)

        armsWidget.setLayout(armsStack_lyt)

        armsLabel = armsWidget.findChildren(qw.QLabel)[0]
        armsStack_lyt.insertWidget(0, armsLabel)
        armsLabel.setAlignment(qc.Qt.AlignLeft)

        armsInnerWidget = qw.QWidget()
        armsInnerWidget.setContentsMargins(0, 0, 0, 0)

        armsStack_lyt.insertWidget(1, armsInnerWidget)

        armsLayout = qw.QHBoxLayout(armsInnerWidget)
        armsLayout.setObjectName('armsLayout')
        armsStack_lyt.setCurrentIndex(1)

        # develop structure layout
        armsLayout.setContentsMargins(80, 0, 80, 0)
        arms_widgets_Array = ['IK System', 'FK System', 'Twist System', 'Twist Joints']
        arms_widgets_dict = {}
        iterador = 0

        for idx in range(2):
            row_lyt = qw.QVBoxLayout()
            armsLayout.addLayout(row_lyt)

            for index in range(2):
                widgte = None

                if iterador == len(arms_widgets_Array) - 1:
                    label = qw.QLabel(arms_widgets_Array[iterador])
                    widget = spinBox.CustomSpinBox()
                    widget.setRange(0, 20)

                    hoz_lyt = qw.QHBoxLayout()
                    row_lyt.addLayout(hoz_lyt)
                    hoz_lyt.addWidget(label)
                    hoz_lyt.addWidget(widget)
                    hoz_lyt.setContentsMargins(20, 0, 20, 0)

                else:
                    widget = checkBox.CustomCheck(arms_widgets_Array[iterador])
                    widget.setObjectName(arms_widgets_Array[iterador])
                    row_lyt.addWidget(widget)

                widget.setObjectName(arms_widgets_Array[iterador])
                arms_widgets_dict[arms_widgets_Array[iterador]] = widget
                iterador += 1

        #

        # Legs Area
        #
        legsWidget = areasDic['Legs']
        legsWidget.setFixedHeight(100)
        legsWidget.setContentsMargins(0, 0, 0, 0)

        legsStack_lyt = qw.QStackedLayout()
        legsStack_lyt.setStackingMode(qw.QStackedLayout.StackAll)

        legsWidget.setLayout(legsStack_lyt)

        legsLabel = legsWidget.findChildren(qw.QLabel)[0]
        legsStack_lyt.insertWidget(0, legsLabel)
        legsLabel.setAlignment(qc.Qt.AlignLeft)

        legsInnerWidget = qw.QWidget()
        legsInnerWidget.setContentsMargins(0, 0, 0, 0)

        legsStack_lyt.insertWidget(1, legsInnerWidget)

        legsLayout = qw.QHBoxLayout(legsInnerWidget)
        legsLayout.setObjectName('legsLayout')
        legsStack_lyt.setCurrentIndex(1)

        # develop structure layout
        legsLayout.setContentsMargins(80, 0, 80, 0)
        legs_widgets_Array = ['IK System', 'FK System', 'Twist System', 'Twist Joints']
        legs_widgets_dict = {}
        iterador = 0

        for idx in range(2):
            row_lyt = qw.QVBoxLayout()
            legsLayout.addLayout(row_lyt)

            for index in range(2):
                widgte = None

                if iterador == len(legs_widgets_Array) - 1:
                    label = qw.QLabel(legs_widgets_Array[iterador])
                    widget = spinBox.CustomSpinBox()
                    widget.setRange(0, 20)

                    hoz_lyt = qw.QHBoxLayout()
                    row_lyt.addLayout(hoz_lyt)
                    hoz_lyt.addWidget(label)
                    hoz_lyt.addWidget(widget)
                    hoz_lyt.setContentsMargins(20, 0, 20, 0)

                else:
                    widget = checkBox.CustomCheck(legs_widgets_Array[iterador])
                    widget.setObjectName(legs_widgets_Array[iterador])
                    row_lyt.addWidget(widget)

                widget.setObjectName(legs_widgets_Array[iterador])
                legs_widgets_dict[legs_widgets_Array[iterador]] = widget
                iterador += 1

        #

        # Auto Area
        #
        autoWidget = areasDic['Autos']

        autoWidget.setMaximumHeight(100)
        autoWidget.setContentsMargins(0, 0, 0, 0)

        autoStack_lyt = qw.QStackedLayout()
        autoStack_lyt.setStackingMode(qw.QStackedLayout.StackAll)

        autoWidget.setLayout(autoStack_lyt)

        autoLabel = autoWidget.findChildren(qw.QLabel)[0]
        autoStack_lyt.insertWidget(0, autoLabel)
        autoLabel.setAlignment(qc.Qt.AlignLeft)

        autoInnerWidget = qw.QWidget()
        autoInnerWidget.setContentsMargins(0, 0, 0, 0)

        autoStack_lyt.insertWidget(1, autoInnerWidget)

        autoLayout = qw.QHBoxLayout(autoInnerWidget)
        autoLayout.setObjectName('autoLayout')
        autoStack_lyt.setCurrentIndex(1)
        autoLayout.setContentsMargins(50, 5, 50, 10)

        # layout structure
        auto_ver_lyt_1 = qw.QVBoxLayout()
        auto_ver_lyt_2 = qw.QVBoxLayout()

        autoLayout.addLayout(auto_ver_lyt_1)
        autoLayout.addLayout(auto_ver_lyt_2)

        auto_ver_lyt_1.addWidget(qw.QLabel('* Select area to setup automation'))
        auto_combo = combo.ComboColt()
        auto_ver_lyt_1.addWidget(auto_combo)

        auto_ver_2_wdt_holder_lyt = qw.QHBoxLayout()
        auto_ver_lyt_2.addLayout(auto_ver_2_wdt_holder_lyt)

        driven_wdg_lbl = qw.QLabel('Driven Value')
        self.driven_value_spin = spinBox.CustomSpinBox()

        auto_ver_2_wdt_holder_lyt.addWidget(driven_wdg_lbl)
        auto_ver_2_wdt_holder_lyt.addWidget(self.driven_value_spin)

        auto_ver_2_wdt_holder_lyt.setAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignVCenter)

        driven_value_btn = buttons.Custom_button(text='Key', borderRad=10)
        driven_btn_lyt = qw.QHBoxLayout()

        driven_value_btn.setFixedSize(100, 25)

        auto_ver_lyt_2.addLayout(driven_btn_lyt)
        driven_btn_lyt.addWidget(driven_value_btn)

        driven_btn_lyt.setAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignVCenter)

        # size vertical 2
        auto_combo.setFixedWidth(200)

        #
        # Create Run Button
        #
        runLayout = qw.QHBoxLayout()
        runLayout.setContentsMargins(20, 5, 20, 5)
        # runLayout.setAlignment(qc.Qt.AlignRight)
        layout.addLayout(runLayout)

        runBtn = buttons.Custom_button(text='RUN', borderRad=5)

        progress_bar_run = qw.QProgressBar()
        progress_bar_run.setStyleSheet(DEFAULT_STYLE)
        progress_bar_run.setRange(0, 99)

        # progress description reader
        lcd_run = qw.QLabel('Ready!')
        lcd_run.setAlignment(qc.Qt.AlignCenter)
        lcd_run.setContentsMargins(5, 0, 5, 0)
        lcd_run.setFixedWidth(60)
        lcd_run.setStyleSheet("background-color: rgba(34,34,34,50); font-family:calibri; font-size:12px; border-radius: 5px; align:center; font-weight:600;"
                              )

        runBtn.setFixedSize(50, 40)
        # runLayout.addSpacerItem(horizontalSpacer)

        runLayout.addWidget(progress_bar_run)
        runLayout.addWidget(lcd_run)
        runLayout.addWidget(runBtn)

        # connects progress bar to testing purposes
        self.driven_value_spin.valueChanged.connect(lambda value: progress_bar_run.setValue(value))

###################################################################################################


class CustomFrameHolder(qw.QFrame):
    penTick = qg.QPen(qg.QColor(200, 200, 200, 200), 2, qc.Qt.SolidLine)

    def __init__(self):
        super(CustomFrameHolder, self).__init__()
        self.setFrameStyle(qw.QFrame.Raised)
        self.setStyleSheet("background: transparent; font-family:calibri; font-weight:600; font-size:12px;")

    def paintEvent(self, event):
        painter = qg.QPainter(self)
        option = qw.QStyleOption()
        option.initFrom(self)

        x = option.rect.x()
        y = option.rect.y()
        height = option.rect.height()
        width = option.rect.width()

        painter.setRenderHint(qg.QPainter.Antialiasing)
        line_path = qg.QPainterPath()
        #------------------- ----------#
        offset_y = 10
        offset_x = 25

        line_path.moveTo(x + offset_x, (height - 2))
        line_path.lineTo(width - offset_x, (height - 2))

        self.penTick.setCapStyle(qc.Qt.RoundCap)
        painter.setPen(self.penTick)
        painter.drawPath(line_path)
