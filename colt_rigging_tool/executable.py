from runpy import run_path
######################################################################################################
run_path(r"C:\Users\colt-desk\Documents\Development\python\ColtRiggingTool\colt_rigging_tool\include_module.py")
######################################################################################################
from colt_rigging_tool.ui import userInterface
reload(userInterface)
userInterface.load_riggingTool()
######################################################################################################
