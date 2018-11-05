#---------------------------------------------------------------------------------#
# CSS

TABSCSS = """

            /* Style the tab using the tab sub-control. Note that it reads QTabBar _not_ QTabWidget */
            QTabBar::tab {
            font-family: calibri;
            font-size: 12px;
            background: rgba(34, 34, 34, 250);
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            min-width: 10ex;
            padding: 4px;
            padding-bottom:2px;
            margin-bottom: 1px;
            margin-left: +0.5px;
            width: 70px;
            border-bottom: 0.5px solid rgba(24, 24, 24, 250);
            }

            QTabBar::tab:selected, QTabBar::tab:hover {
            background: rgba(44, 44, 44, 250);

            }

            QTabBar::tab:selected {
            border-bottom-color: white; /* same as pane color */
            }

            QTabBar::tab:!selected {
            margin-top: 1px; /* make non-selected tabs look smaller */
            }

            QTabBar::tab:selected {
            margin-left: +0.5px;
            margin-right: +0.5px; }

            QTabBar::tab:first:selected {
            margin-left: 0;}

            QTabBar::tab:last:selected {
            margin-right: 0; }

            QTabBar::tab:only-one {
            margin: 0;

            }

            QTabBar::tab:selected { font-size : 13px; color: rgba(255,255,255,225);}

            """

#
cssTabsBackground = """background-color: rgba(35, 36, 38,25);
                   border-bottom-left-radius: 20px;
                   border-bottom-right-radius: 20px;
                   """

###################################################################################################


QSpinCSS_03 = """
            QSpinBox {
            background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(53, 57, 60,255), stop: 0.5 rgba(25,15,05,50), stop: 1.1 rgba(33, 34, 36, 255));
            border: 1px solid black;
            border-radius: 4px;
            font: bold 12px;
            font-family: Calibri;
            nohighlights;
            }

            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right; /* position at the top right corner */

                width: 27px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
                border-width: 1px;
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(150, 150, 150,85), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(125, 10, 1, 200));
                border-left-width: 0.5px;
                border-left-color: black;
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 4px; /* same radius as the QComboBox */
                border-bottom-width: 0.5px;
                border-bottom-color: black;
                border-bottom-style: solid; /* just a single line */

            }

            QSpinBox::up-button:hover {
                background-color: rgba(255,255,255,20)
            }

            QSpinBox::down-button:hover {
                background-color: rgba(255,255,255,20)
            }

            QSpinBox::up-button:pressed {
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(80, 10, 1, 100), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(200, 200, 200,125));
            }

            QSpinBox::down-button:pressed {
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(80, 10, 1, 100), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(200, 200, 200,125));
            }

            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right; /* position at the top right corner */

                width: 27px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
                border-width: 1px;
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(150, 150, 150,85), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(125, 10, 1, 200));
                border-left-width: 0.5px;
                border-left-color: black;
                border-left-style: solid; /* just a single line */
                border-bottom-right-radius: 4px; /* same radius as the QComboBox */
                border-top-width: 0.5px;
                border-top-color: black;
                border-top-style: solid; /* just a single line */
            }"""

###################################################################################################
QSpinCSS_2 = """
            QDoubleSpinBox {
            background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(53, 57, 60,255), stop: 0.5 rgba(25,15,05,50), stop: 1.1 rgba(33, 34, 36, 255));
            border: 1px solid black;
            border-radius: 4px;
            font: bold 12px;
            font-family: Calibri;
            nohighlights;
            }

            QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right; /* position at the top right corner */

                width: 27px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
                border-width: 1px;
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(150, 150, 150,85), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(125, 10, 1, 200));
                border-left-width: 0.5px;
                border-left-color: black;
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 4px; /* same radius as the QComboBox */
                border-bottom-width: 0.5px;
                border-bottom-color: black;
                border-bottom-style: solid; /* just a single line */

            }

            QDoubleSpinBox::up-button:hover {
                background-color: rgba(255,255,255,20)
            }

            QDoubleSpinBox::down-button:hover {
                background-color: rgba(255,255,255,20)
            }

            QDoubleSpinBox::up-button:pressed {
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(80, 10, 1, 100), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(200, 200, 200,125));
            }

            QDoubleSpinBox::down-button:pressed {
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(80, 10, 1, 100), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(200, 200, 200,125));
            }

            QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right; /* position at the top right corner */

                width: 27px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
                border-width: 1px;
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(150, 150, 150,85), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(125, 10, 1, 200));
                border-left-width: 0.5px;
                border-left-color: black;
                border-left-style: solid; /* just a single line */
                border-bottom-right-radius: 4px; /* same radius as the QComboBox */
                border-top-width: 0.5px;
                border-top-color: black;
                border-top-style: solid; /* just a single line */
            }
          """

########################################################

QSpinCSS = """
            QSpinBox {
            background-color: rgba(34,34,34,100);
            border-radius: 4px;
            font: bold 12px;
            font-family: Calibri;
            nohighlights;
            }

            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right; /* position at the top right corner */

                width: 27px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
                border-width: 1px;
                background-color: rgba(34,34,34,200);
                border-left-width: 0.5px;
                border-left-color: rgba(1,1,1,200);
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 4px; /* same radius as the QComboBox */
                border-bottom-width: 0.5px;
                border-bottom-color: rgba(34,34,34,250);
                border-bottom-style: solid; /* just a single line */

            }

            QSpinBox::up-button:hover {
                background-color: rgba(255,255,255,20)
            }

            QSpinBox::down-button:hover {
                background-color: rgba(255,255,255,20)
            }

            QSpinBox::up-button:pressed {
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(80, 10, 1, 100), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(200, 200, 200,125));
            }

            QSpinBox::down-button:pressed {
                background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1.0 ,
                                 fx: 0.5 , fy: 0.5, stop: 0 rgba(80, 10, 1, 100), stop: 0.3 rgba(1,1,1,50), stop: 1.0 rgba(200, 200, 200,125));
            }

            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right; /* position at the top right corner */

                width: 27px; /* 16 + 2*1px border-width = 15px padding + 3px parent border */
                border-width: 1px;
                background-color: rgba(34,34,34,200);
                border-left-width: 0.5px;
                border-left-color: rgba(1,1,1,200);
                border-left-style: solid; /* just a single line */
                border-bottom-right-radius: 4px; /* same radius as the QComboBox */
                border-top-width: 0.5px;
                border-bottom-color: rgba(34,34,34,250);
                border-top-style: solid; /* just a single line */
            }
          """
########################################################
