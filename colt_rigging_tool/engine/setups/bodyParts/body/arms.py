import collections
import inspect

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
CLAVICLE_JOINT = 'L_upperArm_JNT'
HAND_JOINT = "L_hand_JNT"

###################################################################################################
"""

    Description: I've tried to keep each method independent from the other,
    that means that each system "IK-FK" can be constructed separately and will work as an only system

"""
###################################################################################################


class Arm(limb.Limb):

    def __init__(self,
                 armJoint='',
                 clavicle_joint="",
                 name='armClass',
                 prefix='arm',
                 scale=1.0,
                 scaleIK=1.0,
                 scaleFK=1.0,
                 controlAngle=30,
                 pole_vector_distance = 40,
                 fk_hook=None,
                 ik_hook=None,
                 pv_hook=None):

        print(
            """
                Description: arm class to build complex stretch ik fk arms system on humanoid character
                ARM must have 3 joints: "UPPERARM to END".
            """
        )

        super(Arm, self).__init__(
                 firstJoint=armJoint,
                 name=name,
                 prefix= prefix,
                 scale=scale,
                 scaleIK=scaleIK,
                 scaleFK=scaleFK,
                 controlAngle=controlAngle,
                 pole_vector_distance = pole_vector_distance,
                 positive_ik=True,
                 fk_hook=fk_hook,
                 ik_hook=ik_hook,
                 pv_hook=pv_hook)


        # PROPERTIES
        self.fk_clavicle_control = None
        self.clavicle_joint = clavicle_joint

        # hand controls
        self.handTopCtrl = None
        self.fingers = None
        self.fingers_auto_dic = None

        # unparentHandFromSystem
        self.hand = {}
        self.hand_rig_group = None
        self.hand_controls_group = None
        self.hand_skell_group = None

    ######################################################################################################

    @tools.undo_cmds
    def build(self, hand_join="", twist_chain_len=5):

        self.makeFK(simple_fk=True)
        self.makeIK()

        self.groupSystem()
        self.makeBlending()

        self.make_clavicle()

        self.makeFkStretchSystem()
        self.makeIkStretchSystem()

        self.connectStretchSystem()
        #
        self.collectTwistJoints(limbJoints=self.inputChain[0:-1], index=twist_chain_len)
        self.makeTwistSystem()
        #
        if hand_join:
            self.makeHand(hand_joint=hand_join)
            self.make_auto_fist(force=True)
            self.create_hand_skell_group()
        #
        self.hideShapesCB()
        self.controlsVisibilitySetup()
        self.skell_group = self.create_deformation_chain()
        self.hook()
        self.clean()

        ######################################################################################################

    def make_clavicle(self,):
        # IK clavicle control
        clavNameCtrl = tools.remove_suffix(self.clavicle_joint)
        clavicleControl = control.Control(prefix=clavNameCtrl, shape=4, translateTo=self.clavicle_joint,
                                          rotateTo=self.clavicle_joint, scale=self.scale)

        if cmds.getAttr(self.clavicle_joint + '.tx') >= 0:
            cmds.move(10, clavicleControl.control + "*Shape" + ".cv[*]", moveZ=True, absolute=True)
        elif cmds.getAttr(self.clavicle_joint + '.tx') < 0:
            cmds.move(10, clavicleControl.control + "*Shape" + ".cv[*]", moveZ=True, absolute=True)

        cmds.parentConstraint(clavicleControl.control, self.clavicle_joint)
        cmds.parent(clavicleControl.root, self.controls_group)
        #
        cmds.parentConstraint(clavicleControl.control, self.fk_controls[0].root, mo=True)
        cmds.parentConstraint(clavicleControl.control, self.ik_group, mo=True)
        cmds.parent(self.clavicle_joint, self.rig_group)
        self.fk_clavicle_control = clavicleControl

    ######################################################################################################

    def hook(self):
        cmds.parentConstraint(self.fk_hook, self.fk_clavicle_control.root, mo=True)

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

    def create_hand_skell_group(self):
        self.hand_skell_group = tools.create_deformation_joints_for_module(module=self.hand_rig_group)

    ######################################################################################################

    def makeHand(self, hand_joint = ""):

        if not hand_joint:
            return

        self.hand[self.inputChain[-1]] = cmds.listRelatives(hand_joint, ad=True)
        #
        hand = hand_joint
        handName = tools.remove_suffix(hand)
        handGrp = cmds.group(n=handName + '_rig_GRP', em=True)
        hand_control_grp = cmds.group(n=handName + '_controls_GRP', em=True)
        #
        cmds.delete(cmds.parentConstraint(hand, handGrp))
        cmds.delete(cmds.parentConstraint(hand, hand_control_grp))

        topControl = control.Control(prefix=handName + '_UI', translateTo=hand, rotateTo=hand,
                                     shape=4, scale=self.scale * 2, lockChannels=['t', 'r', 's', 'v'])
        cmds.parent(topControl.root, hand_control_grp)

        # check X value
        child = cmds.listRelatives(hand)[0]
        value = cmds.getAttr(child + '.tx')
        #
        if value >= 0:
            cmds.move(4, 3, 0, topControl.root, relative=True, objectSpace=True)
        else:
            cmds.move(-4, -3, 0, topControl.root, relative=True, objectSpace=True)

        # flatten shape
        shapes = cmds.listRelatives(topControl.control, shapes=True)
        cmds.parentConstraint(hand_joint, topControl.root, mo=True)
        tools.hideShapesChannelBox([topControl.control])

        for itm in shapes:
            cvs = cmds.getAttr(itm + '.spans') + 1
            for vt in range(cvs):
                cmds.setAttr(itm + '.controlPoints[%d].yValue' % vt, 0)

        #
        handJoints = tools.list_joint_hier(hand_joint, with_end_joints=False)[1:]
        controlsArray = []

        for jnt in handJoints:
            name = tools.remove_suffix(jnt)
            ctrl = control.Control(prefix=name, translateTo=jnt, rotateTo=jnt, scale=self.scale * 1.5, angle='x')
            cmds.orientConstraint(ctrl.control, jnt)
            controlsArray.append(ctrl)


        for idx, (ctrl, jnt) in enumerate(zip(controlsArray, handJoints)):
            #
            parent = cmds.listRelatives(jnt, p=True)[0]
            if parent != hand_joint:
                try:
                    cmds.parent(ctrl.root, controlsArray[idx - 1].control)
                except:
                    pass
            else:
                cmds.parent(ctrl.root, hand_control_grp)

        # parenting hand controls group to general limb group
        cmds.parent(hand_joint, handGrp)
        cmds.parentConstraint(hand_control_grp, hand_joint, mo=True)
        cmds.parentConstraint(self.inputChain[-1], hand_control_grp, mo=True)
        #
        self.handTopCtrl = topControl
        self.fingers = controlsArray
        self.hand_rig_group = handGrp

        # make hand float attributes for channel box setting
        attributes = ['thumb', 'index', 'middle', 'ring', 'pinky']

        for att in attributes:
            cmds.addAttr(topControl.control, k=True, longName=att, shortName=att[1] + att[-1], minValue=-20,
                         maxValue=50, defaultValue=0)

        auto_fist = collections.defaultdict(list)

        for att, itm in [(att, itm) for att in attributes for itm in controlsArray]:
            if att in itm.auto[:]:
                auto_fist[att].append(itm.auto)

        # add show finger controls attr
        cmds.addAttr(topControl.control, k=True, longName='showControls', shortName='SWC', at='bool', defaultValue=1)

        for ctrl in controlsArray:
            shape = cmds.listRelatives(ctrl.control, s=True)[0]
            cmds.connectAttr(topControl.control + '.showControls', shape + '.visibility', f=True)

        self.fingers_auto_dic = auto_fist
        self.hand_controls_group = hand_control_grp
        self.limb_modules_groups.append(self.hand_rig_group)

    ###################################################################################################
    # create the slider float controls over the hand top control
    #

    def make_auto_fist(self, value=0, force=False):
        control = self.handTopCtrl

        for key, val in self.fingers_auto_dic.items():
            driver = '{}.{}'.format(control.control, key)
            cmds.setAttr(driver, value)

            for itm in val:
                driven = '{}.{}'.format(itm, 'rz')

                # collect values of driver global control and driven rool group to make operation
                globalCtrlValue = cmds.getAttr(cmds.listRelatives(itm)[0] + '.rz')
                drivenValue = cmds.getAttr(driven)
                setAttributeValue = globalCtrlValue + drivenValue

                # check if global control has no value then skip the driven key
                if globalCtrlValue != 0 or force is True:
                    cmds.setAttr(driven, setAttributeValue)
                    cmds.setAttr(cmds.listRelatives(itm)[0] + '.rz', 0)
                    cmds.setDrivenKeyframe(driven, currentDriver=driver, outTangentType='linear',
                                           inTangentType='linear', driverValue=value)

                try:
                    # set post and pre infinity for animCurve in driven
                    animCurve = cmds.listConnections(driven, t='animCurve')[0]
                    cmds.setAttr(animCurve + '.preInfinity', 1)
                    cmds.setAttr(animCurve + '.postInfinity', 1)

                except:
                    pass

    ###################################################################################################
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
                                        self.fk_clavicle_control.control, self.attributeHolder])

        else:
            cmds.warning('FK and IK system must be both created to hide shapes from controls in channelbox')


###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    tools.re_open_current_file()
    arm = Arm(armJoint=CLAVICLE_JOINT, scaleFK=8, clavicle_joint="L_clavicle_JNT")
    arm.build(hand_join=HAND_JOINT)
    arm.make_auto_fist(value=-20, force=True)
    cmds.select(clear=True)
    del arm
