import os
import sys
###################################################################################################
# includes the module in maya sys path to make relative imports


def loadModule():
    DIR = os.path.dirname(os.path.abspath(__file__))
    if not DIR in sys.path:
        sys.path.append(DIR)
        print('\nCURRENT DIR: %s' % DIR)


###################################################################################################

if __name__ == '__main__':
    loadModule()
    pass
