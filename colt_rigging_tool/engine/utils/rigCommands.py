from colt_rigging_tool.engine.setups.controls import control
from colt_rigging_tool.engine.utils import tools
import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMaya as om
import os


reload(tools)
######################################################################################################

class Simple_fk_command(object):

    def __init__(self,
                 joint_root = "",
                 hook = "",
                 parent = "",
                 side = "C",
                 module_name = "simple_fk",
                 shape=0,
                 color = 13,
                 size = 5
                 ):
        #
        self.root_joint = joint_root
        self.hook = hook
        self.parent = parent
        self.side = side
        self.module_name = module_name
        self.shape = shape
        self.color = color
        self.size = size
        #
        self.hierarchy = []
        self._controls = []
        #

    ######################################################################################################

    def create_chain(self):
        hierarchy = tools.list_joint_hier(top_joint=self.root_joint, with_end_joints=False)

        for idx, jnt in enumerate(hierarchy):
            ctrl = control.Control(prefix=jnt[:-3], translateTo=jnt, angle='x',
                                   rotateTo=jnt, scale=self.size, lockChannels=['t', 's', 'v'])
            #
            self._controls.append(ctrl)
            cmds.parentConstraint(ctrl.control, jnt)

            if idx > 0:
                cmds.parent(ctrl.root, self._controls[idx - 1].control)

        if self.parent:
            cmds.parent(self._controls[0].root, self.parent)

        if self.hook:
            cmds.parentConstraint(self.hook, self._controls[0].root)

        return self._controls


######################################################################################################

######################################################################################################
if __name__ == '__main__':
    instance = Simple_fk_command(joint_root="L_foot_01_JNT", side="L")
    instance.create_chain()
