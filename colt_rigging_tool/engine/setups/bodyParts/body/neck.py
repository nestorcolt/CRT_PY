import maya.cmds as cmds
import pymel.core as pm
from engine.setups.controls import control
from engine.utils import tools

reload(control)
reload(tools)

###################################################################################################
# GLOBALS:
END_SPINE = 'spine_end_jnt'

###################################################################################################


class NeckObject(object):
    """

        Description: spine must be 6 joint spine chain to work propertly

    """

    # create array for class instances in memory
    instances = []
    #

    def __init__(self, rigObject='', spineObject='', spineEnd='', name='spineClass', prefix='neck', scale=1.0, scaleIK=1.0, scaleFK=1.0, neckAngle=30):

        print(
            """

                Description: neck class to build flexy spine on Humanoid Character
                Neck must be 3 joint neck
                @param spineEnd: array with end spine joint

            """
        )

        #
        # add instance
        NeckObject.instances.append(self)

        self.name = name
        #
        # Get neck joints

        joints = [itm for itm in cmds.listRelatives(spineEnd, ad=True) if itm.startswith(prefix)]
        joints.reverse()
        # print(joints)
        posArray = [cmds.xform(jnt, q=True, ws=True, t=True) for jnt in joints]

        # create neck curve
        # here is where it's defined how many cvs will have the curve
        neck_curve = cmds.curve(n=prefix + '_curve', d=1, p=[posArray[0], posArray[1], posArray[2]], k=[0, 1, 2])
        cmds.rebuildCurve(neck_curve, d=1, keepRange=0, keepControlPoints=True)
        vertexCount = len(cmds.ls(neck_curve + '.cv[*]', fl=True))

        # controls vars to None for now
        self.IKcontrol = None
        self.FKcontrol = None

        # driven groups
        driven = []

        # create control IK
        for idx in range(vertexCount):
            dummy = cmds.group(name='test', em=True)
            cmds.xform(dummy, ws=True, t=posArray[idx])
            decomp_node = cmds.createNode('decomposeMatrix', name=prefix + '_vtx_%d_decompNode' % idx)
            mid_grp = cmds.group(n=prefix + '_%d_drivenGrp' % idx, em=True)
            cmds.xform(mid_grp, ws=True, t=posArray[idx])
            cmds.connectAttr(mid_grp + '.worldMatrix', decomp_node + '.inputMatrix', f=True)
            cmds.connectAttr(decomp_node + '.outputTranslate', neck_curve + '.controlPoints[%d]' % idx, f=True)

            driven.append(mid_grp)

            if idx == vertexCount - 1:
                self.IKcontrol = control.Control(prefix='head_IK', scale=scale * scaleIK, translateTo=dummy)
                cmds.parent(mid_grp, self.IKcontrol.control)

            cmds.delete(dummy)

        # create control FK
        dummy = cmds.group(name='test', em=True)
        cmds.xform(dummy, ws=True, t=posArray[1])
        cmds.rotate('%ddeg' % neckAngle, rotateX=True, absolute=True)
        self.FKcontrol = control.Control(prefix='neck' + '_FK', shape=1, scale=scale * scaleFK, translateTo=dummy, rotateTo=dummy)
        cmds.parent(driven[1], self.FKcontrol.control)
        cmds.delete(dummy)
        del(dummy)

        # parenting controls
        cmds.parent(self.IKcontrol.root, self.FKcontrol.control)

        if spineObject:
            cmds.parent(self.FKcontrol.root, spineObject.IKcontrolsArray[-1].control)
            cmds.parent(driven[0], spineObject.IKcontrolsArray[-1].control)

        # public members
        self.curve = neck_curve
        self.driven = driven

        # execute methods
        nodes = self.create_pointOnCurve()
        self.targets = nodes[0]
        self.upVectors = nodes[1]

        self.setTorsion()
        self.neckNoXform = self.closeStructure()

        # adjust pivots
        self.adjustControlPivot(self.IKcontrol.control, 0.75)
        self.adjustControlPivot(self.FKcontrol.control, 0.35)

        #

        if rigObject:
            cmds.parent(self.neckNoXform, rigObject.noXformBodybody_group)

        cmds.select(clear=True)

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
        cmds.parent(self.upVectors[0], self.driven[0])
        cmds.parent(self.upVectors[-1], self.IKcontrol.control)

        # create point constraints between upVectors
        cmds.pointConstraint([self.upVectors[0], self.upVectors[-1]], self.upVectors[1])

    ###################################################################################################
    def closeStructure(self):
        """

            Description: Organize the no xform objects inside no xform group
            @return : neck no Xform group

        """

        # print()
        neck_grp = cmds.group(n='neck_noXform_grp', em=True)
        objects = self.targets[:]
        objects.extend(self.upVectors)
        objects.append(self.curve)
        toDo = [itm for itm in objects if pm.ls(itm)[0].getParent() is None]
        # print(toDo)
        cmds.parent(toDo, neck_grp)
        cmds.hide(neck_grp)
        # print()

        return neck_grp

    ###################################################################################################
    def adjustControlPivot(self, obj, percent):
        """

            Description: adjust the control's pivot in a certain percent of the curve arclenght
            obj : control
            percent: percent float value of the curve lenght

        """
        curveShape = cmds.listRelatives(self.curve, s=True)[0]
        point = cmds.createNode('pointOnCurveInfo', n='adjustPivotInfoTemp')
        cmds.connectAttr(curveShape + '.worldSpace', point + '.inputCurve', f=True)

        cmds.setAttr(point + '.parameter', percent)
        pos = cmds.getAttr(point + '.position')[0]

        cmds.move(float(pos[0]), float(pos[1]), float(pos[2]), obj + ".scalePivot", obj + ".rotatePivot", absolute=True)

        cmds.delete(point)

        return True
###################################################################################################


if __name__ == '__main__':
    charNeck = NeckObject(spineEnd=END_SPINE, scaleIK=15, scaleFK=10)
