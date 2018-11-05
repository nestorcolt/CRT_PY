"""

    Description: tools for rig and etc etc etc

"""
import maya.cmds as cmds
import pymel.core as pm
import re
###################################################################################################


def list_joint_hier(top_joint, with_end_joints=True):
    """

                    Description: parameter from function
                    @param top_joint: , str, joint to get listed with joint hierarchy
                    @param with_end_joints: bool, list the hierarchy included end joints
                    @return list(str): listed joints starting with top joint

    """

    listed_joints = cmds.listRelatives(top_joint, type='joint', ad=True)
    listed_joints.append(top_joint)
    listed_joints.reverse()

    complete_joints = listed_joints[:]
    no_ends = []
    chain = []

    if not with_end_joints:
        for jnt in complete_joints:
            if not '_end_' in jnt[:]:
                no_ends.append(jnt)
            elif '_end_' in jnt[:]:
                break
        return no_ends

    else:
        for jnt in complete_joints:
            chain.append(jnt)
            if '_end_' in jnt[:]:
                break
        return chain


###################################################################################################
"""

    Description: to remove the suffix from a name

"""


def remove_suffix(string):

    process = string.split('_')

    if len(process) < 2:
        return string

    suffix = '_' + process[-1]
    name_no_suffix = string[:-len(suffix)]

    return name_no_suffix

###################################################################################################


def make_offset_grp(object, prefix=''):
    """

            Description: make offset group for given object

    """

    if not prefix:
        prefix = remove_suffix(object)

    offset_grp = cmds.group(n=prefix + '_offset_grp', em=True)
    object_parents = cmds.listRelatives(object, p=True)

    if object_parents:
        cmds.parent(offset_grp, object_parents[0])

    # match object transforms

    cmds.delete(cmds.parentConstraint(object, offset_grp))
    cmds.delete(cmds.scaleConstraint(object, offset_grp))


###################################################################################################
"""

    Description: undo functions

"""


def undo_pm(func):
    def wrapper(*args, **kwargs):
        pm.undoInfo(openChunk=True)
        try:
            ret = func(*args, **kwargs)
        finally:
            pm.undoInfo(closeChunk=True)
        return ret
    return wrapper


def undo_cmds(func):
    def wrapper(*args, **kwargs):
        cmds.undoInfo(openChunk=True)
        try:
            ret = func(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)
        return ret
    return wrapper


###################################################################################################
"""

    Description: Finds the first joint in hierachy
    @return : a list with parent joints

"""


def find_first_joint():
    lista = cmds.ls(type='joint')
    parents = []

    for jnt in lista:
        parent = cmds.listRelatives(jnt, p=True, ni=True)[0]
        if parent:
            if not cmds.objectType(parent, isType='joint'):
                first_born = cmds.listRelatives(parent, c=True, type='joint')[0]
                # print('\nFATHER OF ALL: %s' % first_born)
                parents.append(first_born)

    return parents

###################################################################################################


def convert_path(path):
    return '/'.join(path.split('\\'))

###################################################################################################


def create_groups(obj):

    matrix = cmds.xform(obj, q=1, ws=1, m=1)
    group = cmds.group(n=obj + "_Auto", em=1)
    root = cmds.group(n=obj + '_Root')
    cmds.xform(root, ws=1, m=matrix)
    cmds.parent(obj, group)

    return [root, group]

###################################################################################################


def get_boundingBoxSize(geometry):
    box = cmds.exactWorldBoundingBox(geometry)
    box.pop(1)
    box.pop(3)
    radius = max(box)

    # print('Max Radius: {0:.3g}'.format(radius))
    return radius

###################################################################################################


def getBuilder():
    builder = [itm for itm in pm.ls(assemblies=True) if not itm.getShapes() and itm.getChildren()]
    if builder:
        joint = [jnt for jnt in builder[0].getChildren() if pm.objectType(jnt, isType='joint')]
        geos = [geo for geo in builder[0].getChildren() if geo.getShape()]
        # print('builderGroup: {}\njoins: {}\ngeos: {}'.format(builder, joint, geos))

        if builder and joint and geos:
            return {'builder': builder[0].name(), 'joint': joint[0].name(), 'geos': [itm.name() for itm in geos]}

    if not builder or builder is None:
        return False

###################################################################################################
# Rename Family


def renameFamily(name=''):
    sel = cmds.ls(sl=True)

    for obj in sel:
        nameCtrl = name + '_ctrl'
        # print(nameCtrl)
        cmds.rename(obj, nameCtrl)
        cmds.pickWalk(direction='up')
        auto = cmds.ls(sl=True)[0]
        nameAuto = name + '_Auto'
        # print(nameAuto)
        cmds.rename(auto, nameAuto)
        cmds.pickWalk(direction='up')
        root = cmds.ls(sl=True)[0]
        nameRoot = name + '_Root'
        # print(nameRoot)
        cmds.rename(root, nameRoot)

###################################################################################################


def copySkeleton(joint, suffix):
    """

        Description: Copy selected jnt chain
        return parent joint

    """
    newBorn = pm.duplicate(joint)
    pm.parent(newBorn[0], world=True)
    pm.select(newBorn[0])
    pm.select(hi=True)
    sel = pm.ls(sl=True, absoluteName=True)
    parent = None

    for idx, jnt in enumerate(sel):
        node = pm.PyNode(jnt)
        rawName = '_'.join(node.name().split('|')[-1].split('_')[:-1])
        newName = rawName + '_' + suffix
        par = pm.rename(node, newName)

        if idx == 0:
            parent = par

    return parent

###################################################################################################


def getOper(num):
    if num >= 0:
        return '+'
    else:
        return '-'

###################################################################################################


def makeTwistJoints(joint, number=0):
    """

        Description: Make twist joints
        @param joint: parent joint (str)
        @param numbver: numer ot jnt to create
        @return : twist joints array

    """
    # clear any selection first
    cmds.select(clear=True)
    #
    suffix = joint.split('_')[-1]
    axis = cmds.joint(joint, q=True, rotationOrder=True)[0]
    VALUE = cmds.getAttr(pm.PyNode(joint).getChildren(c=True)[0].name() + '.t%s' % axis)
    lenght = abs(VALUE)
    # print(lenght, VALUE)
    oper = getOper(VALUE)
    mtx = cmds.xform(joint, q=True, ws=True, m=True)
    name = remove_suffix(joint) + '_twist_%d_%s'
    twists = []

    if number and joint:
        value = lenght / (number - 1)
        # print(value)
        for idx in range(number):
            jnt = pm.joint(n=name % (idx, suffix), rotationOrder='xyz')
            twists.append(jnt.name())

            if idx > 0:
                formatedValue = ('{}{}'.format(oper, value))
                # print(formatedValue)
                jnt.translateX.set(float(formatedValue))

        cmds.xform(twists[0], ws=True, m=mtx)
        cmds.select(clear=True)

        return twists

###################################################################################################


def overrideColor(chain, color='blue'):
    """

        Description: overide color from joint chain
        colors:
        blue, red, green, yellow

    """

    if color == 'blue':
        color = 5
    elif color == 'red':
        color = 13
    elif color == 'green':
        color = 14
    elif color == 'yellow':
        color = 17

    for jnt in chain:
        # print(jnt)
        cmds.setAttr(jnt + '.overrideEnabled', True)
        cmds.setAttr(jnt + '.ovc', color)

    #
###################################################################################################


def swapJointOrient(joint):

    cmds.makeIdentity(joint, translate=False, rotate=True, scale=True, pn=True, n=False, a=True)

    for ch in 'XYZ':
        jointOrient = cmds.getAttr(joint + '.jointOrient%s' % ch)

        if float(jointOrient) == float(0):
            continue

        cmds.setAttr(joint + '.r%s' % ch.lower(), jointOrient)
        cmds.setAttr(joint + '.jointOrient%s' % ch, 0.0)

    return joint

###################################################################################################


def getSideLetter(name):

    if not name:
        return

    dummy = name.split('_')[0]
    if len(dummy) == 1 and dummy.isalpha():
        return dummy

    else:
        if '_r_' in name[:]:
            where = name.find('_r_')
            return name[where + 1]

        elif'_l_' in name[:]:
            where = name.find('_l_')
            return name[where + 1]

###################################################################################################


def makePoleVectorLine(name, joint, poleVector):
    """

        Description: make visual line to connect pv and limb
        name: prefix to name
        joint: limb to attach
        poleVector: pv to attach, (instance of object)
        return value: polevector curve to parent to X group

    """

    pv_line_pos_1 = cmds.xform(joint, q=True, t=True, ws=True)
    pv_line_pos_2 = cmds.xform(poleVector.control, q=True, t=True, ws=True)

    poleVector_curve = cmds.curve(n=name + '_pv_crv', degree=1, point=[pv_line_pos_1, pv_line_pos_2])

    cmds.cluster(poleVector_curve + '.cv[0]', n=name + '_pv1_cls', weightedNode=[joint, joint], bindState=True)
    cmds.cluster(poleVector_curve + '.cv[1]', n=name + '_pv2_cls', weightedNode=[poleVector.control, poleVector.control], bindState=True)

    cmds.setAttr(poleVector_curve + '.template', True)
    cmds.setAttr(poleVector_curve + '.it', False)

    return poleVector_curve

###################################################################################################


def hideShapesChannelBox(nodos, exception=[]):
    for itm in nodos:
        shapes = cmds.listRelatives(itm, shapes=1)
        # print(shapes)
        for shape in shapes:
            if shape not in exception:
                try:
                    cmds.setAttr("{}.isHistoricallyInteresting".format(shape), 0)
                except:
                    pass


###################################################################################################
# creates the system for controls visibility IK FK or both at the same time
#

def makeControlsVisSetup(name='visibility', prefix='limb', attrHolder=None, controlsIK=[], controlsFK=[]):
    # create nodes to set conditions:
    node_fk = cmds.createNode('condition', name=prefix + name + '_conditionNode_FK')
    node_ik = cmds.createNode('condition', name=prefix + name + '_conditionNode_IK')
    node_blendIKFK = cmds.createNode('condition', name=prefix + name + '_conditionNode_IKFK_blend')
    node_blend_FK = cmds.createNode('condition', name=prefix + name + '_conditionNode_FK_blend')

    # setup attributes in nodes previously created
    # node_fk
    cmds.setAttr(node_fk + '.secondTerm', 1.00)
    cmds.setAttr(node_fk + '.operation', 0)
    cmds.setAttr(node_fk + '.colorIfTrueR', 1)
    cmds.setAttr(node_fk + '.colorIfFalseR', 0)

    # node_ik
    cmds.setAttr(node_ik + '.secondTerm', 0.00)
    cmds.setAttr(node_ik + '.operation', 0)
    cmds.setAttr(node_ik + '.colorIfTrueR', 1)
    cmds.setAttr(node_ik + '.colorIfFalseR', 0)

    # node_blendIKFK
    cmds.setAttr(node_blendIKFK + '.operation', 3)

    # node_blend_FK
    cmds.setAttr(node_blend_FK + '.operation', 1)
    cmds.setAttr(node_blend_FK + '.colorIfTrueR', 0)
    cmds.setAttr(node_blend_FK + '.colorIfFalseR', 1)

    # add both controls vis attribute
    cmds.addAttr(attrHolder, k=True, shortName='bothVis', longName='ShowBothSys', at='bool', defaultValue=1)

    # make connections
    cmds.connectAttr(attrHolder + '.IK_0_FK_1', node_ik + '.firstTerm', force=True)
    cmds.connectAttr(attrHolder + '.IK_0_FK_1', node_fk + '.firstTerm', force=True)
    #
    cmds.connectAttr(node_ik + '.outColorR', node_blendIKFK + '.colorIfFalseR', force=True)
    cmds.connectAttr(node_fk + '.outColorR', node_blendIKFK + '.colorIfTrueR', force=True)

    # connect inputs to blend condition node
    cmds.connectAttr(attrHolder + '.IK_0_FK_1', node_blendIKFK + '.firstTerm', force=True)
    cmds.connectAttr(attrHolder + '.ShowBothSys', node_blendIKFK + '.secondTerm', force=True)

    # connect inputs condition blend FK
    cmds.connectAttr(node_blendIKFK + '.outColorR', node_blend_FK + '.secondTerm', force=True)
    cmds.connectAttr(attrHolder + '.ShowBothSys', node_blend_FK + '.firstTerm', force=True)

    # connect blend node to Fk controls
    for ctrl in controlsFK:
        cmds.connectAttr(node_blendIKFK + '.outColorR', ctrl + '.lodVisibility', force=True)
    # connect blend node to Fk controls
    for ctrl in controlsIK:
        cmds.connectAttr(node_blend_FK + '.outColorR', ctrl + '.lodVisibility', force=True)


###################################################################################################

if __name__ == '__main__':
    # print getSideLetter(cmds.ls(sl=True)[0])
    # swapJointOrient('l_upperleg_rig')
    # makeTwistJoints('l_lowerleg_rig', 5)
    print(copySkeleton('hips_jnt', 'rig'))
    pass
