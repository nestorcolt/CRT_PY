import inspect
import sys
import os
######################################################################################################
print("yas!! your cleaner script it's running")
tool_module_name = "colt_rigging_tool"
current_file = inspect.getfile(inspect.currentframe())
module_path = os.path.dirname(inspect.getfile(colt_rigging_tool))
path_to_delete = [module_path, os.path.dirname(module_path)]
######################################################################################################

def dropCachedImports(*packagesToUnload):
    '''
    prepares maya to re-import
    '''
    def shouldUnload(module):
        for packageToUnload in packagesToUnload:
            if module.startswith(packageToUnload):
                return True
        return False

    for i in sys.modules.keys()[:]:
        if shouldUnload(i):
            print ("unloading module ", i)
            del sys.modules[i]


    for path in path_to_delete:
        for itm in sys.path:
            if "ColtRiggingTool" in itm:
                try:
                    sys.path.remove(itm)
                    print("ColtRiggingTool Removed from path")
                except:
                    "Path not removed from system"

######################################################################################################
dropCachedImports(tool_module_name)
######################################################################################################

