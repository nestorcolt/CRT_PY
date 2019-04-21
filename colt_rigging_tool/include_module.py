import os
import sys
###################################################################################################
# includes the module in maya sys path to make relative imports
def loadModule():
    DIRS = [os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.path.dirname(os.path.abspath(__file__))]
    for DIR in DIRS:
        if not DIR in sys.path:
            sys.path.append(DIR)
            print('\nCURRENT DIR: %s' % DIR)

###################################################################################################
loadModule()

