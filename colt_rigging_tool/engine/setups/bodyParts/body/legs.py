import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel
from engine.utils import tools
from engine.setups.controls import control

reload(control)
reload(tools)

###################################################################################################
# GLOBALS:
UPPERLEG_JOINT = 'r_upperleg_rig'

###################################################################################################
"""

    Description: I've tried to keep each method independent from the other,
    that means that each system "IK-FK" can be constructed separately and will work as an only system

"""
###################################################################################################


class Leg(object):

    def __init__(self, legJoint='', name='legClass', prefix='leg', scale=1.0, scaleIK=1.0, scaleFK=1.0,
                 rig_module=None, controlAngle=30):

        print(
            """
                Description: leg class to build complex stretch ik fk leg system on humanoid character
                Leg must have 3 joints: "upperleg to end" and foot must have 3 joints as well.
            """
        )

        # public member
        self.legJoint = legJoint

        self.letter = tools.getSideLetter(legJoint)
        self.prefix = prefix

        self.scale = scale
        self.scaleFK = scaleFK

        self.parent = cmds.listRelatives(legJoint, p=True)[0]

        # List joint chain from leg
        self.shortChain = tools.list_joint_hier(legJoint)
        #
        cmds.select(legJoint)
        cmds.select(hi=True)
        self.longChain = [tools.swapJointOrient(itm) for itm in cmds.ls(sl=True)[:-1]]

        cmds.select(clear=True)

        self.legEndJoint = self.shortChain[-1]

        # parent main rig upper lim to main rig upoper limb grp
        main_grp = cmds.group(n=self.letter + '_' + self.prefix + '_main_grp', em=True)
        cmds.xform(main_grp, ws=True, m=cmds.xform(legJoint, q=True, ws=True, m=True))
        cmds.parent(legJoint, main_grp)

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
        #
        self.global_control = rig_module.global_control_obj.control

        self.checkBlend = False

        #
        # holder group Init
        self.leg_main_grp = cmds.group(name=self.letter + '_' + prefix + '_sys_grp', em=True)
        cmds.xform(self.leg_main_grp, ws=True, m=cmds.xform(legJoint, q=True, ws=True, m=True))

        # parent main rig grp to limb sys grp
        cmds.parent(main_grp, self.leg_main_grp)

        #
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
        for jnt in self.longChain:
            tools.swapJointOrient(jnt)

    ###################################################################################################
    # clean objects no needed on scene after construction completes

    @tools.undo_cmds
    def clean(self):
        pm.delete(self.locShape)
        cmds.parent(self.leg_main_grp, self.parent)
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

        elif self.checkIK:
            tools.hideShapesChannelBox([self.poleVector.control])

        else:
            cmds.warning('FK and IK system must be both created to hide shapes from controls in channelbox')

    ###################################################################################################
    # group evertyhing inside of a holder grp (lol grp grp grp)

    @tools.undo_cmds
    def groupSystem(self):

        try:
            pm.parent(self.locShape, self.leg_main_grp)
        except:
            print('attribute holder already grouped')

        #
        if self.checkFK and not self.groupedFK:
            cmds.parent(self.fk_group, self.leg_main_grp)
            self.groupedFK = True

        if self.checkIK and not self.groupedIK:
            cmds.parent(self.ik_group, self.attachLineGrp, self.leg_main_grp)
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
        fk_main_jnt = tools.copySkeleton(self.longChain[0], 'FK')
        fk_hier = cmds.ls(sl=True)

        # xform main ik group
        cmds.xform(fk_group, ws=True, m=cmds.xform(fk_hier[0], q=True, ws=True, m=True))
        cmds.parent(fk_hier[0], fk_group)

        # swap orient values from jointO to rotate channels
        for jnt in fk_hier:
            tools.swapJointOrient(jnt)

        tools.overrideColor(fk_hier, 'green')
        fk_hier = fk_hier[:-1]
        cmds.select(clear=True)
        fk_hier.reverse()
        #
        fk_controls = []

        footJoint = [cmds.listRelatives(jnt)[0] for jnt in fk_hier if 'end' in jnt[:]][0]
        footJoint_2 = cmds.listRelatives(footJoint)[0]

        for idx, jnt in enumerate(fk_hier):

            dummy = cmds.group(n='dummy_grp_%d' % idx, em=True)
            cmds.setAttr(dummy + '.displayLocalAxis', True)
            cmds.xform(dummy, ws=True, m=cmds.xform(jnt, q=True, ws=True, m=True))

            # ctrl creation
            name = tools.remove_suffix(jnt)

            if jnt == footJoint:
                silly = cmds.group(n='silly', em=True)
                cmds.setAttr(silly + '.rz', -90)
                cmds.delete(cmds.orientConstraint(silly, dummy))
                cmds.delete(silly)

            if jnt == footJoint_2:
                silly = cmds.group(n='silly', em=True)
                cmds.setAttr(silly + '.rz', -90)
                cmds.setAttr(silly + '.ry', -90)
                cmds.delete(cmds.orientConstraint(silly, dummy))
                cmds.delete(silly)

            ctrl = control.Control(prefix=name + '_FK', translateTo=dummy, rotateTo=dummy, angle='x', scale=self.scaleFK)

            if jnt == footJoint:
                cmds.addAttr(ctrl.control, longName='footControl', dt="string")
                cmds.setAttr(ctrl.control + '.footControl', 'fk_control', type='string')

            if jnt == footJoint_2:
                cmds.addAttr(ctrl.control, longName='toesControl', dt="string")
                cmds.setAttr(ctrl.control + '.toesControl', 'fk_control', type='string')

            # hide shape from fk leg end ctrl i dont need it in the hier
            #
            if 'end' in jnt[:]:
                pm.hide(pm.PyNode(ctrl.control).getShape())

            # contraint Fk to control
            cmds.parentConstraint(ctrl.control, jnt, mo=True)
            fk_controls.append(ctrl)
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
        ik_main_jnt = tools.copySkeleton(self.shortChain[0], 'IK')

        ik_hier = cmds.ls(sl=True)
        cmds.delete(cmds.parent(ik_hier[-3], w=True))
        cmds.select(ik_hier[0])
        cmds.select(hi=True)

        ik_hier = cmds.ls(sl=True)

        # xform main ik group
        cmds.xform(ik_group, ws=True, m=cmds.xform(ik_hier[0], q=True, ws=True, m=True))
        cmds.parent(ik_hier[0], ik_group)

        # swap orient values from jointO to rotate channels
        for jnt in ik_hier:
            tools.swapJointOrient(jnt)

        tools.overrideColor(ik_hier, 'red')
        cmds.select(clear=True)

        #  set prefered angle first
        cmds.joint(ik_hier[0], edit=True, setPreferredAngles=True, ch=True)

        # creates ik handle
        ik_handle = cmds.ikHandle(n=self.letter + '_' + self.prefix + '_ikh', solver='ikRPsolver', startJoint=ik_hier[0], endEffector=ik_hier[-1])

        # create pole vector
        poleVec = control.Control(prefix=self.letter + '_' + self.prefix + '_poleVec', shape=3, translateTo=ik_hier[1], rotateTo=ik_hier[1], scale=2)

        # check if joint T value is positive oor negative
        if cmds.getAttr(ik_hier[1] + '.tx') < 0:
            cmds.move(-25, poleVec.root, moveZ=True, objectSpace=True, absolute=True)
        elif cmds.getAttr(ik_hier[1] + '.tx') >= 0:
            cmds.move(25, poleVec.root, moveZ=True, objectSpace=True, absolute=True)

        # set pole vector contranint
        cmds.poleVectorConstraint(poleVec.control, ik_handle[0])

        # rename effector and parent item to ik group
        cmds.rename(ik_handle[1], self.letter + '_' + self.prefix + '_effector')
        cmds.parent(ik_handle[0], ik_group)

        # populate ik class properties
        self.ik_group = ik_group
        self.ik_handle = ik_handle[0]
        self.ik_hier = ik_hier
        self.poleVector = poleVec

        # create pole vector attach line
        self.poleVectorAttachLine = tools.makePoleVectorLine(name=self.letter + '_' + self.prefix,
                                                             joint=self.ik_hier[1], poleVector=self.poleVector)

        self.attachLineGrp = cmds.group(n=self.poleVectorAttachLine + '_grp', em=True)
        cmds.parent(self.poleVectorAttachLine, self.attachLineGrp)

        # fk system activated
        self.checkIK = True

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

        for idx in range(3):
            const = cmds.orientConstraint([self.ik_hier[idx], self.fk_hier[idx]], self.shortChain[idx])[0]
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
        cmds.connectAttr(fk_plusMinus + '.output2D.output2Dx', self.fk_controls[1].root + '.translate.translateX', f=True)
        cmds.connectAttr(fk_plusMinus + '.output2D.output2Dy', self.fk_controls[2].root + '.translate.translateX', f=True)

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
        topGrp = self.ik_group
        handle = self.ik_handle
        upper = cmds.getAttr(self.ik_hier[1] + '.tx')
        end = cmds.getAttr(self.ik_hier[2] + '.tx')
        value = abs(upper + end)

        # creates dummy to attach to ik handle
        dummy_B = cmds.group(n=self.letter + '_' + self.prefix + 'ikStretchMeasurePoint_B', em=True)
        cmds.parentConstraint(handle, dummy_B)
        cmds.parent(dummy_B, topGrp)

        #
        # make IK Stretch

        ik_distBetween = cmds.createNode('distanceBetween', n=self.letter + '_' + self.prefix + '_distanceBetween_ikStretch')
        ik_condition = cmds.createNode('condition', n=self.letter + '_' + self.prefix + '_condition_ikStretch')
        ibypass_multiDiv = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_ikStretchFix')
        ik_multiDiv_A = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_ikStretch_A')
        ik_multiDiv_B = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_ikStretch_B')

        # manage distance between node
        cmds.connectAttr(topGrp + '.worldMatrix[0]', ik_distBetween + '.inMatrix1', f=True)
        cmds.connectAttr(dummy_B + '.worldMatrix[0]', ik_distBetween + '.inMatrix2', f=True)

        # connect to multiply divide A
        cmds.setAttr(ik_multiDiv_A + '.input2X', value)
        cmds.setAttr(ik_multiDiv_A + '.operation', 2)
        cmds.setAttr(ibypass_multiDiv + '.operation', 2)
        #
        cmds.connectAttr(ik_distBetween + '.distance', ibypass_multiDiv + '.input1X', f=True)
        cmds.connectAttr(self.global_control + '.globalScale', ibypass_multiDiv + '.input2X', f=True)

        # connect condition node
        cmds.setAttr(ik_condition + '.secondTerm', value)
        cmds.setAttr(ik_condition + '.operation', 2)

        cmds.connectAttr(ibypass_multiDiv + '.outputX', ik_condition + '.firstTerm', f=True)
        cmds.connectAttr(ibypass_multiDiv + '.outputX', ik_multiDiv_A + '.input1X', f=True)
        cmds.connectAttr(ik_multiDiv_A + '.outputX', ik_condition + '.colorIfTrueR', f=True)

        # connect to multiply divide B
        cmds.setAttr(ik_multiDiv_B + '.operation', 1)
        cmds.setAttr(ik_multiDiv_B + '.input2X', upper)
        cmds.setAttr(ik_multiDiv_B + '.input2Y', end)

        cmds.connectAttr(ik_condition + '.outColorR', ik_multiDiv_B + '.input1X', f=True)
        cmds.connectAttr(ik_condition + '.outColorR', ik_multiDiv_B + '.input1Y', f=True)

        # connect multiply divide B to transform nodes to ik chain
        cmds.connectAttr(ik_multiDiv_B + '.outputX', self.ik_hier[1] + '.translate.translateX', f=True)
        cmds.connectAttr(ik_multiDiv_B + '.outputY', self.ik_hier[2] + '.translate.translateX', f=True)

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
                cmds.parent(grp, self.leg_main_grp)

                for ch in 'XYZ':
                    cmds.setAttr(twist[0] + '.jointOrient%s' % ch, 0)
                    cmds.setAttr(twist[0] + '.rotate%s' % ch, 0)

                twistJoints[jnt] = twist

        if len(twistJoints) > 0:
            # print(twistJoints)
            self.twistSysArray = twistJoints

            return self.twistSysArray

    ###################################################################################################

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

                    cmds.orientConstraint(cmds.listRelatives(self.shortChain[-1])[0], ref_lower_limb, mo=True, skip=['y', 'z'])

                    cmds.connectAttr(ref_lower_limb + '.rotateX', multiplyNode + '.input1.input1X', force=True)

                    # divide scale or stretch
                    cmds.connectAttr(self.shortChain[2] + '.translateX', multiplyNodeStretch + '.input1.input1X', f=True)

                    for idx in range(1, factor + 1):
                        cmds.connectAttr(multiplyNode + '.outputX', TD[idx] + '.rotateX', f=True)
                        cmds.connectAttr(multiplyNodeStretch + '.outputX', TD[idx] + '.translateX', f=True)


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
    leg = Leg(legJoint=UPPERLEG_JOINT, scaleFK=8)

    leg.makeFK()
    leg.makeIK()
    leg.groupSystem()
    leg.makeBlending()

    leg.makeFkStretchSystem()
    leg.makeIkStretchSystem()

    leg.connectStretchSystem()

    leg.collectTwistJoints(leg.shortChain[:-1], index=5)
    leg.makeTwistSystem()

    leg.hideShapesCB()
    leg.clean()

###################################################################################################


# IN MODULE TEST:
if __name__ == '__main__':
    loader()
    cmds.select(clear=True)
    pass
