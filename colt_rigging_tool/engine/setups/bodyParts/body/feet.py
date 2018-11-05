import collections
import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel
from engine.utils import tools
from engine.setups.controls import control


reload(control)
reload(tools)

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

    def __init__(self, legEndJoint='', name='feetClass', prefix='foot', scale=1.0, scaleIK=1.0, scaleFK=1.0):

        # public member
        self.letter = tools.getSideLetter(legEndJoint)
        self.prefix = prefix

        self.scale = scale
        self.scaleIK = scaleIK

        # general limb parent
        self.parent = legEndJoint

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

    ###################################################################################################
    # clean method

    def cleanFeet(self):
        for itm in self.dummyNames:
            cmds.delete(itm)

    ###################################################################################################
    # build the foot structure based on the locators previusly created
    #
    def createFootStructure(self, locArray):
        """

            Description: ARG1 = locators array on scene ARG2 = ik handle from IK leg system

        """

        sideValue = cmds.getAttr(locArray[0] + '.tx')
        letter = ''

        if sideValue >= 0:
            letter = 'l'
        else:
            letter = 'r'

        # tag current foot
        self.currentFoot = letter

        ikHandle = '%s_leg_ikh' % letter
        ctrlDict = {}

        attHolder = letter + '_leg_attributeHolderShape'
        self.currentHolder = attHolder

        for itm in locArray:
            pt = cmds.ls(itm)[0]
            ctrl = None

            if itm == 'ankle':
                ctrl = control.Control(prefix=letter + '_' + pt + '_IK', translateTo=pt, angle='x', rotateTo=pt, scale=self.scaleIK * 4)
                cmds.move(0, ctrl.control + '.cv[*]', absolute=True, moveY=True)
                cmds.parent(attHolder, ctrl.control, s=True, add=True)

            elif itm in ['ball', 'toes', 'tillIn', 'tillOut']:
                ctrl = control.Control(prefix=letter + '_' + pt + '_IK', translateTo=pt, angle='x', rotateTo=pt, scale=self.scaleIK * 4, lockChannels=['t', 's', 'v'])

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
                ctrl = control.Control(prefix=letter + '_' + pt + '_IK', translateTo=pt, angle='y', rotateTo=pt, scale=self.scaleIK * 4, lockChannels=['t', 's', 'v'])

            # add contorl to dictionary
            ctrlDict[itm] = ctrl

        # print(ctrlDict)
        #

        # make hierchy
        cmds.parent(ctrlDict['ball'].root, ctrlDict['toes_tip'].control)
        cmds.parent(ctrlDict['toes'].root, ctrlDict['toes_tip'].control)
        cmds.parent(ctrlDict['toes_tip'].root, ctrlDict['tillOut'].control)
        cmds.parent(ctrlDict['tillOut'].root, ctrlDict['tillIn'].control)
        cmds.parent(ctrlDict['tillIn'].root, ctrlDict['heel'].control)
        cmds.parent(ctrlDict['heel'].root, ctrlDict['ankle'].control)

        # parent ikHandle :
        cmds.parentConstraint(ctrlDict['ball'].control, ikHandle, mo=True)

        #
        # make auto attributes - means: create in IK controls all foot attributes for motions
        mainFootControl = ctrlDict['ankle']
        self.currentControls = ctrlDict

        cmds.addAttr(mainFootControl.control, k=True, longName='ball', defaultValue=0)
        cmds.addAttr(mainFootControl.control, k=True, longName='toes', defaultValue=0)
        cmds.addAttr(mainFootControl.control, k=True, longName='toes_tip', defaultValue=0)
        cmds.addAttr(mainFootControl.control, k=True, longName='tillOut', defaultValue=0)
        cmds.addAttr(mainFootControl.control, k=True, longName='tillIn', defaultValue=0)
        cmds.addAttr(mainFootControl.control, k=True, longName='heel', defaultValue=0)

        # add foot roll attribute
        cmds.addAttr(mainFootControl.control, k=True, longName='footRoll', defaultValue=0)

        # add show hide attribute
        cmds.addAttr(mainFootControl.control, k=True, longName='showControls', shortName='SWC', at='bool', defaultValue=1)

        for key, ctrl in ctrlDict.items():
            if key == 'ankle':
                continue

            shape = cmds.listRelatives(ctrl.control, s=True)[0]
            cmds.connectAttr(ctrlDict['ankle'].control + '.showControls', shape + '.visibility', f=True)

        # attact auto foot values to attributes in main control
        self.setupAutos()
        self.setupAutos(val=-360)
        self.setupAutos(val=360)

        # save dic into current class property
        if letter == 'l':
            self.leftFoot = ctrlDict

        if letter == 'r':
            self.rightFoot = ctrlDict

    ###################################################################################################
    # flips and duplicate the structure to current side to other
    #
    def flipAndDuplicate(self, locArray):

        for itm in locArray:
            cmds.setAttr(itm + '.tx', (cmds.getAttr(itm + '.tx') * -1))

        self.createFootStructure(locArray)
        self.makeBlend()
        self.cleanFeet()

    ###################################################################################################
    # blending chains
    #

    def makeBlend(self):

        sideArray = [itm for itm in cmds.ls('*_ctrl') if itm.startswith(self.currentFoot + '_')]

        jnt = self.parent[1:]
        joint = self.currentFoot + jnt

        foot_1 = cmds.listRelatives(joint)[0]
        foot_2 = cmds.listRelatives(foot_1)[0]

        footControls = []
        toesControls = []

        footDummies = []
        toesDummies = []

        for itm in sideArray:
            if cmds.attributeQuery('footControl', node=itm, exists=True):
                footControls.append(itm)
            if cmds.attributeQuery('toesControl', node=itm, exists=True):
                toesControls.append(itm)

        for ctrl in footControls:
            node = cmds.group(name=ctrl + '_footDummy', em=True)
            cmds.xform(node, ws=True, m=cmds.xform(foot_1, q=True, ws=True, m=True))
            cmds.parent(node, ctrl)
            footDummies.append(node)

        for ctrl in toesControls:
            node = cmds.group(name=ctrl + '_footDummy', em=True)
            cmds.xform(node, ws=True, m=cmds.xform(foot_2, q=True, ws=True, m=True))
            cmds.parent(node, ctrl)
            toesDummies.append(node)

        # orient contraint from dummies to main foot joint and toes joint
        footCons = cmds.orientConstraint(footDummies, foot_1)[0]
        toesCons = cmds.orientConstraint(toesDummies, foot_2)[0]

        # connect constraint to attribute holder
        footConsAtt = cmds.listAttr(footCons)[-2:]
        toesConsAtt = cmds.listAttr(toesCons)[-2:]

        # foot plus mins average to blending procs
        plusMinus = cmds.createNode('plusMinusAverage', n=self.currentFoot + '_footBlendPlsMnsAvg')
        cmds.setAttr(plusMinus + '.operation', 2)
        cmds.setAttr(plusMinus + '.input2D[0].input2Dx', 1)

        def connectAttributes(constraint, arrayIKFK):
            for att in arrayIKFK:
                if '_FK_' in att:
                    pm.connectAttr(self.currentHolder + '.IK_0_FK_1', constraint + '.' + att, f=True)
                if '_IK_' in att:
                    pm.connectAttr(self.currentHolder + '.IK_0_FK_1', plusMinus + '.input2D[1].input2Dx', f=True)
                    pm.connectAttr(plusMinus + '.output2D.output2Dx', constraint + '.' + att, f=True)

        # call this motherfucker function
        connectAttributes(footCons, footConsAtt)
        connectAttributes(toesCons, toesConsAtt)

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
    # foot rool slider attribute set up ----------- !!!!
    # i've done a crzy shit here but it works in one system and two at the same time
    #
    def setupFootRoll(self, value=0, force=False):
        # find current main control
        #
        if len(cmds.ls(sl=True)) < 1:
            cmds.warning('must select a foot control to set driven keys')
            return

        attribute = 'footRoll'
        footAreas = ['toes_tip', 'ball', 'heel']
        visControls = []

        ctrlItems = {'l': self.leftFoot, 'r': self.rightFoot}
        interval = [0, 'l', 'r']
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
                cmds.setDrivenKeyframe(curDriven, currentDriver=curDriver, outTangentType='linear', inTangentType='linear', driverValue=value)

                if flip:
                    cmds.setDrivenKeyframe(flipDriven, currentDriver=flipDriver, outTangentType='linear', inTangentType='linear', driverValue=value)

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

    ###################################################################################################

    # foot autos for foot motions in channelbox
    #
    def setupAutos(self, val=0):
        # this will set up the slider values for foot motions in channelbox
        #
        # find current main control
        control = self.currentControls['ankle']
        attributes = [att for att in self.dummyNames if att != 'ankle']

        for attr in attributes:
            driver = '{}.{}'.format(control.control, attr)
            drivenCtrl = self.currentControls[attr]
            driven = cmds.listRelatives(drivenCtrl.control, p=True)[0]

            if attr in ['tillOut', 'tillIn']:
                cmds.addAttr(control.control + '.' + attr, edit=True, minValue=0)
                check = cmds.getAttr(driven + '.limitedChannel')

                if check == 'minimum' and val >= 0:
                    cmds.setDrivenKeyframe(driven, attribute='rotateX', value=val, currentDriver=driver, outTangentType='linear', inTangentType='linear', driverValue=abs(val))
                if check == 'maximum' and val <= 0:
                    cmds.setDrivenKeyframe(driven, attribute='rotateX', value=val, currentDriver=driver, outTangentType='linear', inTangentType='linear', driverValue=abs(val))

            else:
                cmds.setDrivenKeyframe(driven, attribute='rotateY', value=val, currentDriver=driver, outTangentType='linear', inTangentType='linear', driverValue=val)

            # set post and pre infinity for animCurve in driven
            animCurve = cmds.listConnections(driven, t='animCurve')[0]
            cmds.setAttr(animCurve + '.preInfinity', 1)
            cmds.setAttr(animCurve + '.postInfinity', 1)

###################################################################################################
# builder function to keep class instances inside of a function and not in global


@tools.undo_cmds
def loader():
    if cmds.objExists('l_leg_sys_grp'):
        # cmds.delete('l_leg_sys_grp')
        pass

    # delete unused nodes
    mel.eval('MLdeleteUnused;')

    dummies = ['ankle', 'ball', 'toes', 'toes_tip', 'tillIn', 'tillOut', 'heel']
    # instance:
    foot = Feet(legEndJoint=LEG_END_JOINT, scaleFK=8)
    # foot.createLocators(dummies)
    foot.createFootStructure(dummies)
    foot.makeBlend()
    foot.hideShapesCB()
    foot.setupFootRoll()
    # foot.flipAndDuplicate(dummies)

###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    # loader()
    dummies = ['ankle', 'ball', 'toes', 'toes_tip', 'tillIn', 'tillOut', 'heel']
    # instance:

    def run():
        foot = Feet(legEndJoint=LEG_END_JOINT, scaleFK=8)
        # foot.createLocators(dummies)
        foot.createFootStructure(dummies)
        foot.makeBlend()
        foot.hideShapesCB()
        foot.setupFootRoll(force=True)

        return foot

    # foot = run()
    foot.setupFootRoll(value=-100, force=True)
    # foot.flipAndDuplicate(dummies)
    # foot.flipLocators(dummies)
    cmds.select(clear=True)
    pass
