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
UPPERARM_JOINT = 'L_clavicle_JNT'
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
                 name='armClass',
                 prefix='arm',
                 scale=1.0,
                 scaleIK=1.0,
                 scaleFK=1.0,
                 controlAngle=30,
                 pole_vector_distance = 60):

        print(
            """
                Description: arm class to build complex stretch ik fk arms system on humanoid character
                ARM must have 3 joints: "upperARM to end".
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
                 pole_vector_distance = pole_vector_distance)

        # PROPERTIES

        self.ik_clavicle_control = None

        # hand controls
        self.handTopCtrl = None
        self.fingers = None
        self.fingers_auto_dic = None

        # unparentHandFromSystem
        self.hand = {}
        self.hand_module_grp = None

    ######################################################################################################

    @tools.undo_cmds
    def build(self, hand_join="", twist_chain_len=5):

        self.makeFK()
        self.makeIK()
        #
        if hand_join:
            self.makeHand(hand_joint=hand_join)
            self.make_auto_fist(force=True)

        self.groupSystem()
        self.makeBlending()

        self.makeIkClavicle(chain=self.ik_hier, rigGroup=self.ik_group)
        self.create_deformation_chain()

        self.makeFkStretchSystem()
        self.makeIkStretchSystem()

        self.connectStretchSystem()
        #
        self.collectTwistJoints(limbJoints=self.inputChain[1:-1], index=twist_chain_len)
        self.makeTwistSystem()
        #
        self.hideShapesCB()
        self.controlsVisibilitySetup()
        self.clean()

        ######################################################################################################

    def makeIkClavicle(self, chain=[], rigGroup=""):
        # IK clavicle control
        clavNameCtrl = tools.remove_suffix(chain[0])
        ik_clavicleControl = control.Control(prefix=clavNameCtrl + '_IK', shape=4, translateTo=chain[0],
                                             rotateTo=chain[0], scale=self.scale)

        if cmds.getAttr(chain[0] + '.tx') >= 0:
            cmds.move(10, ik_clavicleControl.control + "*Shape" + ".cv[*]", moveZ=True, absolute=True)
        elif cmds.getAttr(chain[0] + '.tx') < 0:
            cmds.move(10, ik_clavicleControl.control + "*Shape" + ".cv[*]", moveZ=True, absolute=True)

        cmds.parent(chain[0], ik_clavicleControl.control)
        cmds.parent(ik_clavicleControl.root, rigGroup)

        self.ik_clavicle_control = ik_clavicleControl


    ###################################################################################################
    # creates the system for controls visibility IK FK or both
    #
    def controlsVisibilitySetup(self):
        # note: the attribute holder is a pm.core node type
        attrHolder = self.attributeHolder
        fkControls = [ctrl.control for ctrl in self.fk_controls]
        ikControls = [ctrl.control for ctrl in [self.ik_control, self.ik_clavicle_control, self.poleVector]]
        ikControls.append(self.poleVectorAttachLine)

        # call generic function from tools module
        tools.makeControlsVisSetup(attrHolder=attrHolder, prefix=self.letter + '_' + self.prefix,
                                   controlsIK=ikControls, controlsFK=fkControls)

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

        cmds.parentConstraint(hand_joint, topControl.root, mo=True)

        tools.hideShapesChannelBox([topControl.control])

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
        cmds.parentConstraint(hand_control_grp, hand_joint, mo=True)
        cmds.parentConstraint(self.inputChain[-1], hand_control_grp, mo=True)
        #
        cmds.parent(hand_joint, handGrp)

        self.handTopCtrl = topControl
        self.fingers = controlsArray
        self.hand_module_grp = handGrp

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
        self.limb_modules_groups.append(self.hand_module_grp)

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
                                        self.ik_clavicle_control.control, self.attributeHolder])

        else:
            cmds.warning('FK and IK system must be both created to hide shapes from controls in channelbox')

###################################################################################################
# builder function to keep class instances inside of a function and not in global




###################################################################################################


# IN MODULE TEST:
# if __name__ == '__main__':
    tools.re_open_current_file()
    # instance:
arm = Arm(armJoint=UPPERARM_JOINT, scaleFK=8)
arm.build(hand_join=HAND_JOINT)
# arm.make_auto_fist(value=-20, force=True)
cmds.select(clear=True)
# del arm
pass
