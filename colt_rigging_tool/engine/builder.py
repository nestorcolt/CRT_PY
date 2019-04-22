
import maya.cmds as cmds
import pymel.core as pm
import maya.OpenMaya as om
import os
import shutil
import json

from engine.utils import tools
from engine.setups.modules import structure
from engine.setups.bodyParts.body import spine
from engine.setups.bodyParts.body import neck
from engine.setups.bodyParts.body import arms
from engine.setups.bodyParts.body import legs
from engine.setups.bodyParts.body import feet
from engine.asset.deformation import deformModule

reload(tools)
reload(structure)
reload(spine)
reload(neck)
reload(arms)
reload(legs)
reload(feet)
reload(deformModule)

###################################################################################################
# GLOBALS:
CURRENT_RIG = None

###################################################################################################


class BuildCharacterRig(object):
    def __init__(self):

        # public members:
        self.geometry = None
        self.character = None
        self.builder = None
        self.rigging = None

        self.rigJoints = None
        self.defJoints = None

        self.footDummies = ['ankle', 'ball', 'toes', 'toes_tip', 'tillIn', 'tillOut', 'heel']

        # body areas:
        self.spine = None
        self.neck = None
        #
        self.l_arm = None
        self.r_arm = None
        #
        self.l_leg = None
        self.r_leg = None

        self.feet = None
        #
        #
        self.head = None

        # controls COG and GlobalMain
        self.globalControl = None
        self.COG = None

    ###################################################################################################
    # populate public members
    #
    def populateProperties(self, geometry, character, builder):
        self.geometry = geometry
        self.character = character
        self.builder = builder

    ###################################################################################################
    # get both joint chains
    #
    def getSkeletons(self, structure=None):
        baseJntDef = self.builder['joint']
        # rig parent joint is pymel object type
        baseJntRig = tools.copySkeleton(baseJntDef, 'rig')

        cmds.select(baseJntRig.name())
        cmds.select(hi=True)
        riggingChain = cmds.ls(sl=True)
        cmds.select(clear=True)

        cmds.select(baseJntDef)
        cmds.select(hi=True)
        deformationChain = cmds.ls(sl=True)
        cmds.select(clear=True)

        self.rigJoints = riggingChain
        self.defJoints = deformationChain

        if structure:
            jointsFolder = structure.joints_group
            cmds.parent(baseJntRig.name(), jointsFolder)

    ###################################################################################################
    # Make rig structure, folders in outliner
    #

    def makeRig(self, charName, geometry, builder, backup=False):
        """

            Description: Init the file and construc the folder structure
            @param charName : character name in scene, "for prefix"
            @param geometry : geometry string name

        """
        if bool(builder):
            rigging = structure.Base(charName, mesh=geometry, parentJoint=builder['joint'], geoList=builder['geos'], builder=builder['builder'])
            self.globalControl = rigging.global_control_obj

            return rigging

    ###################################################################################################
    # this connects the deformation rig to control rig
    #

    def connectDefJoints(self, defJoints, rigJoints):
        attribute = self.globalControl.control + '.ConnectRig'

        for df, jnt in zip(defJoints, rigJoints):
            parConst = cmds.parentConstraint(jnt, df, mo=True)[0]
            scaleConst = cmds.scaleConstraint(jnt, df, mo=True)[0]

            parentAttr = cmds.listAttr(parConst)[-1]
            scaleAttr = cmds.listAttr(scaleConst)[-1]

            cmds.connectAttr(attribute, parConst + '.' + parentAttr, force=True)
            cmds.connectAttr(attribute, scaleConst + '.' + scaleAttr, force=True)

    ###################################################################################################
    # build spine and neck
    #

    def buildSpine(self, rig, hipsJnt, spineEndJnt, do_neck=False):
        # spine
        self.spine = spine.SpineStretch(rigObject=rig, joints=[hipsJnt, spineEndJnt], scaleIK=4, scaleFK=20)

        if do_neck:
            # neck
            self.neck = neck.NeckObject(rigObject=rig, spineObject=self.spine, spineEnd=spineEndJnt, scaleIK=15, scaleFK=10)

    # squach and stretch spine
    def spineSqandSt(self):
        spine = self.spine
        joints = [itm.replace('_jnt', '_rig') for itm in spine.spineJoints]
        spine.buildSqandSt(joints)
        cmds.parent(self.spine.spineAnimCurve, self.rigging.noXform_group)

    # calibrate the squath and stretch of spine
    def calibrateSpineStretch(self, raw=True):
        nullGrp = self.spine.spineAnimCurve
        cmds.select(nullGrp)

        if raw:
            sender = 'graphEditor'
            for panel in cmds.getPanel(sty="%s" % (sender)) or []:
                cmds.scriptedPanel(panel, e=True, to=True)

            cmds.FrameAll()

    ###################################################################################################
    # this connects the rig joints to driven locators in spine system
    #
    def connectRigToSpine(self):
        spineTargets = self.spine.targets

        if self.neck is not None:
            neckTargets = self.neck.targets
            spineTargets.extend(neckTargets)

        for tar, jnt in zip(spineTargets, self.rigJoints[:len(spineTargets)]):
            cmds.parentConstraint(tar, jnt, mo=True)

    ###################################################################################################
    # build arms method:
    #
    def buildArm(self, upperArmJoint, ikSys=False, fkSys=False, twist=False, twistValue=5):
        # instance:
        arm = arms.Arm(armJoint=upperArmJoint, scaleFK=8)

        if ikSys:
            arm.makeIK()
            arm.makeIkStretchSystem()

        if fkSys:
            arm.makeFK()
            arm.makeFkStretchSystem()

        if arm.checkIK and arm.checkFK:
            arm.makeBlending()
            arm.connectStretchSystem()
            arm.controlsVisibilitySetup()

        if twist:
            arm.collectTwistJoints(arm.shortChain[:-1], index=twistValue)
            arm.makeTwistSystem()

        arm.makeHand()
        arm.make_auto_fist(force=True)
        arm.groupSystem()
        arm.hideShapesCB()

        # parent arm groups to structure folders
        if self.rigging:
            cmds.parent(arm.ik_control.root, self.rigging.global_control_obj.control)
            cmds.parent(arm.poleVector.root, self.rigging.global_control_obj.control)
            # COG CONTROLS COMES FROM PYNODE NODETYPE
            pm.parent(arm.arm_main_grp, self.rigJoints[self.rigJoints.index(self.spine.spineJoints[-1].replace('_jnt', '_rig'))])

        return arm

    ###################################################################################################
    # build arms method:
    #
    def buildLeg(self, upperLegJoint, ikSys=False, fkSys=False, twist=False, twistValue=5):
        # instance:
        leg = legs.Leg(legJoint=upperLegJoint, scaleFK=8, rig_module=self.rigging)

        if ikSys:
            leg.makeIK()
            leg.makeIkStretchSystem()

        if fkSys:
            leg.makeFK()
            leg.makeFkStretchSystem()

        if leg.checkIK and leg.checkFK:
            leg.makeBlending()
            leg.connectStretchSystem()

        if twist:
            leg.collectTwistJoints(leg.shortChain[:-1], index=twistValue)
            leg.makeTwistSystem()

        leg.groupSystem()
        leg.hideShapesCB()

        # parent arm groups to structure folders
        if self.rigging:
            cmds.parent(leg.poleVector.root, self.rigging.global_control_obj.control)
            # COG CONTROLS COMES FROM PYNODE NODETYPE
            pm.parent(leg.leg_main_grp, self.spine.COG_control)

        return leg

    ###################################################################################################
    # build feet systems
    #
    # create dummy locators to position around/In foot shape (every char has a diferent foot shape)
    def createFootGuideLocators(self, dummies):
        """

            Description: to create locators for placement around the foot shape(every char has a diferent foot shape and size)
            ARG = self.footDummies prop

        """

        if all([cmds.objExists(itm) for itm in self.footDummies]) == True:
            cmds.warning('Dummy objects found on escene')
            return

        else:
            for itm in self.footDummies:
                try:
                    cmds.delete(itm)
                except:
                    pass

        trans = 0
        for name in dummies:
            loc = cmds.spaceLocator(n=name)[0]
            cmds.setAttr(loc + '.rz', -90)
            cmds.setAttr(loc + '.ry', -90)
            cmds.setAttr(loc + '.tz', trans)
            trans += 3

            shape = cmds.listRelatives(loc, s=True)[0]
            cmds.setAttr(shape + '.overrideEnabled', True)
            cmds.setAttr(shape + '.ovc', 13)

            for ch in 'XYZ':
                cmds.setAttr(shape + '.localScale%s' % ch, 2)

    ###################################################################################################
    # flip in X axis the guide locators for foot construction
    #
    def flipFootLocs(self, locArray):
        for itm in locArray:
            cmds.setAttr(itm + '.tx', (cmds.getAttr(itm + '.tx') * -1))

    ###################################################################################################
    # build feet class and construct the feet system
    #

    def buildFeet(self):

        legJoint = None

        if self.l_leg is None and self.r_leg is None:
            cmds.warning('No legs found, feet construction skipped')
            return

        if all([cmds.getAttr(itm + '.tx') for itm in self.footDummies]) < 0:
            print('all foot locators are in X-')
            try:
                legJoint = self.r_leg.legEndJoint
            except:
                self.flipFootLocs(self.footDummies)
                legJoint = self.l_leg.legEndJoint

        elif all([cmds.getAttr(itm + '.tx') for itm in self.footDummies]) > 0:
            print('all foot locators are in X+')
            try:
                legJoint = self.l_leg.legEndJoint
            except:
                self.flipFootLocs(self.footDummies)
                legJoint = self.r_leg.legEndJoint

        foot = feet.Feet(legEndJoint=legJoint, scaleFK=8)
        foot.createFootStructure(self.footDummies)
        foot.makeBlend()

        if all([self.l_leg, self.r_leg]) == True:
            foot.flipAndDuplicate(self.footDummies)

        self.feet = foot
        attributeHolders = [leg.attributeHolder.name().split('|')[1] for leg in [self.l_leg, self.r_leg] if leg is not None]
        foot.hideShapesCB(noHideArray=attributeHolders)

        feetArray = [foot.leftFoot, foot.rightFoot]
        for item in feetArray:
            if item is not None:
                footCtrl = item['ankle']
                cmds.parent(footCtrl.root, self.rigging.global_control_obj.control)

    ###################################################################################################
    # make visibility system for leg system
    #
    def makeLegVisSys(self):
        if self.l_leg is None and self.r_leg is None:
            return

        legsArray = [[self.l_leg, self.feet.leftFoot], [self.r_leg, self.feet.rightFoot]]

        for ft in legsArray:
            if ft[0] is not None:
                fkControls = [ctrl.control for ctrl in ft[0].fk_controls]
                ikControls = [ft[0].poleVectorAttachLine, ft[0].poleVector.control, ft[1]['ankle'].control]
                holder = ft[0].attributeHolder.name().split('|')[1]
                tools.makeControlsVisSetup(prefix=ft[0].letter + '_' + ft[0].prefix, attrHolder=holder, controlsIK=ikControls, controlsFK=fkControls)

    ###################################################################################################
    # bipass the foot rool setup in this main rig class
    #
    def setupFootRoll(self, value=0, force=True):
        self.feet.setupFootRoll(value=value, force=force)

    ###################################################################################################
    # setup finger roll attributes
    #
    def setupHandRoll(self, value=0, force=False):
        if len(cmds.ls(sl=True)) < 1:
            cmds.warning('must select a hand control to set driven keys')
            return

        selected = cmds.ls(sl=True)[0].encode('ascii', 'ignore')
        arms = {'l': self.l_arm, 'r': self.r_arm}
        interval = [0, 'l', 'r']
        current = interval[interval.index(selected[0])]
        flipped = interval[interval.index(selected[0]) * -1]

        # get current hand/arm:
        arm = arms[current]

        # mirror method:
        flipArm = arms[flipped]
        if flipArm is not None:
            for cur, flp in zip(arm.fingers, flipArm.fingers):
                # print(cur.control, flp.control)
                for ch in 'xyz':
                    get = cmds.getAttr(cur.control + '.r' + ch)
                    cmds.setAttr(flp.control + '.r' + ch, get)

            # call mirrored method
            flipArm.make_auto_fist(value=value, force=force)

        # call current method
        arm.make_auto_fist(value=value, force=force)

    ###################################################################################################
    # collects twist joints and match from rig joints to deformation joints
    #
    def matchTwistSystem(self):
        limbs = [self.l_arm, self.r_arm, self.r_leg, self.l_leg]

        for itm in limbs:
            if itm is not None:
                twistDict = itm.twistSysArray

                for key, val in twistDict.items():
                    defJoint = key.replace('_rig', '_jnt')
                    newTwsArr = tools.makeTwistJoints(defJoint, len(val))
                    cmds.parent(newTwsArr[0], defJoint)

                    # connect twist def to twist rig
                    self.connectDefJoints(newTwsArr, val)

    ###################################################################################################
    # creates skin cluster to character deformation system
    #
    def buildSkin(self, meshes, method=0):
        # method = 0 - Linear
        # method = 1 - Quaternion

        cmds.select(clear=True)
        for msh in meshes:
            cmds.skinCluster(self.defJoints[0], msh, name=msh + '_SkinCluster', dr=4.0, skinMethod=method,
                             maximumInfluences=50)

    ###################################################################################################
    # manage weights from character
    #
    def manageWeights(self, geometries=[], save=True):

        if save:
            deformModule.save_skinWeights(geometries)

        else:
            deformModule.load_skinWeights(geometries)

    ###################################################################################################
    # joints vis from all systems on and off
    #
    def jointsVisibility(self, operation=2):
        # operation 0 = bone
        # operation 2 = hide

        joints = cmds.ls(type='joint')
        for jnt in joints:
            if not jnt.endswith('_jnt'):
                cmds.setAttr(jnt + '.drawStyle', operation)

    ##################################################################################################
    # clean objects from escene and hide stuff
    #
    def doClean(self):
        toClean = [self.l_leg, self.r_leg, self.l_arm, self.r_arm]

        for itm in toClean:
            if itm is not None:
                itm.clean()

        for itm in self.footDummies:
            if cmds.objExists(itm):
                cmds.delete(itm)

