import sys
######################################################################################################
print("yas!! your script it's running")
path_to_delete = [r"C:\Users\colt-desk\Documents\Development\python\ColtRiggingTool",
                  r"C:\Users\colt-desk\Documents\Development\python\ColtRiggingTool\colt_rigging_tool"]

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
            if path in itm:
                try:
                    sys.path.remove(path)
                    print("{} Removed from path".format(path))
                except:
                    print("Path not removed from system")

dropCachedImports("colt_rigging_tool")

######################################################################################################
