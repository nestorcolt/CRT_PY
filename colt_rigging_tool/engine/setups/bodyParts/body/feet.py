import collections
import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel
from colt_rigging_tool.engine.utils import tools
from colt_rigging_tool.engine.utils import rigCommands
from colt_rigging_tool.engine.setups.controls import control


reload(control)
reload(tools)
reload(rigCommands)

###################################################################################################
# GLOBALS:
LEG_END_JOINT = 'l_leg_end_rig'

###################################################################################################
"""

    Description: feet class for building foot system on humanoid character
    - Need to have previusly created the leg system for setting the correct orientation of IK controls

    Usage:
    - call the createLocators Method first
    - with the locs created locate them in the desired position and correct orientation
    matching the Fk foot controls orientation from the leg system
    - call the createFootStructure method and populate the function with the right arguments

"""
###################################################################################################


class Feet(object):

    def __init__(self,
                 foot_joint='',
                 hook = "",
                 name='feetClass',
                 prefix='foot',
                 scale=1.0,
                 scaleIK=1.0,
                 scaleFK=1.0,
                 hook_ik="",
                 hook_fk="",
                 attribute_holder = ""):

        # public member
        self.letter = tools.getSideLetter(foot_joint)

        self.prefix = prefix
        self.scale = scale

        self.scaleIK = scaleIK
        # general limb parent
        self.parent = hook
        self.ik_hook = hook_ik
        self.fk_hook = hook_fk
        self.input_attribute_holder = attribute_holder

        self.foot_joint = foot_joint
        # locators for positioning
        self.dummyNames = ['ankle', 'ball', 'toes', 'toes_tip', 'tillIn', 'tillOut', 'heel']
        self.dummyLocs = []

        self.dummyPos = []
        # feet dictionaries
        self.leftFoot = None

        self.rightFoot = None
        #
        # current foot
        self.currentFoot = None

        self.currentControls = None
        # current attribute holder
        self.currentHolder = None

        self.mainFootControl = None
        self.chains = {}
        #
        self._ik_control = cmds.createNode("transform", n="{}_footInner_IK_NCTL".format(self.letter))
        #
        self.ik_group =  cmds.createNode("transform", n="{}_foot_IK_GRP".format(self.letter))
        self.fk_group = cmds.createNode("transform", n="{}_foot_FK_GRP".format(self.letter))
        self.main_group = cmds.createNode("transform", n="{}_foot_MAIN_GRP".format(self.letter))
        #
        self.foot_group = cmds.createNode("transform", n="{}_foot_rig_GRP".format(self.letter))
        self.controls_group = cmds.createNode("transform", n="{}_foot_controls_GRP".format(self.letter))
        self._fk_controls = []

        cmds.parent(self.ik_group, self.foot_group)
        cmds.parent(self.fk_group, self.foot_group)
        cmds.parent(self.main_group, self.foot_group)
        cmds.parent(self._ik_control, self.controls_group)

    ######################################################################################################
    def hook_to_leg(self):

        if not self.input_attribute_holder or not cmds.objExists(self.input_attribute_holder):
            return

        if self.ik_hook and self.fk_hook:
            if cmds.objExists(self.ik_hook) or cmds.objExists(self.fk_hook):
                cmds.parentConstraint(self.ik_hook, self._ik_control, mo=True)
                cmds.parentConstraint(self.fk_hook, self._fk_controls[0].root, mo=True)

                # rename index 0 fx control
                ctrl = self._fk_controls[0].control
                cmds.setAttr("{}.lodVisibility".format(pm.PyNode(ctrl).getShape().name()), 0)
                ctrl_name = ctrl.replace("_CTL", "_NCTRL")
                cmds.rename(ctrl, ctrl_name)

            # connect Attributes holder
            cmds.connectAttr("{}.IK_0_FK_1".format(self.input_attribute_holder),
                             "{}.IK_0_FK_1".format(self.currentHolder), f=True)


    ######################################################################################################

    def create_attribute_holder(self):
        self.currentHolder = cmds.createNode("transform", n="{}_foot_attributeHolder_node".format(self.letter))
        cmds.parent(self.currentHolder, self.foot_group)
        # create attribute
        if not pm.attributeQuery('IK_0_FK_1', node=self.currentHolder, exists=True):
            pm.addAttr(self.currentHolder, k=True, shortName='IKFK', longName='IK_0_FK_1',
                       defaultValue=0, minValue=0, maxValue=1)
        #
    ######################################################################################################

    def duplicate_and_bind(self):
        self.chains["MAIN"] = tools.list_joint_hier(self.foot_joint, with_end_joints=False)
        #
        for tag in "IK_FK".split("_"):
            root = tools.copySkeleton(self.foot_joint, tag).name()
            self.chains[tag] = tools.list_joint_hier(root, with_end_joints=False)
        #
        cmds.parent(self.chains["MAIN"][0], self.main_group)
        cmds.parent(self.chains["IK"][0], self.ik_group)
        cmds.parent(self.chains["FK"][0], self.fk_group)

        for idx, (ik, fk) in enumerate(zip(self.chains["IK"], self.chains["FK"])):
            main = self.chains["MAIN"][idx]
            const = cmds.parentConstraint([ik, fk], main)[0]
            cmds.setAttr(const + '.interpType', 2)
            node = cmds.createNode('plusMinusAverage', n=const + '_plusMinusAvg_%d' % idx)
            cmds.setAttr(node + '.operation', 2)
            cmds.setAttr(node + '.input2D[0].input2Dx', 1)
            attributes = cmds.listAttr(const)[-2:]
            #
            # locator to node
            pm.connectAttr(self.currentHolder + '.IK_0_FK_1', node + '.input2D[1].input2Dx', f=True)
            # locator to constraint
            pm.connectAttr(self.currentHolder + '.IK_0_FK_1', const + '.' + attributes[1], f=True)
            # node to contraint
            cmds.connectAttr(node + '.output2Dx', const + '.' + attributes[0], f=True)

    ###################################################################################################
    ######################################################################################################

    # clean method
    @tools.undo_cmds
    def build(self):
        self.create_attribute_holder()
        self.duplicate_and_bind()
        self.create_IK_reverse_foot(self.dummyNames)
        self.create_FK_foot()
        self.hook_to_leg()
        # self.hideShapesCB()
        # self.setupFootRoll()


    ######################################################################################################

    def cleanFeet(self):
        for itm in self.dummyNames:
            cmds.delete(itm)

    ######################################################################################################

    def create_FK_foot(self):
        self.fk_simple_obj = rigCommands.Simple_fk_command(joint_root=self.chains["FK"][0],
                                                          parent=self.controls_group,
                                                          color=13,
                                                          size=6)

        self._fk_controls = self.fk_simple_obj.create_chain()

    ###################################################################################################
    # build the foot structure based on the locators previusly created
    #

    def create_IK_reverse_foot(self, locArray):
        sideValue = cmds.getAttr(locArray[0] + '.tx')
        letter = ''

        if sideValue >= 0:
            letter = 'L'
        else:
            letter = 'R'

        # tag current foot
        self.currentFoot = letter

        ikHandle = '%s_leg_ikh' % letter
        ctrlDict = {}

        for itm in locArray:
            pt = cmds.ls(itm)[0]
            ctrl = None

            if itm == 'ankle':
                cmds.delete(cmds.parentConstraint(pt, self._ik_control))
                cmds.parentConstraint(self._ik_control, pt, mo=True)

            elif itm in ['ball', 'toes', 'tillIn', 'tillOut']:
                ctrl = control.Control(prefix=letter + '_' + pt + '_IK', translateTo=pt, angle='z',
                                       rotateTo=pt, scale=self.scaleIK * 4, lockChannels=['t', 's', 'v'])

                if itm == 'ball':
                    cmds.addAttr(ctrl.control, longName='footControl', dt="string")
                    cmds.setAttr(ctrl.control + '.footControl', 'ik_control', type='string')

                if itm == 'toes':
                    cmds.move(3, ctrl.control + '.cv[*]', relative=True, moveZ=True)
                    cmds.addAttr(ctrl.control, longName='toesControl', dt="string")
                    cmds.setAttr(ctrl.control + '.toesControl', 'ik_control', type='string')

                if itm == 'tillIn':
                    if sideValue >= 0:
                        cmds.transformLimits(ctrl.control, rotationX=[0, 0], enableRotationX=[1, 0])
                        cmds.transformLimits(ctrl.auto, rotationX=[0, 0], enableRotationX=[1, 0])
                        cmds.addAttr(ctrl.auto, longName='limitedChannel', dt="string")
                        cmds.setAttr(ctrl.auto + '.limitedChannel', 'minimum', type='string')

                    else:
                        cmds.transformLimits(ctrl.control, rotationX=[0, 0], enableRotationX=[0, 1])
                        cmds.transformLimits(ctrl.auto, rotationX=[0, 0], enableRotationX=[0, 1])
                        cmds.addAttr(ctrl.auto, longName='limitedChannel', dt="string")
                        cmds.setAttr(ctrl.auto + '.limitedChannel', 'maximum', type='string')

                elif itm == 'tillOut':
                    if sideValue >= 0:
                        cmds.transformLimits(ctrl.control, rotationX=[0, 0], enableRotationX=[0, 1])
                        cmds.transformLimits(ctrl.auto, rotationX=[0, 0], enableRotationX=[0, 1])
                        cmds.addAttr(ctrl.auto, longName='limitedChannel', dt="string")
                        cmds.setAttr(ctrl.auto + '.limitedChannel', 'maximum', type='string')

                    else:
                        cmds.transformLimits(ctrl.control, rotationX=[0, 0], enableRotationX=[1, 0])
                        cmds.transformLimits(ctrl.auto, rotationX=[0, 0], enableRotationX=[1, 0])
                        cmds.addAttr(ctrl.auto, longName='limitedChannel', dt="string")
                        cmds.setAttr(ctrl.auto + '.limitedChannel', 'minimum', type='string')

            elif itm in ['toes_tip', 'heel']:
                ctrl = control.Control(prefix=letter + '_' + pt + '_IK', translateTo=pt, angle='X',
                                       rotateTo=pt, scale=self.scaleIK * 4, lockChannels=['t', 's', 'v'])

            # add contorl to dictionary
            ctrlDict[itm] = ctrl

        # make auto attributes - means: create in IK controls all foot attributes for motions
        self.mainFootControl = self._ik_control
        self.currentControls = ctrlDict

        # make hierchy
        cmds.parent(ctrlDict['ball'].root, ctrlDict['toes_tip'].control)
        cmds.parent(ctrlDict['toes'].root, ctrlDict['toes_tip'].control)
        cmds.parent(ctrlDict['toes_tip'].root, ctrlDict['tillOut'].control)
        cmds.parent(ctrlDict['tillOut'].root, ctrlDict['tillIn'].control)
        cmds.parent(ctrlDict['tillIn'].root, ctrlDict['heel'].control)
        cmds.parentConstraint(self.mainFootControl , ctrlDict['heel'].root, mo=True)

        # parent ikHandle :
        cmds.addAttr(self.mainFootControl , k=True, longName='ball', defaultValue=0)
        cmds.addAttr(self.mainFootControl , k=True, longName='toes', defaultValue=0)
        cmds.addAttr(self.mainFootControl , k=True, longName='toes_tip', defaultValue=0)
        cmds.addAttr(self.mainFootControl , k=True, longName='tillOut', defaultValue=0)
        cmds.addAttr(self.mainFootControl , k=True, longName='tillIn', defaultValue=0)
        cmds.addAttr(self.mainFootControl , k=True, longName='heel', defaultValue=0)

        # add foot roll attribute
        cmds.addAttr(self.mainFootControl , k=True, longName='footRoll', defaultValue=0)

        # add show hide attribute
        cmds.addAttr(self.mainFootControl , k=True, longName='showControls', shortName='SWC', at='bool', defaultValue=1)

        for key, ctrl in ctrlDict.items():
            if key == 'ankle':
                continue

            shape = cmds.listRelatives(ctrl.control, s=True)[0]
            cmds.connectAttr(self.mainFootControl  + '.showControls', shape + '.visibility', f=True)

        # attact auto foot values to attributes in main control
        self.setupAutos()
        self.setupAutos(val=-360)
        self.setupAutos(val=360)

        # parent controls to ik joints
        cmds.parentConstraint(ctrlDict['ball'].control, self.chains["IK"][0], mo=True)
        cmds.parentConstraint(ctrlDict['toes'].control, self.chains["IK"][1], mo=True)
        cmds.parent(ctrlDict['heel'].root, self.controls_group)

        # save dic into current class property
        if letter == 'l':
            self.leftFoot = ctrlDict

        if letter == 'r':
            self.rightFoot = ctrlDict


    ###################################################################################################
    # blending chains
    #

    def flipAndDuplicate(self, locArray):

        for itm in locArray:
            cmds.setAttr(itm + '.tx', (cmds.getAttr(itm + '.tx') * -1))

    ###################################################################################################
    # Hide shapes from channel box in for each control in leg system
    #

    @tools.undo_cmds
    def hideShapesCB(self, noHideArray=[]):
        feet = [self.leftFoot, self.rightFoot]

        for itm in feet:
            if itm is not None:
                # hide shapes of controls from channelbox
                controls = itm.copy()
                rawControls = [itm.control for itm in controls.values()]
                tools.hideShapesChannelBox(rawControls, exception=noHideArray)

    ###################################################################################################

    def setupFootRoll(self, value=0, force=False):
        # find current main control
        #
        if len(cmds.ls(sl=True)) < 1:
            cmds.warning('must select a foot control to set driven keys')
            return

        attribute = 'footRoll'
        footAreas = ['toes_tip', 'ball', 'heel']
        visControls = []

        ctrlItems = {'L': self.leftFoot, 'R': self.rightFoot}
        interval = [0, 'L', 'R']
        selected = cmds.ls(sl=True)[0].encode('ascii', 'ignore')
        current = interval[interval.index(selected[0])]
        flipped = interval[interval.index(selected[0]) * -1]

        # check if system can be flipped or not
        flip = False

        # create foot roll group if not exist and locate in the middle of auto and root

        def createFootRollGrp(node):
            rool = cmds.group(n=node + '_footRollGrp', em=True)
            cmds.xform(rool, ws=True, m=cmds.xform(node, q=True, ws=True, m=True))
            parent = cmds.listRelatives(node, p=True)[0]
            cmds.parent(node, rool)
            cmds.parent(rool, parent)
            return rool

        # establish current foot
        curDriver = '{}.{}'.format(ctrlItems[current]['ankle'].control, attribute)
        cmds.setAttr(curDriver, value)
        # flipped
        if ctrlItems[flipped] is not None:
            flip = True

        if flip:
            flipDriver = '{}.{}'.format(ctrlItems[flipped]['ankle'].control, attribute)
            cmds.setAttr(flipDriver, value)

        for itm in footAreas:
            curAuto = ctrlItems[current][itm].auto
            if flip:
                flipAuto = ctrlItems[flipped][itm].auto

            # check if footRoolGrp is already created and in hierchy, if not will create it
            curRool = cmds.listRelatives(curAuto, p=True)[0]
            if flip:
                flipRool = cmds.listRelatives(flipAuto, p=True)[0]

            if not curRool.endswith('_footRollGrp'):
                curRool = createFootRollGrp(curAuto)
                if flip:
                    flipRool = createFootRollGrp(flipAuto)

            curDriven = '{}.{}'.format(curRool, 'ry')
            if flip:
                flipDriven = '{}.{}'.format(flipRool, 'ry')

            # collect values of driver global control and driven rool group to make operation
            globalCtrlValue = cmds.getAttr(cmds.listRelatives(curAuto)[0] + '.ry')

            curDrivenValue = cmds.getAttr(curDriven)
            curSetAttributeValue = globalCtrlValue + curDrivenValue

            if flip:
                flipDrivenValue = cmds.getAttr(flipDriven)
                flipSetAttributeValue = globalCtrlValue + flipDrivenValue

            # check if global control has no value then skip the driven key
            if globalCtrlValue != 0 or force is True:
                cmds.setAttr(curDriven, curSetAttributeValue)
                if flip:
                    cmds.setAttr(flipDriven, flipSetAttributeValue)

                cmds.setAttr(cmds.listRelatives(curAuto)[0] + '.ry', 0)
                cmds.setDrivenKeyframe(curDriven, currentDriver=curDriver, outTangentType='linear',
                                       inTangentType='linear', driverValue=value)

                if flip:
                    cmds.setDrivenKeyframe(flipDriven, currentDriver=flipDriver, outTangentType='linear',
                                           inTangentType='linear', driverValue=value)

            try:
                # set post and pre infinity for animCurve in driven
                curAnimCurve = cmds.listConnections(curDriven, t='animCurve')[0]
                cmds.setAttr(curAnimCurve + '.preInfinity', 1)
                cmds.setAttr(curAnimCurve + '.postInfinity', 1)

                if flip:
                    flipAnimCurve = cmds.listConnections(flipDriven, t='animCurve')[0]
                    cmds.setAttr(flipAnimCurve + '.preInfinity', 1)
                    cmds.setAttr(flipAnimCurve + '.postInfinity', 1)
            except:
                pass

            finally:
                cmds.select(clear=True)
    # foot autos for foot motions in channelbox
    #

    def setupAutos(self, val=0):
        # this will set up the slider values for foot motions in channelbox
        #
        # find current main control
        control = self.mainFootControl
        attributes = [att for att in self.dummyNames if att != 'ankle']

        for attr in attributes:
            driver = '{}.{}'.format(control, attr)
            drivenCtrl = self.currentControls[attr]
            driven = cmds.listRelatives(drivenCtrl.control, p=True)[0]

            if attr in ['tillOut', 'tillIn']:
                cmds.addAttr(control + '.' + attr, edit=True, minValue=0)
                check = cmds.getAttr(driven + '.limitedChannel')

                if check == 'minimum' and val >= 0:
                    cmds.setDrivenKeyframe(driven, attribute='rotateX', value=val, currentDriver=driver,
                                           outTangentType='linear', inTangentType='linear', driverValue=abs(val))
                if check == 'maximum' and val <= 0:
                    cmds.setDrivenKeyframe(driven, attribute='rotateX', value=val, currentDriver=driver,
                                           outTangentType='linear', inTangentType='linear', driverValue=abs(val))

            else:
                cmds.setDrivenKeyframe(driven, attribute='rotateY', value=val, currentDriver=driver,
                                       outTangentType='linear', inTangentType='linear', driverValue=val)

            # set post and pre infinity for animCurve in driven
            animCurve = cmds.listConnections(driven, t='animCurve')[0]
            cmds.setAttr(animCurve + '.preInfinity', 1)
            cmds.setAttr(animCurve + '.postInfinity', 1)


###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    foot = Feet(foot_joint="L_foot_01_JNT", hook="L_legEnd_JNT",
                hook_fk="L_legEnd_JNT", hook_ik="L_legEnd_JNT",
                attribute_holder = "L_leg_UI_CTL")
    foot.build()
    cmds.select(clear=True)
