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
UPPERARM_JOINT = 'l_upperarm_rig'

###################################################################################################
"""

    Description: I've tried to keep each method independent from the other,
    that means that each system "IK-FK" can be constructed separately and will work as an only system

"""
###################################################################################################


class Arm(object):

    def __init__(self, armJoint='', name='armClass', prefix='arm', scale=1.0, scaleIK=1.0, scaleFK=1.0, controlAngle=30):

        print(
            """
                Description: arm class to build complex stretch ik fk arms system on humanoid character
                ARM must have 3 joints: "upperARM to end".
            """
        )

        # public member
        self.letter = tools.getSideLetter(armJoint)
        self.prefix = prefix

        self.scale = scale
        self.scaleFK = scaleFK

        # clavicle joint
        self.clavicle = cmds.listRelatives(armJoint, p=True)[0]

        # general limb parent
        self.parent = cmds.listRelatives(self.clavicle, p=True)[0]

        # List joint chain from leg
        self.shortChain = tools.list_joint_hier(armJoint)

        # unparentHandFromSystem
        self.hand = {}
        self.hand[self.shortChain[-1]] = cmds.parent(cmds.listRelatives(self.shortChain[-1])[0], w=True)[0]
        # print(self.hand)

        #
        #

        # INIT VARS FOR FK AND IK SYSTEM
        # FK VARS
        # check if fk system exist
        self.checkFK = False
        self.checkFKStretch = False

        # check if fk is already into global grp
        self.groupedFK = False

        self.fk_group = None
        self.fk_hier = None
        self.fk_controls = None

        # IK VARS
        # check if ik system exist
        self.checkIK = False
        self.checkIKStretch = False

        # check if ik is already into global grp
        self.groupedIK = False

        self.ik_group = None
        self.ik_handle = None
        self.ik_hier = None
        self.poleVector = None
        self.poleVectorAttachLine = None
        self.attachLineGrp = None
        self.ik_control = None
        self.ik_clavicle_control = None

        # hand controls
        self.handTopCtrl = None
        self.fingers = None
        self.fingers_auto_dic = None
        #

        self.checkBlend = False

        #
        # holder group Init
        self.arm_main_grp = cmds.group(name=self.letter + '_' + prefix + '_sys_grp', em=True)
        cmds.xform(self.arm_main_grp, ws=True, m=cmds.xform(self.parent, q=True, ws=True, m=True))
        #
        #

        # holder group for main chain Init
        self.main_grp = cmds.group(name=self.letter + '_' + prefix + '_main_grp', em=True)
        cmds.xform(self.main_grp, ws=True, m=cmds.xform(self.clavicle, q=True, ws=True, m=True))

        cmds.parent(self.clavicle, self.main_grp)
        cmds.parent(self.main_grp, self.arm_main_grp)

        # parent main sys group to spine joint (system parent)
        # cmds.parent(self.arm_main_grp, self.parent)

        #
        # create shape attribute holder
        self.locShape = pm.spaceLocator(n=self.letter + '_' + self.prefix + '_attributeHolder')
        self.attributeHolder = pm.ls(self.locShape, long=True)[0].getShape()
        cb_attrs = self.attributeHolder.listAttr(cb=True)

        # hide attributeHolder
        pm.hide(self.attributeHolder)

        for attr in cb_attrs:
            attr.lock()
            pm.setAttr(attr.name(), cb=False)

        # INIT NODES VARS FOR STRETCH SYS
        self.IKStretchNode = None
        self.FKStretchNode = None

        # Condition Node to connect stretch sys to rig joints
        self.IKFKStretchConditionNode = cmds.createNode('condition', name=self.letter + '_' + self.prefix + '_UnifyStretchCondNode')

        # create twist array to hold upper and lower twist chain
        self.twistSysArray = []

        # swap orient values from jointO to rotate channels
        mainJoints = self.shortChain[:]
        mainJoints.insert(0, self.clavicle)

        for jnt in mainJoints:
            tools.swapJointOrient(jnt)

    ###################################################################################################
    # clean objects no needed on scene after construction completes

    @tools.undo_cmds
    def clean(self):
        # re parent hand to arm
        cmds.parent(self.hand[self.shortChain[-1]], self.shortChain[-1])
        # del att holder object
        pm.delete(self.locShape)
        del(self.locShape)

        return True

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
            tools.hideShapesChannelBox([self.poleVector.control, self.ik_control.control, self.ik_clavicle_control.control], exception=[self.attributeHolder])

        else:
            cmds.warning('FK and IK system must be both created to hide shapes from controls in channelbox')

    ###################################################################################################
    # group evertyhing inside of a holder grp (lol grp grp grp)

    @tools.undo_cmds
    def groupSystem(self):

        try:
            pm.parent(self.locShape, self.arm_main_grp)
        except:
            print('attribute holder already grouped')

        #
        if self.checkFK and not self.groupedFK:
            cmds.parent(self.fk_group, self.arm_main_grp)
            self.groupedFK = True

        if self.checkIK and not self.groupedIK:
            cmds.parent(self.ik_group, self.attachLineGrp, self.arm_main_grp)
            self.groupedIK = True

    ###################################################################################################
    # Build Fk Chain
    #

    @tools.undo_cmds
    def makeFK(self):

        # check if FK is already created
        if self.checkFK:
            return

        fk_group = cmds.group(n=self.letter + '_' + self.prefix + '_fk_grp', em=True)
        fk_main_jnt = tools.copySkeleton(self.clavicle, 'FK')
        fk_hier = cmds.ls(sl=True)

        # xform main ik group
        cmds.xform(fk_group, ws=True, m=cmds.xform(fk_hier[0], q=True, ws=True, m=True))
        cmds.parent(fk_hier[0], fk_group)

        # swap orient values from jointO to rotate channels
        for jnt in fk_hier:
            tools.swapJointOrient(jnt)

        tools.overrideColor(fk_hier, 'green')
        cmds.select(clear=True)
        fk_hier.reverse()

        #
        fk_controls = []

        for idx, jnt in enumerate(fk_hier):

            dummy = cmds.group(n='dummy_grp_%d' % idx, em=True)
            cmds.setAttr(dummy + '.displayLocalAxis', True)
            cmds.xform(dummy, ws=True, m=cmds.xform(jnt, q=True, ws=True, m=True))

            # ctrl creation
            name = tools.remove_suffix(jnt)
            ctrl = None
            gimbLock = None

            if idx == len(fk_hier) - 1:
                ctrl = control.Control(prefix=name + '_FK', translateTo=dummy, rotateTo=dummy, angle='z', scale=self.scaleFK * 0.25)
                cmds.move(10, ctrl.control + ".cv[*]", moveZ=True, absolute=True)

            else:
                ctrl = control.Control(prefix=name + '_FK', translateTo=dummy, rotateTo=dummy, angle='x', scale=self.scaleFK)

                if idx == len(fk_hier) - 2:
                    gimbLock = control.Control(prefix=name + '_FK' + '_gimbLock', shape=3, translateTo=dummy, rotateTo=dummy, scale=self.scaleFK * 0.25)
                    cmds.setAttr(gimbLock.control + '.rotateOrder', 1)

                    if cmds.getAttr(jnt + '.tx') > 0:
                        cmds.move(12, gimbLock.control + ".cv[*]", moveY=True, objectSpace=True, relative=True)
                    elif cmds.getAttr(jnt + '.tx') < 0:
                        cmds.move(-12, gimbLock.control + ".cv[*]", moveY=True, objectSpace=True, relative=True)
            #
            # contraint Fk to control
            cmds.parentConstraint(ctrl.control, jnt, mo=True)
            fk_controls.append(ctrl)

            if gimbLock is not None:
                fk_controls.append(gimbLock)

            cmds.delete(dummy)

        # parenting the roots and controls from fk system
        fk_controls.reverse()

        for idx, ctrl in enumerate(fk_controls):
            if idx != len(fk_controls) - 1:
                cmds.parent(fk_controls[idx + 1].root, ctrl.control)

        # reverse arrays again to math order upside down
        fk_controls
        fk_hier.reverse()

        # parent to general fk leg system group
        cmds.parent(fk_controls[0].root, fk_group)

        # populate class fk properties
        self.fk_group = fk_group
        self.fk_hier = fk_hier
        self.fk_controls = fk_controls

        # fk system activated
        self.checkFK = True
        #
        #
        for itm in fk_controls:
            pm.parent(self.attributeHolder, itm.control, add=True, s=True)

        return {'fk_group': fk_group, 'fk_hier': fk_hier, 'fk_controls': fk_controls}

    ###################################################################################################
    # Build IK chain

    @tools.undo_cmds
    def makeIK(self):

        # check if IK is already created
        if self.checkIK:
            return

        ik_group = cmds.group(n=self.letter + '_' + self.prefix + '_ik_grp', em=True)
        ik_main_jnt = tools.copySkeleton(self.clavicle, 'IK')

        ik_hier = cmds.ls(sl=True)

        cmds.select(ik_hier[0])
        cmds.select(hi=True)

        ik_hier = cmds.ls(sl=True)

        # xform main ik group
        cmds.xform(ik_group, ws=True, m=cmds.xform(ik_hier[0], q=True, ws=True, m=True))

        tools.overrideColor(ik_hier, 'red')
        cmds.select(clear=True)

        #  set prefered angle first
        cmds.joint(ik_hier[0], edit=True, setPreferredAngles=True, ch=True)

        # creates ik handle
        ik_handle = cmds.ikHandle(n=self.letter + '_' + self.prefix + '_ikh', solver='ikRPsolver', startJoint=ik_hier[1], endEffector=ik_hier[-1])

        # create pole vector
        poleVec = control.Control(prefix=self.letter + '_' + self.prefix + '_poleVec', shape=4, scale=2)

        cmds.delete(cmds.pointConstraint([ik_hier[1], ik_hier[-1]], poleVec.root))
        cmds.delete(cmds.aimConstraint(ik_hier[2], poleVec.root, aim=(0.0, 0.0, 1.0)))

        # check if joint T value is positive oor negative
        if cmds.getAttr(ik_hier[2] + '.tx') < 0:
            cmds.move(60, poleVec.root, moveZ=True, objectSpace=True, absolute=True)
        elif cmds.getAttr(ik_hier[2] + '.tx') >= 0:
            cmds.move(60, poleVec.root, moveZ=True, objectSpace=True, absolute=True)

        cmds.delete(cmds.orientConstraint(ik_hier[2], poleVec.root))

        # set pole vector contranint
        cmds.poleVectorConstraint(poleVec.control, ik_handle[0])

        # rename effector and parent item to ik group
        cmds.rename(ik_handle[1], self.letter + '_' + self.prefix + '_effector')
        cmds.parent(ik_handle[0], ik_group)

        # create IK control
        ik_control = control.Control(prefix=self.letter + '_' + self.prefix + '_IK', shape=2, angle='x', translateTo=ik_hier[-1], rotateTo=ik_hier[-1], scale=self.scale * 6)
        cmds.parentConstraint(ik_control.control, ik_handle[0])

        pm.parent(self.attributeHolder, ik_control.control, add=True, s=True)

        # IK clavicle control
        clavNameCtrl = tools.remove_suffix(ik_main_jnt)
        ik_clavicleControl = control.Control(prefix=clavNameCtrl + '_IK', shape=4, translateTo=ik_hier[0], rotateTo=ik_hier[0], scale=self.scale)

        if cmds.getAttr(ik_hier[0] + '.tx') >= 0:
            cmds.move(10, ik_clavicleControl.control + ".cv[*]", moveZ=True, absolute=True)
        elif cmds.getAttr(ik_hier[0] + '.tx') < 0:
            cmds.move(10, ik_clavicleControl.control + ".cv[*]", moveZ=True, absolute=True)

        cmds.parent(ik_hier[0], ik_clavicleControl.control)
        cmds.parent(ik_clavicleControl.root, ik_group)

        # swap orient values from jointO to rotate channels
        for jnt in ik_hier:
            tools.swapJointOrient(jnt)

        # populate ik class properties
        self.ik_group = ik_group
        self.ik_handle = ik_handle[0]
        self.ik_hier = ik_hier
        self.poleVector = poleVec
        self.ik_control = ik_control
        self.ik_clavicle_control = ik_clavicleControl

        # create pole vector attach line
        self.poleVectorAttachLine = tools.makePoleVectorLine(name=self.letter + '_' + self.prefix,
                                                             joint=self.ik_hier[2], poleVector=self.poleVector)

        self.attachLineGrp = cmds.group(n=self.poleVectorAttachLine + '_grp', em=True)
        cmds.parent(self.poleVectorAttachLine, self.attachLineGrp)

        # fk system activated
        self.checkIK = True

        # set orient const to ik control to hand or wrist
        cmds.orientConstraint(ik_control.control, ik_hier[-1])

        return {'ik_group': ik_group, 'ik_handle': ik_handle, 'ik_hier': ik_hier, 'poleVector': poleVec}

    ###################################################################################################
    # Make IKFK blending

    @tools.undo_cmds
    def makeBlending(self):

        if not self.checkFK and not self.checkIK:
            cmds.warning('IK and FK systems must be created to make blending')
            return

        if self.checkBlend:
            return

        # attribute holder
        holderShape = self.attributeHolder

        # create attribute
        if not pm.attributeQuery('IK_0_FK_1', node=holderShape, exists=True):
            pm.addAttr(holderShape, k=True, shortName='IKFK', longName='IK_0_FK_1', defaultValue=0, minValue=0, maxValue=1)
        #

        mainRigJnt = self.shortChain[:]
        mainRigJnt.insert(0, self.clavicle)

        for idx in range(len(mainRigJnt)):
            const = cmds.orientConstraint([self.ik_hier[idx], self.fk_hier[idx]], mainRigJnt[idx])[0]
            cmds.setAttr(const + '.interpType', 0)
            node = cmds.createNode('plusMinusAverage', n=const + '_plusMinusAvg_%d' % idx)
            cmds.setAttr(node + '.operation', 2)
            cmds.setAttr(node + '.input2D[0].input2Dx', 1)

            attributes = cmds.listAttr(const)[-2:]

            #
            # locator to node
            pm.connectAttr(holderShape + '.IK_0_FK_1', node + '.input2D[1].input2Dx', f=True)
            # locator to constraint
            pm.connectAttr(holderShape + '.IK_0_FK_1', const + '.' + attributes[1], f=True)
            # node to contraint
            cmds.connectAttr(node + '.output2Dx', const + '.' + attributes[0], f=True)

        #
        # blend finished and done True
        self.checkBlend = True

    ###################################################################################################
    # Make stretch system

    # FK Stretch
    @tools.undo_cmds
    def makeFkStretchSystem(self):

        # check if FK stretch was already done
        if self.checkFKStretch:
            return

        # collect data:
        attHolder = cmds.ls(self.attributeHolder.split('|')[1])[0]

        #
        # make FK Stretch
        cmds.addAttr(attHolder, k=True, shortName='fkSt', longName='FK_Stretch', defaultValue=0, minValue=-50, maxValue=50)
        FKS_att = 'FK_Stretch'

        fk_plusMinus = cmds.createNode('plusMinusAverage', n=self.letter + '_' + self.prefix + '_plusMinusAvg_fkStretch')
        fk_multiDiv = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_fkStretch')

        # set attribute for plus minus average
        cmds.setAttr(fk_plusMinus + '.input2D[1].input2Dx', cmds.getAttr(self.shortChain[1] + '.tx'))
        cmds.setAttr(fk_plusMinus + '.input2D[1].input2Dy', cmds.getAttr(self.shortChain[2] + '.tx'))

        # connect multiply divide
        cmds.setAttr(fk_multiDiv + '.operation', 1)

        if cmds.getAttr(self.shortChain[1] + '.tx') < 0:
            cmds.setAttr(fk_multiDiv + '.input2X', -1)
            cmds.setAttr(fk_multiDiv + '.input2Y', -1)
        else:
            cmds.setAttr(fk_multiDiv + '.input2X', 1)
            cmds.setAttr(fk_multiDiv + '.input2Y', 1)

        #
        cmds.connectAttr(attHolder + '.' + FKS_att, fk_multiDiv + '.input1X', f=True)
        cmds.connectAttr(attHolder + '.' + FKS_att, fk_multiDiv + '.input1Y', f=True)

        # connect condition to plus minis avg
        cmds.connectAttr(fk_multiDiv + '.outputX', fk_plusMinus + '.input2D[0].input2Dx', f=True)
        cmds.connectAttr(fk_multiDiv + '.outputY', fk_plusMinus + '.input2D[0].input2Dy', f=True)

        # connect plus minus avg to transform nodes to fk chain
        cmds.connectAttr(fk_plusMinus + '.output2D.output2Dx', self.fk_controls[-2].root + '.translate.translateX', f=True)
        cmds.connectAttr(fk_plusMinus + '.output2D.output2Dy', self.fk_controls[-1].root + '.translate.translateX', f=True)

        self.FKStretchNode = fk_plusMinus

        self.checkFKStretch = True

    ###################################################################################################
    # IK Stretch

    @tools.undo_cmds
    def makeIkStretchSystem(self):

        # check if IK stretch was already done
        if self.checkIKStretch:
            return

        # collect data:
        dummy_A = cmds.group(n=self.letter + '_' + self.prefix + 'ikStretchMeasurePoint_A', em=True)
        cmds.delete(cmds.parentConstraint(self.ik_hier[1], dummy_A))
        cmds.parent(dummy_A, self.ik_hier[0])

        topGrp = dummy_A
        handle = self.ik_control.control
        upper = cmds.getAttr(self.ik_hier[-2] + '.tx')
        end = cmds.getAttr(self.ik_hier[-1] + '.tx')
        value = abs(upper + end)

        # creates dummy to attach to ik handle
        dummy_B = cmds.group(n=self.letter + '_' + self.prefix + 'ikStretchMeasurePoint_B', em=True)
        cmds.parentConstraint(handle, dummy_B)
        cmds.parent(dummy_B, topGrp)

        #
        # make IK Stretch

        ik_distBetween = cmds.createNode('distanceBetween', n=self.letter + '_' + self.prefix + '_distanceBetween_ikStretch')
        ik_condition = cmds.createNode('condition', n=self.letter + '_' + self.prefix + '_condition_ikStretch')
        ik_multiDiv_A = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_ikStretch_A')
        ik_multiDiv_B = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_ikStretch_B')

        # manage distance between node
        cmds.connectAttr(topGrp + '.worldMatrix[0]', ik_distBetween + '.inMatrix1', f=True)
        cmds.connectAttr(dummy_B + '.worldMatrix[0]', ik_distBetween + '.inMatrix2', f=True)

        # connect to multiply divide A
        cmds.setAttr(ik_multiDiv_A + '.input2X', value)
        cmds.setAttr(ik_multiDiv_A + '.operation', 2)
        cmds.connectAttr(ik_distBetween + '.distance', ik_multiDiv_A + '.input1X', f=True)

        # connect condition node
        cmds.setAttr(ik_condition + '.secondTerm', value)
        cmds.setAttr(ik_condition + '.operation', 2)

        cmds.connectAttr(ik_distBetween + '.distance', ik_condition + '.firstTerm', f=True)
        cmds.connectAttr(ik_multiDiv_A + '.outputX', ik_condition + '.colorIfTrueR', f=True)

        # connect to multiply divide B
        cmds.setAttr(ik_multiDiv_B + '.operation', 1)
        cmds.setAttr(ik_multiDiv_B + '.input2X', upper)
        cmds.setAttr(ik_multiDiv_B + '.input2Y', end)

        cmds.connectAttr(ik_condition + '.outColorR', ik_multiDiv_B + '.input1X', f=True)
        cmds.connectAttr(ik_condition + '.outColorR', ik_multiDiv_B + '.input1Y', f=True)

        # connect multiply divide B to transform nodes to ik chain
        cmds.connectAttr(ik_multiDiv_B + '.outputX', self.ik_hier[-2] + '.translate.translateX', f=True)
        cmds.connectAttr(ik_multiDiv_B + '.outputY', self.ik_hier[-1] + '.translate.translateX', f=True)

        self.IKStretchNode = ik_multiDiv_B

        self.checkIKStretch = True

    ###################################################################################################
    # Make Blending between stretch systems

    def connectStretchSystem(self):

        # Collect data:
        attHolder = cmds.ls(self.attributeHolder.split('|')[1])[0]
        condition = self.IKFKStretchConditionNode
        ik_node = self.IKStretchNode
        fk_node = self.FKStretchNode

        # check if there is a connection between condition node and main joints form leg
        connection = cmds.listConnections(condition, d=True, t='joint')
        runner = False

        if connection is not None:
            runner = any([itm for itm in connection if itm in self.shortChain])

        if not runner:
            cmds.connectAttr(condition + '.outColorR', self.shortChain[1] + '.translateX', f=True)
            cmds.connectAttr(condition + '.outColorG', self.shortChain[2] + '.translateX', f=True)

            # connect attribute holder to condition
            cmds.connectAttr(attHolder + '.IK_0_FK_1', condition + '.firstTerm', f=True)
            cmds.setAttr(condition + '.secondTerm', 1)
            cmds.setAttr(condition + '.operation', 0)

        if self.checkFK and cmds.listConnections(condition, d=True, type='plusMinusAverage') is None:
            cmds.connectAttr(fk_node + '.output2D.output2Dx', condition + '.colorIfTrueR', f=True)
            cmds.connectAttr(fk_node + '.output2D.output2Dy', condition + '.colorIfTrueG', f=True)
            cmds.setAttr(attHolder + '.IK_0_FK_1', 1)

        if self.checkIK and cmds.listConnections(condition, d=True, type='multiplyDivide') is None:
            cmds.connectAttr(ik_node + '.outputX', condition + '.colorIfFalseR', f=True)
            cmds.connectAttr(ik_node + '.outputY', condition + '.colorIfFalseG', f=True)
            cmds.setAttr(attHolder + '.IK_0_FK_1', 0)

    ###################################################################################################
    #  make twist for limbs
    #

    def collectTwistJoints(self, limbJoints, index=0):
        # will create and update the class property with twist chains and its parent from limb
        # return twist dictionary array with twist chains as value and limb joint as key

        twistJoints = {}

        for jnt in limbJoints:

            twist = tools.makeTwistJoints(jnt, index)

            if twist:
                for itm in twist:
                    tools.swapJointOrient(itm)

                grp = cmds.group(n=self.letter + '_' + self.prefix + '_' + jnt.split('_')[1] + '_twist_grp', em=True)
                cmds.delete(cmds.parentConstraint(jnt, grp))
                cmds.pointConstraint(jnt, grp)
                cmds.parent(twist[0], grp)
                cmds.parent(grp, self.arm_main_grp)

                for ch in 'XYZ':
                    cmds.setAttr(twist[0] + '.jointOrient%s' % ch, 0)
                    cmds.setAttr(twist[0] + '.rotate%s' % ch, 0)

                twistJoints[jnt] = twist

        if len(twistJoints) > 0:
            # print(twistJoints)
            self.twistSysArray = twistJoints

            return self.twistSysArray

    ###################################################################################################
    # create twist system for twist joints
    #

    def makeTwistSystem(self):

        if len(self.twistSysArray) < 1:
            cmds.warning('No twist joints found on structure')
            return

        for itm in self.shortChain:
            twistData = self.twistSysArray.get(itm, None)

            if twistData is not None:
                TD = twistData
                # create Ik from twist[0] to twist[1] and reset PV values
                handle = cmds.ikHandle(n='_'.join(TD[0].split('_')[:2]) + '_twist_ikh', solver='ikRPsolver', startJoint=TD[0], endEffector=TD[1])[0]
                for ch in 'XYZ':
                    cmds.setAttr('{}.poleVector{}'.format(handle, ch), 0)

                # parent the handle to the limb joint
                cmds.parent(handle, itm)

                # null vars
                ref_node = None
                ref_lower_limb = None

                # create multiplyDivide to connect rotation
                multiplyNode = cmds.createNode('multiplyDivide', n='_'.join(TD[0].split('_')[:2]) + '_twist_rot_Muldiv')
                multiplyNodeStretch = cmds.createNode('multiplyDivide', n='_'.join(TD[0].split('_')[:2]) + '_twist_trans_Muldiv')

                cmds.setAttr(multiplyNode + '.operation', 2)
                cmds.setAttr(multiplyNodeStretch + '.operation', 2)

                # division factor
                factor = len(TD) - 1

                cmds.setAttr(multiplyNode + '.input2X', factor)
                cmds.setAttr(multiplyNodeStretch + '.input2X', factor)

                # condition that check if limb twist is upper or lower area
                if self.shortChain.index(itm) == 0:
                    # create reference node
                    ref_node = cmds.createNode('transform', n='_'.join(TD[0].split('_')[:2]) + '_twist_reference')
                    cmds.delete(cmds.parentConstraint(TD[0], ref_node))

                    cmds.orientConstraint(self.shortChain[0], ref_node, skip=['y', 'z'])
                    cmds.parent(ref_node, TD[0])

                    cmds.connectAttr(ref_node + '.rotateX', multiplyNode + '.input1.input1X', force=True)

                    # divide scale or stretch
                    cmds.connectAttr(self.shortChain[1] + '.translateX', multiplyNodeStretch + '.input1.input1X', f=True)

                    for idx in range(1, factor + 1):
                        cmds.connectAttr(multiplyNode + '.outputX', TD[idx] + '.rotateX', f=True)
                        cmds.connectAttr(multiplyNodeStretch + '.outputX', TD[idx] + '.translateX', f=True)

                elif self.shortChain.index(itm) == 1:

                    ref_lower_limb = cmds.createNode('transform', n='_'.join(TD[0].split('_')[:2]) + '_twist_lowerRef')
                    cmds.delete(cmds.parentConstraint(TD[-1], ref_lower_limb))
                    cmds.parent(ref_lower_limb, TD[0])

                    cmds.orientConstraint(self.shortChain[-1], ref_lower_limb, mo=True, skip=['y', 'z'])
                    cmds.connectAttr(ref_lower_limb + '.rotateX', multiplyNode + '.input1.input1X', force=True)

                    # divide scale or stretch
                    cmds.connectAttr(self.shortChain[2] + '.translateX', multiplyNodeStretch + '.input1.input1X', f=True)

                    for idx in range(1, factor + 1):
                        cmds.connectAttr(multiplyNode + '.outputX', TD[idx] + '.rotateX', f=True)
                        cmds.connectAttr(multiplyNodeStretch + '.outputX', TD[idx] + '.translateX', f=True)

    ###################################################################################################
    # creates rig from hand
    #

    def makeHand(self):

        hand = self.hand.values()[0]
        handName = tools.remove_suffix(hand)
        handGrp = cmds.group(n=handName + '_grp', em=True)
        cmds.delete(cmds.parentConstraint(hand, handGrp))

        topControl = control.Control(prefix=handName + '_auto', translateTo=hand, rotateTo=hand, shape=4, scale=self.scale * 2, lockChannels=['t', 'r', 's', 'v'])
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
        cmds.parent(handGrp, self.arm_main_grp)
        # parent top ctrl to hand joint
        cmds.parent(topControl.root, hand)

        self.handTopCtrl = topControl
        self.fingers = controlsArray

        # make hand float attributes for channel box setting

        attributes = ['thumb', 'index', 'middle', 'ring', 'pinky']

        for att in attributes:
            cmds.addAttr(topControl.control, k=True, longName=att, shortName=att[1] + att[-1], minValue=-20, maxValue=50, defaultValue=0)

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
                    cmds.setDrivenKeyframe(driven, currentDriver=driver, outTangentType='linear', inTangentType='linear', driverValue=value)

                try:
                    # set post and pre infinity for animCurve in driven
                    animCurve = cmds.listConnections(driven, t='animCurve')[0]
                    cmds.setAttr(animCurve + '.preInfinity', 1)
                    cmds.setAttr(animCurve + '.postInfinity', 1)

                except:
                    pass

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

###################################################################################################
# builder function to keep class instances inside of a function and not in global


@tools.undo_cmds
def loader():
    if cmds.objExists('l_leg_sys_grp'):
        # cmds.delete('l_leg_sys_grp')
        pass

    # delete unused nodes
    mel.eval('MLdeleteUnused;')

    # instance:
    arm = Arm(armJoint=UPPERARM_JOINT, scaleFK=8)

    arm.makeFK()
    arm.makeIK()

    arm.makeHand()
    arm.make_auto_fist(force=True)

    arm.groupSystem()
    arm.makeBlending()

    arm.makeFkStretchSystem()
    arm.makeIkStretchSystem()

    arm.connectStretchSystem()

    arm.collectTwistJoints(arm.shortChain[:-1], index=5)
    arm.makeTwistSystem()

    arm.hideShapesCB()
    arm.controlsVisibilitySetup()
    arm.clean()

    return arm

###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    arm = loader()
    # arm.make_auto_fist(value=-20, force=True)
    cmds.select(clear=True)
    pass