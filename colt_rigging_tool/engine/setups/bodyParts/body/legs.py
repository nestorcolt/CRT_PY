import collections
import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel
from colt_rigging_tool.engine.utils import tools
from colt_rigging_tool.engine.setups.controls import control
from colt_rigging_tool.engine.setups.bodyParts.body import limb

reload(control)
reload(tools)
reload(limb)

###################################################################################################
# GLOBALS:
UPPERLEG_JOINT = 'L_upperLeg_JNT'

###################################################################################################
"""

    Description: I've tried to keep each method independent from the other,
    that means that each system "IK-FK" can be constructed separately and will work as an only system

"""

###################################################################################################


class Leg(limb.Limb):

    def __init__(self,
                 legJoint='',
                 name='legClass',
                 prefix='leg',
                 scale=1.0,
                 scaleIK=1.0,
                 scaleFK=1.0,
                 controlAngle=30,
                 pole_vector_distance=40,
                 ik_hook = None,
                 fk_hook=None,
                 pv_hook=None):

        print(
            """
                Description: leg class to build complex stretch ik fk leg system on humanoid character
                LEG must have 3 joints: "UPPERLEG to END".
            """
        )

        super(Leg, self).__init__(
            firstJoint=legJoint,
            name=name,
            prefix=prefix,
            scale=scale,
            scaleIK=scaleIK,
            scaleFK=scaleFK,
            controlAngle=controlAngle,
            pole_vector_distance=pole_vector_distance,
            positive_ik=False,
            fk_hook=fk_hook,
            ik_hook=ik_hook,
            pv_hook=pv_hook)

    ######################################################################################################

    @tools.undo_cmds
    def build(self, twist_chain_len=5):

        self.makeFK(simple_fk=True, world_orient=True)
        self.makeIK(world_orient=True)
        # #
        self.groupSystem()
        self.makeBlending()
        #
        self.makeFkStretchSystem()
        self.makeIkStretchSystem()

        self.connectStretchSystem()
        # #
        self.collectTwistJoints(limbJoints=self.inputChain[:-1], index=twist_chain_len)
        self.makeTwistSystem()
        # #
        self.hideShapesCB()
        self.controlsVisibilitySetup()
        self.skell_group = self.create_deformation_chain()
        self.hook()
        self.clean()

        ######################################################################################################


    ###################################################################################################
    # creates the system for controls visibility IK FK or both
    #
    def controlsVisibilitySetup(self):
        # note: the attribute holder is a pm.core node type
        attrHolder = self.attributeHolder
        fkControls = [ctrl.control for ctrl in self.fk_controls]
        ikControls = [ctrl.control for ctrl in [self.ik_control, self.poleVector]]
        ikControls.append(self.poleVectorAttachLine)

        # call generic function from tools module
        tools.makeControlsVisSetup(attrHolder=attrHolder, prefix=self.letter + '_' + self.prefix,
                                   controlsIK=ikControls, controlsFK=fkControls)

    ######################################################################################################
    # Hide shapes from channel box in for each control in leg system

    @tools.undo_cmds
    def hideShapesCB(self):

        if self.checkFK:
            # hide shapes of controls from channelbox
            controls = self.fk_controls[:]
            rawControls = [itm.control for itm in controls]
            tools.hideShapesChannelBox(rawControls, exception=[self.attributeHolder])

        if self.checkIK:
            tools.hideShapesChannelBox([self.poleVector.control, self.ik_control.control,
                                        self.attributeHolder])

        else:
            cmds.warning('FK and IK system must be both created to hide shapes from controls in channelbox')


###################################################################################################
# builder function to keep class instances inside of a function and not in global


###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    tools.re_open_current_file()
    # instance:
    leg = Leg(legJoint=UPPERLEG_JOINT, scaleFK=8)
    leg.build()
    cmds.select(clear=True)
    del leg
    pass
