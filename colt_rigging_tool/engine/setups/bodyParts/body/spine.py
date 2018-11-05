import maya.cmds as cmds
import pymel.core as pm
from engine.setups.controls import control
from weakref import WeakSet
from engine.utils import tools
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


class SpineStretch(object):
    """

        Description: spine must be 6 joint spine chain to work propertly

    """

    # create array for class instances in memory
    instances = []
    #

    def __init__(self, rigObject='', joints=[], name='spineClass', prefix='spine', scale=1.0, scaleIK=1.0, scaleFK=1.0):

        print(
            """

                Description: Spine class to build flexy spine on Humanoid Character
                @param joints: array with first and last joint in hier
            """
        )

        #
        # add instance
        SpineStretch.instances.append(self)

        self.name = name
        #

        joinChain = getJointHier(joints[0], joints[1])
        posArray = [cmds.xform(jnt, q=True, ws=True, t=True) for jnt in joinChain]

        self.spineJoints = joinChain

        # create spine curve
        # here is where it's defined how many cvs will have the curve
        spine_curve = cmds.curve(n=prefix + '_curve', d=1, p=[posArray[0], posArray[1], posArray[2], posArray[3], posArray[4], posArray[5]], k=[0, 1, 2, 3, 4, 5])
        cmds.rebuildCurve(spine_curve, d=3, keepRange=0, keepControlPoints=True)
        vertexCount = len(cmds.ls(spine_curve + '.cv[*]', fl=True))
        IKcontrolsArray = []

        # create controls IK
        for idx in range(vertexCount):
            dummy = cmds.group(name='test', em=True)
            cmds.xform(dummy, ws=True, t=posArray[idx])
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

        # execute methods
        nodes = self.create_pointOnCurve()
        self.targets = nodes[0]
        self.upVectors = nodes[1]

        self.IKcontrolsArray = IKcontrolsArray
        self.FKcontrolsArray = FKcontrolsArray

        #
        self.setTorsion()
        self.spineNoXform = self.closeStructure()

        # fix Ik Orientation and size + parenting to rigObject in Scene

        for idx in range(2, 6):
            IKcontrolsArray[idx * -1].setAngle('z')
            cmds.move(15, IKcontrolsArray[idx * -1].control + ".cv[*]", moveZ=True, absolute=True)

        #

        factor = 1.2
        cmds.scale(scaleIK * factor, scaleIK * factor, scaleIK * factor, IKcontrolsArray[0].control + ".cv[*]", relative=True)
        cmds.scale(scaleIK * factor, scaleIK * factor, scaleIK * factor, IKcontrolsArray[-1].control + ".cv[*]", relative=True)

        if rigObject:

            self.COG_controlRoot = FKcontrolsArray[0].root
            self.COG_control = pm.ls(FKcontrolsArray[0].control, fl=True)[0]

            cmds.parent(self.COG_controlRoot, rigObject.global_control_obj.control)
            cmds.parent(self.spineNoXform, rigObject.noXformBodybody_group)

            cmds.select(FKcontrolsArray[0].control)
            tools.renameFamily('COG')

        cmds.select(clear=True)

    ###################################################################################################
    # build squatch and stretch
    #
    def buildSqandSt(self, spineJoints=[]):

        targets = spineJoints[1:-2]
        curve = self.curve
        value = cmds.arclen(curve)

        nodeCvInfo = cmds.createNode('curveInfo', name='spineStretchCurveInfoNode')
        nodeCvMD = cmds.createNode('multiplyDivide', name='spineStretchMultiplyDivideNode')
        nodePlsMns = cmds.createNode('plusMinusAverage', name='spineStretchplusMinusAverageNode')

        nodeNull = cmds.createNode('transform', name='spineStretchNullNode')
        # cmds.setAttr(nodeNull + '.hiddenInOutliner', 1)

        cmds.connectAttr(curve + '.worldSpace', nodeCvInfo + '.inputCurve', f=True)

        #
        cmds.setAttr(nodePlsMns + '.operation', 2)
        cmds.setAttr(nodePlsMns + '.input2D[0].input2Dx', 1)
        cmds.connectAttr(nodeCvMD + '.outputX', nodePlsMns + '.input2D[1].input2Dx', f=True)

        #
        cmds.setAttr(nodeCvMD + '.operation', 2)
        cmds.setAttr(nodeCvMD + '.input1X', value)
        cmds.connectAttr(nodeCvInfo + '.arcLength', nodeCvMD + '.input2X', f=True)

        # values = keyframes of nulll node
        nullVals = [1, 5, 10]
        nullKeys = [1, 5, 1]

        for idx, val in enumerate(nullVals):
            cmds.setKeyframe(nodeNull, v=nullKeys[idx] * -1, at='translateX', t=val)

        frameCaches = []

        for idx, jnt in enumerate(targets):
            mulDivSqSt = cmds.createNode('multiplyDivide', name='spineSqSt_' + jnt + '_scaleFactor')
            cmds.setAttr(mulDivSqSt + '.operation', 1)

            frameCache = cmds.createNode('frameCache', name='spineSqSt_' + jnt + '_frameCache')
            frameCaches.append(frameCache)

            # connections
            cmds.connectAttr(nodeNull + '.translateX', frameCache + '.stream', f=True)
            cmds.connectAttr(frameCache + '.varying', mulDivSqSt + '.input1X', f=True)
            cmds.connectAttr(nodePlsMns + '.output2D.output2Dx', mulDivSqSt + '.input2X', f=True)

            nodePlsMnsScaleMain = cmds.createNode('plusMinusAverage', name=jnt + 'spineStretchnodePlsMnsScaleMainNode')
            cmds.setAttr(nodePlsMnsScaleMain + '.operation', 1)
            cmds.setAttr(nodePlsMnsScaleMain + '.input2D[0].input2Dx', 1)
            cmds.connectAttr(mulDivSqSt + '.outputX', nodePlsMnsScaleMain + '.input2D[1].input2Dx', f=True)

            # connect joints
            cmds.connectAttr(nodePlsMnsScaleMain + '.output2D.output2Dx', jnt + '.scaleY', force=True)
            cmds.connectAttr(nodePlsMnsScaleMain + '.output2D.output2Dx', jnt + '.scaleZ', force=True)

        for index, i in enumerate(range(nullVals[0], nullVals[-1] + 1, len(targets) + 1)):
            if index == len(targets) - 1:
                i = i + 1

            cmds.setAttr(frameCaches[index] + '.varyTime', i)
            # print(i, 'timming')
            # print(index, 'index')
            # print(frameCaches[index])

        #
        self.spineAnimCurve = nodeNull

        return

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
                cmds.aimConstraint(self.targets[idx + 1], trg, worldUpType='object', worldUpObject=up, upVector=[0.0, 0.0, 1.0])

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

        # print()
        spine_grp = cmds.group(n='spine_noXform_grp', em=True)
        objects = self.targets[:]
        objects.extend(self.upVectors)
        objects.append(self.curve)
        toDo = [itm for itm in objects if pm.ls(itm)[0].getParent() is None]
        # print(toDo)
        cmds.parent(toDo, spine_grp)
        cmds.hide(spine_grp)
        # print()

        return spine_grp


###################################################################################################

if __name__ == '__main__':
    charSpine = SpineStretch
    charSpine(joints=[HIPS, SPINE_END], scaleIK=4, scaleFK=20)
