import os
import sys
import inspect
###################################################################################################
# includes the module in maya sys path to make relative imports
current_frame = inspect.getfile(inspect.currentframe())
module_name = os.path.dirname(current_frame)
root_name = os.path.dirname(module_name)
#
def loadModule():
    DIRS = [module_name, root_name]
    for DIR in DIRS:
        if not DIR in sys.path:
            sys.path.append(DIR)
            print('CURRENT DIR: %s' % DIR)

###################################################################################################
loadModule()

