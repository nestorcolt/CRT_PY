import maya.cmds as cmds
import pymel.core as pm
from colt_rigging_tool.engine.setups.controls import control
from colt_rigging_tool.engine.utils import tools
from weakref import WeakSet
reload(control)
reload(tools)

###################################################################################################
# GLOBALS:

HIPS = 'hips_jnt'
SPINE_END = 'spine_end_jnt'

###################################################################################################


def getJointHier(startJoint, endJoint):
    chain = []
    cmds.select(clear=True)
    cmds.select(startJoint)

    while True:
        joint = cmds.ls(sl=True)[0]
        chain.append(joint)
        cmds.pickWalk(direction='down')
        if joint == endJoint:
            # chain.append(joint)
            cmds.select(clear=True)
            break

    return chain


######################################################################################################

class False_IKFK_spine(object):
    """

        Description: spine must be 6 joint spine chain to work propertly

    """

    # create array for class instances in memory
    instances = []
    #

    def __init__(self,
                 joints=[],
                 name='spineClass',
                 prefix='spine',
                 scale=1.0,
                 scaleIK=1.0,
                 scaleFK=1.0,
                 controls_parent=None,
                 module_parent=None):

        print(
            """

                Description: Spine class to build flexy spine on Humanoid Character
                @param joints: array with first and last joint in hier
            """
        )

        #
        # add instance
        False_IKFK_spine.instances.append(self)

        self.name = name
        #

        joinChain = getJointHier(joints[0], joints[1])
        posArray = [cmds.xform(jnt, q=True, ws=True, t=True) for jnt in joinChain]

        self.spineJoints = joinChain

        # create spine curve
        # here is where it's defined how many cvs will have the curve
        spine_curve = cmds.curve(n=prefix + '_curve', d=1, p=posArray, k=range(len(posArray)))
        cmds.rebuildCurve(spine_curve, d=3, keepRange=0, keepControlPoints=True)
        vertexCount = len(cmds.ls(spine_curve + '.cv[*]', fl=True))
        #
        IKcontrolsArray = []

        # create controls IK
        for idx in range(vertexCount):
            dummy = cmds.group(name='test', em=True)
            cmds.xform(dummy, ws=True, t=posArray[idx])

            if posArray[idx] == posArray[-1]:
                cmds.xform(dummy, ws=True, t=posArray[-2])

            controlName = tools.remove_suffix(str(joinChain[idx]))
            ctrl = control.Control(prefix=controlName + '_IK', scale=scale * scaleIK, translateTo=dummy)
            IKcontrolsArray.append(ctrl)
            decomp_node = cmds.createNode('decomposeMatrix', name=prefix + '_vtx_%d_decompNode' % idx)
            mid_grp = cmds.group(n=controlName + '_drivenGrp', em=True)
            cmds.xform(mid_grp, ws=True, t=posArray[idx])
            cmds.connectAttr(mid_grp + '.worldMatrix', decomp_node + '.inputMatrix', f=True)
            cmds.connectAttr(decomp_node + '.outputTranslate', spine_curve + '.controlPoints[%d]' % idx, f=True)
            cmds.parent(mid_grp, ctrl.control)
            cmds.delete(dummy)

        #
        FKcontrolsArray = []

        # create controls FK
        for idx in range(3):
            dummy = cmds.group(name='test', em=True)
            cmds.xform(dummy, ws=True, t=posArray[idx])
            controlName = tools.remove_suffix(str(joinChain[idx]))
            ctrl = control.Control(prefix=controlName + '_FK', shape=2, scale=scale * scaleFK, translateTo=dummy)
            FKcontrolsArray.append(ctrl)
            cmds.delete(dummy)

        # make parent logic
        #
        # parent IK

        cmds.parent(IKcontrolsArray[-2].root, IKcontrolsArray[-1].control)
        cmds.parent(IKcontrolsArray[1].root, IKcontrolsArray[0].control)
        cmds.parent(IKcontrolsArray[-3].root, IKcontrolsArray[-2].control)
        #
        # parent FK
        cmds.parent(IKcontrolsArray[-1].root, FKcontrolsArray[2].control)
        cmds.parent(IKcontrolsArray[2].root, FKcontrolsArray[1].control)
        cmds.parent(FKcontrolsArray[2].root, FKcontrolsArray[1].control)
        cmds.parent(FKcontrolsArray[1].root, FKcontrolsArray[0].control)
        cmds.parent(IKcontrolsArray[0].root, FKcontrolsArray[0].control)
        #
        # end of parenting

        # Public members
        self.curve = spine_curve
        self.COG_control = None
        self.spineAnimCurve = None
        self.skell_group = None
        self.rig_group= cmds.createNode("transform", n="C_spine_rig_GRP")
        self.controls_group = cmds.createNode("transform", n="C_spine_controls_GRP")

        # execute methods
        nodes = self.create_pointOnCurve()
        self.targets = nodes[0]
        self.upVectors = nodes[1]

        self.IKcontrolsArray = IKcontrolsArray
        self.FKcontrolsArray = FKcontrolsArray

        ######################################################################################################
        # call methods
        self.setTorsion()
        self.spineNoXform = self.closeStructure()

        # fix Ik Orientation and size + parenting to rigObject in Scene
        for idx in range(2, 6):
            IKcontrolsArray[idx * -1].setAngle('z')
            cmds.move(15, IKcontrolsArray[idx * -1].control + ".cv[*]", moveZ=True, absolute=True)

        cmds.move(1, IKcontrolsArray[-1].control + ".cv[*]", moveY=True, relative=True)

        #
        factor = 1.2
        cmds.scale(scaleIK * factor, scaleIK * factor, scaleIK * factor,
                   IKcontrolsArray[0].control + ".cv[*]", relative=True)
        cmds.scale(scaleIK * factor, scaleIK * factor, scaleIK * factor,
                   IKcontrolsArray[-1].control + ".cv[*]", relative=True)

        # make controls group

        cmds.parent(FKcontrolsArray[0].root, self.controls_group)
        cmds.select(FKcontrolsArray[0].control)
        tools.renameFamily('C_COG')
        cmds.select(clear=True)

    ######################################################################################################

    def include_spine_joints(self):
        for jnt, drv in zip(self.spineJoints, self.targets):
            cmds.parentConstraint(drv, jnt, mo=True)

    ###################################################################################################

    def create_pointOnCurve(self):
        """
            Description: create the logic for the node pointOnCurveInfo
            @ return : a nested array with target groups and them upvectors

        """
        # print()
        curve = self.curve
        # number of CVs = degree + spans.
        degs = cmds.getAttr(curve + '.degree')
        spans = cmds.getAttr(curve + '.spans')
        cv_lenght = degs + spans
        data = []
        targets = []
        upVectors = []
        to_return = []

        for idx in range(cv_lenght):
            trans = cmds.xform(curve + '.cv[%d]' % idx, q=True, ws=True, t=True)
            loc = cmds.group(n=curve + '_%d_target' % idx, em=True)
            upVec = cmds.group(n=curve + '_%d_UpVect' % idx, em=True)
            cmds.xform(loc, ws=True, t=trans)
            cmds.xform(upVec, ws=True, t=trans)
            cmds.setAttr(upVec + '.tz', -35)
            pos = [float(num) for num in trans]
            data.append([idx, loc, pos])
            targets.append(loc)
            upVectors.append(upVec)

        # print (data)

        curveShape = cmds.listRelatives(curve, s=True)[0]

        for idx, itm in enumerate(data):
            pos = itm[2]
            point = cmds.createNode('pointOnCurveInfo', n=curve + '_pointOncurve_%d' % idx)
            cmds.connectAttr(curveShape + '.worldSpace', point + '.inputCurve', f=True)
            cmds.connectAttr(point + '.position', itm[1] + '.translate', f=True)
            value = 0.001

            for num in range(999):
                YglobalPos = pos[1]
                YpointPos = cmds.getAttr(point + '.position')[0][1]
                # print YpointPos

                if YpointPos >= YglobalPos:
                    # print('Global: %d  - Point: %d' % (YglobalPos, YpointPos))
                    break

                else:
                    cmds.setAttr(point + '.parameter', value)
                    value += 0.001

        return [targets, upVectors]

    ################################################################################################

    def setTorsion(self):

        count = len(self.targets)
        # print()
        for idx, (trg, up) in enumerate(zip(self.targets, self.upVectors)):
            # cmds.setAttr(trg + '.displayLocalAxis', True)
            # cmds.setAttr(up + '.displayLocalAxis', True)

            # set aim constraint
            if idx != (count - 1):
                # print(trg, self.targets[idx + 1], up)
                cmds.aimConstraint(self.targets[idx + 1], trg, worldUpType='object', worldUpObject=up,
                                   upVector=[0.0, 0.0, 1.0])

        # parenting upvectors procedure: first and last
        cmds.parent(self.upVectors[0], self.IKcontrolsArray[0].control)
        cmds.parent(self.upVectors[-1], self.IKcontrolsArray[-1].control)

        # create point constraints between upVectors
        cmds.pointConstraint([self.upVectors[0], self.upVectors[-1]], self.upVectors[2])
        cmds.pointConstraint([self.upVectors[0], self.upVectors[2]], self.upVectors[1])
        cmds.pointConstraint([self.upVectors[2], self.upVectors[4]], self.upVectors[3])
        cmds.pointConstraint([self.upVectors[2], self.upVectors[-1]], self.upVectors[4])

    ###################################################################################################

    def closeStructure(self):
        """

            Description: Organize the no xform objects inside no xform group
            @return : spine no Xform group

        """

        spine_grp= self.rig_group
        self.include_spine_joints()
        #
        objects = self.targets[:]
        objects.extend(self.upVectors)
        objects.append(self.curve)
        toDo = [itm for itm in objects if pm.ls(itm)[0].getParent() is None]
        cmds.parent(toDo, spine_grp)
        cmds.parent(self.spineJoints[0], spine_grp)
        self.skell_group = self.create_deformation_chain()
        cmds.hide(self.skell_group)
        cmds.hide(spine_grp)

        return spine_grp

    ######################################################################################################

    def create_deformation_chain(self):
        return tools.create_deformation_joints_for_module(self.rig_group)

###################################################################################################

if __name__ == '__main__':
    charSpine = False_IKFK_spine(joints=["joint1_JNT", "joint6_JNT"], scaleIK=4, scaleFK=20)
