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
        attrHolder = self.attributeHolder.name()
        fkControls = [ctrl.control for ctrl in self.fk_controls]
        ikControls = [ctrl.control for ctrl in [self.ik_control, self.ik_clavicle_control, self.poleVector]]
        ikControls.append(self.poleVectorAttachLine)

        # call generic function from tools module
        tools.makeControlsVisSetup(attrHolder=attrHolder, prefix=self.letter + '_' + self.prefix, controlsIK=ikControls, controlsFK=fkControls)

    ######################################################################################################

    def makeHand(self):

        hand = self.hand.values()[0]
        handName = tools.remove_suffix(hand)
        handGrp = cmds.group(n=handName + '_GRP', em=True)
        cmds.delete(cmds.parentConstraint(hand, handGrp))

        topControl = control.Control(prefix=handName + '_auto', translateTo=hand, rotateTo=hand,
                                     shape=4, scale=self.scale * 2, lockChannels=['t', 'r', 's', 'v'])
        tools.hideShapesChannelBox([topControl.control])

        # check X value
        child = cmds.listRelatives(hand)[0]
        value = cmds.getAttr(child + '.tx')
        if value >= 0:
            cmds.move(8, 2, 0, topControl.root, relative=True, objectSpace=True)
        else:
            cmds.move(-8, -2, 0, topControl.root, relative=True, objectSpace=True)

        # flatten shape
        shapes = cmds.listRelatives(topControl.control, shapes=True)

        for itm in shapes:
            cvs = cmds.getAttr(itm + '.spans') + 1
            for vt in range(cvs):
                cmds.setAttr(itm + '.controlPoints[%d].yValue' % vt, 0)

        #
        handJoints = [itm for itm in cmds.listRelatives(hand, ad=True)
                      if cmds.listRelatives(itm) is not None and cmds.listRelatives(itm, p=True)[0] != hand]

        controlsArray = []

        for jnt in handJoints:
            name = tools.remove_suffix(jnt)
            ctrl = control.Control(prefix=name, translateTo=jnt, rotateTo=jnt, scale=self.scale * 1.5, angle='x')
            cmds.orientConstraint(ctrl.control, jnt)
            controlsArray.append(ctrl)

        for idx, (ctrl, jnt) in enumerate(zip(controlsArray, handJoints)):

            parent = cmds.listRelatives(cmds.listRelatives(jnt, p=True)[0], p=True)[0]
            if parent != hand:
                try:
                    cmds.parent(ctrl.root, controlsArray[idx + 1].control)
                except:
                    pass
            else:
                cmds.parent(ctrl.root, handGrp)

        # parenting hand controls group to general limb group
        cmds.parentConstraint(hand, handGrp)
        cmds.parent(handGrp, self.limb_main_grp)
        # parent top ctrl to hand joint
        cmds.parent(topControl.root, hand)

        self.handTopCtrl = topControl
        self.fingers = controlsArray

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
# builder function to keep class instances inside of a function and not in global


@tools.undo_cmds
def loader():
    if cmds.objExists('l_leg_sys_GRP'):
        # cmds.delete('l_leg_sys_GRP')
        pass

    # delete unused nodes
    mel.eval('MLdeleteUnused;')

    # instance:
    arm = Arm(armJoint=UPPERARM_JOINT, scaleFK=8)

    arm.makeFK()
    arm.makeIK()

    # arm.makeHand()
    # arm.make_auto_fist(force=True)

    arm.groupSystem()
    arm.makeBlending()

    arm.makeIkClavicle(chain=arm.ik_hier, rigGroup=arm.ik_group)
    arm.create_deformation_chain()

    arm.makeFkStretchSystem()
    arm.makeIkStretchSystem()

    arm.connectStretchSystem()
    #
    arm.collectTwistJoints(limbJoints=arm.inputChain[1:-1], index=5)
    arm.makeTwistSystem()
    #
    # arm.hideShapesCB()
    # arm.controlsVisibilitySetup()
    # arm.clean()

    return arm

###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    arm = loader()
    # arm.make_auto_fist(value=-20, force=True)
    cmds.select(clear=True)
    pass
