import collections
import maya.cmds as cmds
import pymel.core as pm
import maya.mel as mel
from colt_rigging_tool.engine.utils import tools
from colt_rigging_tool.engine.setups.controls import control

reload(control)
reload(tools)


###################################################################################################
"""

    Description: I've tried to keep each method independent from the other,
    that means that each system "IK-FK" can be constructed separately and will work as an only system

"""
###################################################################################################


class Limb(object):

    def __init__(self,
                 firstJoint='',
                 name='limbClass',
                 prefix='arm',
                 scale=1.0,
                 scaleIK=1.0,
                 scaleFK=1.0,
                 controlAngle=30,
                 pole_vector_distance = 60,
                 positive_ik=True,
                 fk_hook= None,
                 ik_hook= None,
                 pv_hook= None):

        # public member
        self.letter = tools.getSideLetter(firstJoint)
        self.prefix = prefix

        self.scale = scale
        self.scaleFK = scaleFK
        self.fk_hook = fk_hook
        self.ik_hook = ik_hook
        self.pv_hook = pv_hook

        # List joint chain from leg
        self.inputChain = tools.list_joint_hier(firstJoint)

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
        self.positive_ik = positive_ik

        # IK VARS
        # check if ik system exist
        self.checkIK = False
        self.checkIKStretch = False
        self.poleVector_distance = pole_vector_distance

        # check if ik is already into global grp
        self.groupedIK = False

        self.ik_group = None
        self.ik_handle = None
        self.ik_hier = None
        self.poleVector = None
        self.poleVectorAttachLine = None
        self.attachLineGrp = None
        self.ik_control = None
        self.checkBlend = False

        #
        # holder group Init
        self.rig_group = cmds.group(name=self.letter + '_' + prefix + '_rig_GRP', em=True)
        self.controls_group = cmds.group(name=self.letter + '_' + prefix + '_controls_GRP', em=True)
        self.skell_group = None
        self.limb_modules_groups = []
        self.limb_modules_groups.append(self.rig_group)

        # holder group for main chain Init
        self.main_grp = cmds.group(name=self.letter + '_' + prefix + '_main_GRP', em=True)
        cmds.parent(self.inputChain[0], self.main_grp)
        cmds.parent(self.main_grp, self.rig_group)


        ######################################################################################################
        # create shape attribute holder
        #
        self.attributeHolder_obj = pm.circle(n=self.letter + '_' + self.prefix + '_UI_CTL')[0]
        self.attributeHolder = self.attributeHolder_obj.name()
        cb_attrs = self.attributeHolder_obj.listAttr(k=True)
        cmds.parentConstraint(self.inputChain[-1], self.attributeHolder)
        cmds.parent(self.attributeHolder, self.rig_group)
        cmds.parent(self.attributeHolder, self.controls_group)

        tools.overrideColor(self.attributeHolder, "red", single=True)
        cmds.scale(scale * 4, scale * 4, scale * 4, self.attributeHolder + "*Shape" + ".cv[*]", relative=True)

        for attr in cb_attrs:
            attr.lock()
            try:
                pm.setAttr(attr.name(), cb=False, k=False)
            except:
                pass

        ######################################################################################################
        # INIT NODES VARS FOR STRETCH SYS
        self.IKStretchNode = None
        self.FKStretchNode = None

        # Condition Node to connect stretch sys to rig joints
        self.IKFKStretchConditionNode = cmds.createNode('condition', name=self.letter + '_' + self.prefix + '_UnifyStretchCondNode')

        # create twist array to hold upper and lower twist chain
        self.twistSysArray = []

    ###################################################################################################

    def hook(self):
        if self.fk_hook is not None:
            cmds.parentConstraint(self.fk_hook, self.fk_controls[0].root, mo=True)

        if self.ik_hook is not None:
            cmds.parentConstraint(self.ik_hook, self.ik_group, mo=True)

    ###################################################################################################
    # clean objects no needed on scene after construction completes

    @tools.undo_cmds
    def clean(self):
        # TODO IMPLEMENT CLEAN METHOD
        pass
    


    ###################################################################################################
    # group evertyhing inside of a holder grp (lol grp grp grp)

    @tools.undo_cmds
    def groupSystem(self):
        #
        if self.checkFK and not self.groupedFK:
            cmds.parent(self.fk_group, self.rig_group)
            cmds.parent(self.fk_controls[0].root, self.controls_group)
            self.groupedFK = True

        if self.checkIK and not self.groupedIK:
            cmds.parent(self.ik_group, self.attachLineGrp, self.rig_group)
            cmds.parent(self.ik_mainControl_group, self.poleVector.root,  self.controls_group)
            self.groupedIK = True

    ###################################################################################################
    # Build Fk Chain
    #
    @tools.undo_cmds
    def makeFK(self, simple_fk=False, world_orient=False):

        # check if FK is already created
        if self.checkFK:
            return

        fk_group = cmds.group(n=self.letter + '_' + self.prefix + '_FK_GRP', em=True)
        fk_main_jnt = tools.copySkeleton(self.inputChain[0], 'FK')
        fk_hier = cmds.ls(sl=True)

        # xform main ik group
        cmds.xform(fk_group, ws=True, m=cmds.xform(fk_hier[0], q=True, ws=True, m=True))
        cmds.parent(fk_hier[0], fk_group)
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

            if jnt == fk_hier[-1] and simple_fk == False:
                ctrl = control.Control(prefix=name + '_FK', translateTo=dummy, rotateTo=dummy,
                                       angle='z', scale=self.scaleFK * 0.25)
                cmds.move(10, ctrl.control + ".cv[*]", moveZ=True, absolute=True)

            else:
                ctrl = control.Control(prefix=name + '_FK', translateTo=dummy, rotateTo=dummy,
                                       angle='x', scale=self.scaleFK)

                if jnt == fk_hier[-2] and simple_fk == False:
                    gimbLock = control.Control(prefix=name + '_FK' + '_gimbLock', shape=3, translateTo=dummy,
                                               rotateTo=dummy, scale=self.scaleFK * 0.25)
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
        fk_hier.reverse()

        #
        if world_orient:
            cmds.rotate(0,fk_controls[-1].root, rotateY=True, absolute=True, worldSpace=True)

        # populate class fk properties
        self.fk_group = fk_group
        self.fk_hier = fk_hier
        self.fk_controls = fk_controls

        # fk system activated
        self.checkFK = True
        #
        #
        return {'fk_group': fk_group, 'fk_hier': fk_hier, 'fk_controls': fk_controls}

    ###################################################################################################
    # Build IK chain
    #
    @tools.undo_cmds
    def makeIK(self, world_orient=False):

        # check if IK is already created
        if self.checkIK:
            return

        ik_group = cmds.group(n=self.letter + '_' + self.prefix + '_IK_GRP', em=True)
        self.ik_mainControl_group = cmds.group(n=self.letter + '_' + self.prefix + '_IK_controls_GRP', em=True)

        # this returns a pymel object. get object.name()
        ik_main_jnt = tools.copySkeleton(self.inputChain[0], 'IK')
        cmds.delete(cmds.parentConstraint(ik_main_jnt.name(), ik_group))

        cmds.select(ik_main_jnt.name())
        cmds.select(hi=True)
        ik_hier = cmds.ls(sl=True)

        tools.overrideColor(ik_hier, 'red')
        cmds.select(clear=True)
        dummie_ik_aim = cmds.createNode("transform", n="dummie_ik_aim_node")
        cmds.delete(cmds.pointConstraint(ik_hier[-2], dummie_ik_aim))

        if self.positive_ik:
            cmds.move(45, dummie_ik_aim, moveZ=True, worldSpace=True, absolute= True)
        else:
            cmds.move(-45, dummie_ik_aim, moveZ=True, worldSpace=True, absolute=True)

        # get previous angles from joint orient
        joint_orient = map(lambda axis: cmds.getAttr("{}.jointOrient{}".format(ik_hier[-2], axis)),"XYZ")

        #  set prefered angle
        x_val = cmds.getAttr("{}.translateX".format(ik_main_jnt.name()))
        get_sign = lambda x: (1, -1)[x < 0]
        cmds.delete(cmds.aimConstraint(dummie_ik_aim, ik_hier[-2], aimVector=(get_sign(x_val), 0, 0)))
        cmds.joint(ik_hier[-2], edit=True, setPreferredAngles=True, children=False)

        pref_angle_raw = cmds.getAttr("{}.preferredAngleY".format(ik_hier[-2]))

        # back to previous angles
        map(lambda axis, angle: cmds.setAttr("{}.jointOrient{}".format(ik_hier[-2], axis), angle),
            "XYZ", joint_orient)

        map(lambda axis, angle: cmds.setAttr("{}.preferredAngle{}".format(ik_hier[-2], axis), angle),
            "XYZ", (0,get_sign(pref_angle_raw), 0) )


        cmds.joint(ik_hier[-2], edit=True, angleX="0deg", angleY="0deg", angleZ="0deg")

        # creates ik handle
        ik_handle = cmds.ikHandle(n=self.letter + '_' + self.prefix + '_ikh', solver='ikRPsolver',
                                  startJoint=ik_hier[-3], endEffector=ik_hier[-1])
        # create pole vector
        poleVec = control.Control(prefix=self.letter + '_' + self.prefix + '_poleVec', shape=4, scale=2)

        root, mid, end = map(lambda item: cmds.xform(item, ws=True, q=True, t=True), ik_hier[-3:])

        # Vector math function to get pole vector exact position
        pv_position = tools.get_pole_vec_pos(root, mid, end, self.poleVector_distance)
        cmds.move(pv_position.x, pv_position.y, pv_position.z, poleVec.root, worldSpace=True, absolute=True)

        # set pole vector contranint
        cmds.poleVectorConstraint(poleVec.control, ik_handle[0])

        # rename effector and parent item to ik group
        cmds.rename(ik_handle[1], self.letter + '_' + self.prefix + '_effector')
        cmds.parent(ik_handle[0], ik_group)

        # create IK control
        control_orientation = ik_hier[-1]
        #
        ik_control = control.Control(prefix=self.letter + '_' + self.prefix + '_IK', shape=2, angle='x',
                                     translateTo=ik_hier[-1], rotateTo=ik_hier[-1], scale=self.scale * 6)

        cmds.parent(ik_control.root, self.ik_mainControl_group)
        cmds.parentConstraint(ik_control.control, ik_handle[0])
        cmds.parent(ik_main_jnt.name(), ik_group)

        # populate ik class properties
        self.ik_group = ik_group
        self.ik_handle = ik_handle[0]
        self.ik_hier = ik_hier
        self.poleVector = poleVec
        self.ik_control = ik_control

        # create pole vector attach line
        self.poleVectorAttachLine = tools.makePoleVectorLine(name=self.letter + '_' + self.prefix,
                                                             joint=self.ik_hier[-2], poleVector=self.poleVector)

        self.attachLineGrp = cmds.group(n=self.poleVectorAttachLine + '_GRP', em=True)
        cmds.parent(self.poleVectorAttachLine, self.attachLineGrp)

        # fk system activated
        self.checkIK = True

        # set orient const to ik control to hand or wrist
        cmds.orientConstraint(ik_control.control, ik_hier[-1])
        cmds.delete(dummie_ik_aim)

        #
        if world_orient:
            cmds.rotate(0,ik_control.root, rotateY=True, absolute=True, worldSpace=True)

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
        mainRigJnt = self.inputChain[:]
        for idx in range(len(mainRigJnt)):
            const = cmds.parentConstraint([self.ik_hier[idx], self.fk_hier[idx]], mainRigJnt[idx])[0]
            cmds.setAttr(const + '.interpType', 2)
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
        attHolder = self.attributeHolder

        #
        # make FK Stretch
        cmds.addAttr(attHolder, k=True, shortName='fkSt', longName='FK_Stretch', defaultValue=0, minValue=-50, maxValue=50)
        FKS_att = 'FK_Stretch'

        fk_plusMinus = cmds.createNode('plusMinusAverage', n=self.letter + '_' + self.prefix + '_plusMinusAvg_fkStretch')
        fk_multiDiv = cmds.createNode('multiplyDivide', n=self.letter + '_' + self.prefix + '_multiDiv_fkStretch')

        # set attribute for plus minus average
        cmds.setAttr(fk_plusMinus + '.input2D[1].input2Dx', cmds.getAttr(self.inputChain[-2] + '.tx'))
        cmds.setAttr(fk_plusMinus + '.input2D[1].input2Dy', cmds.getAttr(self.inputChain[-1] + '.tx'))

        # connect multiply divide
        cmds.setAttr(fk_multiDiv + '.operation', 1)
        cmds.setAttr(fk_plusMinus + '.operation', 1)

        if cmds.getAttr(self.inputChain[-2] + '.tx') < 0:
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
        cmds.delete(cmds.parentConstraint(self.ik_hier[-3], dummy_A))
        cmds.parent(dummy_A, self.ik_group)

        topGrp = dummy_A
        handle = self.ik_control.control
        upper = cmds.getAttr(self.ik_hier[-2] + '.tx')
        end = cmds.getAttr(self.ik_hier[-1] + '.tx')
        value = abs(upper + end)

        # creates dummy to attach to ik handle
        dummy_B = cmds.group(n=self.letter + '_' + self.prefix + 'ikStretchMeasurePoint_B', em=True)
        cmds.parentConstraint(handle, dummy_B)
        cmds.parent(dummy_B, topGrp)


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
        attHolder = self.attributeHolder
        condition = self.IKFKStretchConditionNode
        ik_node = self.IKStretchNode
        fk_node = self.FKStretchNode
        #
        reverse = cmds.createNode("reverse", n="{}Stretch_REV".format(attHolder))
        stretch_fix_PMA_01 = cmds.createNode("plusMinusAverage", n="{}StretchFix_01_PMA".format(attHolder))
        stretch_fix_MDV = cmds.createNode("multiplyDivide", n="{}StretchFix_MDV".format(attHolder))
        stretch_fix_PMA_02 = cmds.createNode("plusMinusAverage", n="{}StretchFix_02_PMA".format(attHolder))

        # set fix nodes attributes
        cmds.setAttr("{}.operation".format(stretch_fix_PMA_01), 2)
        cmds.setAttr("{}.operation".format(stretch_fix_MDV), 1)
        cmds.setAttr("{}.operation".format(stretch_fix_PMA_02), 1)
        #
        # connect fix nodes
        cmds.connectAttr("{}.output2Dx".format(stretch_fix_PMA_01), "{}.input1X".format(stretch_fix_MDV))
        cmds.connectAttr("{}.output2Dy".format(stretch_fix_PMA_01), "{}.input1Y".format(stretch_fix_MDV))

        cmds.connectAttr("{}.outputX".format(stretch_fix_MDV), "{}.input2D[0].input2Dx".format(stretch_fix_PMA_02))
        cmds.connectAttr("{}.outputY".format(stretch_fix_MDV), "{}.input2D[0].input2Dy".format(stretch_fix_PMA_02))

        cmds.connectAttr(fk_node + '.output2D.output2Dx', "{}.input2D[1].input2Dx".format(stretch_fix_PMA_02), f=True)
        cmds.connectAttr(fk_node + '.output2D.output2Dy', "{}.input2D[1].input2Dy".format(stretch_fix_PMA_02), f=True)

        cmds.connectAttr("{}.IK_0_FK_1".format(attHolder), "{}.inputX".format(reverse))
        cmds.connectAttr("{}.outputX".format(reverse), "{}.input2X".format(stretch_fix_MDV))
        cmds.connectAttr("{}.outputX".format(reverse), "{}.input2Y".format(stretch_fix_MDV))

        cmds.connectAttr("{}.outputX".format(ik_node), "{}.input2D[0].input2Dx".format(stretch_fix_PMA_01))
        cmds.connectAttr("{}.outputY".format(ik_node), "{}.input2D[0].input2Dy".format(stretch_fix_PMA_01))

        cmds.connectAttr("{}.output2Dx".format(fk_node), "{}.input2D[1].input2Dx".format(stretch_fix_PMA_01))
        cmds.connectAttr("{}.output2Dy".format(fk_node), "{}.input2D[1].input2Dy".format(stretch_fix_PMA_01))

        # check if there is a connection between condition node and main joints form leg
        connection = cmds.listConnections(condition, d=True, type='joint')
        runner = False

        if connection is not None:
            runner = any([itm for itm in connection if itm in self.inputChain])

        if not runner:
            cmds.connectAttr(condition + '.outColorR', self.inputChain[-2] + '.translateX', f=True)
            cmds.connectAttr(condition + '.outColorG', self.inputChain[-1] + '.translateX', f=True)

            # connect attribute holder to condition
            cmds.connectAttr(attHolder + '.IK_0_FK_1', condition + '.firstTerm', f=True)
            cmds.setAttr(condition + '.secondTerm', 0)
            cmds.setAttr(condition + '.operation', 2)

        if self.checkFK and cmds.listConnections(condition, d=True, type='plusMinusAverage') is None:
            cmds.connectAttr(stretch_fix_PMA_02 + '.output2D.output2Dx', condition + '.colorIfTrueR', f=True)
            cmds.connectAttr(stretch_fix_PMA_02 + '.output2D.output2Dy', condition + '.colorIfTrueG', f=True)
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

                grp = cmds.group(n=self.letter + '_' + self.prefix + '_' + jnt.split('_')[1] + '_twist_GRP', em=True)
                # will align the twist parent to upper limb or lower limb
                cmds.delete(cmds.parentConstraint(jnt, grp))
                cmds.pointConstraint(jnt, grp)
                x_val = cmds.getAttr("{}.translateX".format(jnt))

                # esto del get sign esta cojonudo
                get_sign = lambda x: (1, -1)[x < 0]
                cmds.aimConstraint(cmds.listRelatives(jnt)[0], grp, aimVector=(get_sign(x_val), 0, 0))
                cmds.parent(twist[0], grp)
                cmds.parent(grp, self.rig_group)
                #
                for ch in 'XYZ':
                    cmds.setAttr(twist[0] + '.jointOrient%s' % ch, 0)
                    cmds.setAttr(twist[0] + '.rotate%s' % ch, 0)

                twistJoints[jnt] = twist

        if len(twistJoints) > 0:
            self.twistSysArray = twistJoints

            return self.twistSysArray

    ###################################################################################################
    # create twist system for twist joints
    #

    def makeTwistSystem(self):

        if len(self.twistSysArray) < 1:
            cmds.warning('No twist joints found on structure')
            return

        for itm in self.inputChain[-3:]:
            twistData = self.twistSysArray.get(itm, None)

            if twistData is not None:
                TD = twistData
                # create Ik from twist[0] to twist[1] and reset PV values
                handle = cmds.ikHandle(n='_'.join(TD[0].split('_')[:2]) + '_twist_ikh', solver='ikRPsolver',
                                       startJoint=TD[0], endEffector=TD[1])[0]
                for ch in 'XYZ':
                    cmds.setAttr('{}.poleVector{}'.format(handle, ch), 0)

                # parent the handle to the limb joint
                cmds.parentConstraint(itm, handle)
                cmds.parent(handle, cmds.listRelatives(TD[0], parent=True)[0])

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
                if itm == self.inputChain[-3]:
                    # create reference node
                    ref_node = cmds.createNode('transform', n='_'.join(TD[0].split('_')[:2]) + '_twist_reference')
                    cmds.delete(cmds.parentConstraint(TD[0], ref_node))

                    cmds.orientConstraint(self.inputChain[-3], ref_node, skip=['y', 'z'])
                    cmds.parent(ref_node, TD[0])

                    cmds.connectAttr(ref_node + '.rotateX', multiplyNode + '.input1.input1X', force=True)

                    # divide scale or stretch
                    cmds.connectAttr(self.inputChain[-2] + '.translateX', multiplyNodeStretch + '.input1.input1X', f=True)

                    for idx in range(1, factor + 1):
                        cmds.connectAttr(multiplyNode + '.outputX', TD[idx] + '.rotateX', f=True)
                        cmds.connectAttr(multiplyNodeStretch + '.outputX', TD[idx] + '.translateX', f=True)

                elif itm == self.inputChain[-2]:

                    ref_lower_limb = cmds.createNode('transform', n='_'.join(TD[0].split('_')[:2]) + '_twist_lowerRef')
                    cmds.delete(cmds.parentConstraint(TD[-1], ref_lower_limb))
                    cmds.parent(ref_lower_limb, TD[0])

                    cmds.orientConstraint(self.inputChain[-1], ref_lower_limb, mo=True, skip=['y', 'z'])
                    cmds.connectAttr(ref_lower_limb + '.rotateX', multiplyNode + '.input1.input1X', force=True)

                    # divide scale or stretch
                    cmds.connectAttr(self.inputChain[-1] + '.translateX', multiplyNodeStretch + '.input1.input1X', f=True)

                    for idx in range(1, factor + 1):
                        cmds.connectAttr(multiplyNode + '.outputX', TD[idx] + '.rotateX', f=True)
                        cmds.connectAttr(multiplyNodeStretch + '.outputX', TD[idx] + '.translateX', f=True)


    ######################################################################################################

    def create_deformation_chain(self):
        return tools.create_deformation_joints_for_module(self.rig_group)

######################################################################################################
