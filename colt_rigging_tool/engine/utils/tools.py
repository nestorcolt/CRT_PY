"""

    Description: tools for rig and etc etc etc

"""
import os
import maya.OpenMaya as om
import maya.cmds as mc
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

    listed_joints = mc.listRelatives(top_joint, type='joint', ad=True)
    listed_joints.append(top_joint)
    listed_joints.reverse()

    complete_joints = listed_joints[:]
    no_ends = []
    chain = []

    if not with_end_joints:
        for jnt in complete_joints:
            if mc.listRelatives(jnt):
                no_ends.append(jnt)
            #
            elif not mc.listRelatives(jnt):
                continue

        return no_ends

    else:
        for jnt in complete_joints:
            chain.append(jnt)
            #
            if not mc.listRelatives(jnt):
                continue

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

    offset_grp = mc.group(n=prefix + '_OFFSET_GRP', em=True)
    object_parents = mc.listRelatives(object, p=True)

    if object_parents:
        mc.parent(offset_grp, object_parents[0])

    # match object transforms

    mc.delete(mc.parentConstraint(object, offset_grp))
    mc.delete(mc.scaleConstraint(object, offset_grp))


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
        mc.undoInfo(openChunk=True)
        try:
            ret = func(*args, **kwargs)
        finally:
            mc.undoInfo(closeChunk=True)
        return ret
    return wrapper


###################################################################################################
"""

    Description: Finds the first joint in hierachy
    @return : a list with parent joints

"""


def find_first_joint():
    lista = mc.ls(type='joint')
    parents = []

    for jnt in lista:
        parent = mc.listRelatives(jnt, p=True, ni=True)[0]
        if parent:
            if not mc.objectType(parent, isType='joint'):
                first_born = mc.listRelatives(parent, c=True, type='joint')[0]
                # print('\nFATHER OF ALL: %s' % first_born)
                parents.append(first_born)

    return parents

###################################################################################################


def convert_path(path):
    return '/'.join(path.split('\\'))

###################################################################################################


def create_groups(obj):

    matrix = mc.xform(obj, q=1, ws=1, m=1)
    group = mc.group(n=obj + "_OFFSET", em=1)
    root = mc.group(n=obj + '_ROOT')
    mc.xform(root, ws=1, m=matrix)
    mc.parent(obj, group)

    return [root, group]

###################################################################################################


def get_boundingBoxSize(geometry):
    box = mc.exactWorldBoundingBox(geometry)
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
    sel = mc.ls(sl=True)

    for obj in sel:
        nameCtrl = name + '_CTL'
        # print(nameCtrl)
        mc.rename(obj, nameCtrl)
        mc.pickWalk(direction='up')
        auto = mc.ls(sl=True)[0]
        nameAuto = name + '_OFFSET'
        # print(nameAuto)
        mc.rename(auto, nameAuto)
        mc.pickWalk(direction='up')
        root = mc.ls(sl=True)[0]
        nameRoot = name + '_ROOT'
        # print(nameRoot)
        mc.rename(root, nameRoot)

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
    mc.select(clear=True)
    #
    suffix = joint.split('_')[-1]
    axis = mc.joint(joint, q=True, rotationOrder=True)[0]
    VALUE = mc.getAttr(pm.PyNode(joint).getChildren(c=True)[0].name() + '.t%s' % axis)
    lenght = abs(VALUE)
    # print(lenght, VALUE)
    oper = getOper(VALUE)
    mtx = mc.xform(joint, q=True, ws=True, m=True)
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

        mc.xform(twists[0], ws=True, m=mtx)
        mc.select(clear=True)

        return twists

###################################################################################################


def overrideColor(chain, color='blue', single=False):
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

    if not single:
        for jnt in chain:
            # print(jnt)
            mc.setAttr(jnt + '.overrideEnabled', True)
            mc.setAttr(jnt + '.ovc', color)

    else:
        mc.setAttr(chain + '.overrideEnabled', True)
        mc.setAttr(chain + '.ovc', color)

    #
###################################################################################################


def swapJointOrient(joint):

    mc.makeIdentity(joint, translate=False, rotate=True, scale=True, pn=True, n=False, a=True)

    for ch in 'XYZ':
        jointOrient = mc.getAttr(joint + '.jointOrient%s' % ch)

        if float(jointOrient) == float(0):
            continue

        mc.setAttr(joint + '.r%s' % ch.lower(), jointOrient)
        mc.setAttr(joint + '.jointOrient%s' % ch, 0.0)

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

    pv_line_pos_1 = mc.xform(joint, q=True, t=True, ws=True)
    pv_line_pos_2 = mc.xform(poleVector.control, q=True, t=True, ws=True)

    poleVector_curve = mc.curve(n=name + '_pv_crv', degree=1, point=[pv_line_pos_1, pv_line_pos_2])

    mc.cluster(poleVector_curve + '.cv[0]', n=name + '_pv1_cls', weightedNode=[joint, joint], bindState=True)
    mc.cluster(poleVector_curve + '.cv[1]', n=name + '_pv2_cls', weightedNode=[poleVector.control, poleVector.control], bindState=True)

    mc.setAttr(poleVector_curve + '.template', True)
    mc.setAttr(poleVector_curve + '.it', False)

    return poleVector_curve

###################################################################################################


def hideShapesChannelBox(nodos, exception=[]):
    for itm in nodos:
        shapes = mc.listRelatives(itm, shapes=1)
        # print(shapes)
        for shape in shapes:
            if shape not in exception:
                try:
                    mc.setAttr("{}.isHistoricallyInteresting".format(shape), 0)
                except:
                    pass


###################################################################################################
# creates the system for controls visibility IK FK or both at the same time
#

def makeControlsVisSetup(name='visibility', prefix='limb', attrHolder=None, controlsIK=[], controlsFK=[]):
    # create nodes to set conditions:
    node_fk = mc.createNode('condition', name=prefix + name + '_conditionNode_FK')
    node_ik = mc.createNode('condition', name=prefix + name + '_conditionNode_IK')
    node_blendIKFK = mc.createNode('condition', name=prefix + name + '_conditionNode_IKFK_blend')
    node_blend_FK = mc.createNode('condition', name=prefix + name + '_conditionNode_FK_blend')

    # setup attributes in nodes previously created
    # node_fk
    mc.setAttr(node_fk + '.secondTerm', 1.00)
    mc.setAttr(node_fk + '.operation', 0)
    mc.setAttr(node_fk + '.colorIfTrueR', 1)
    mc.setAttr(node_fk + '.colorIfFalseR', 0)

    # node_ik
    mc.setAttr(node_ik + '.secondTerm', 0.00)
    mc.setAttr(node_ik + '.operation', 0)
    mc.setAttr(node_ik + '.colorIfTrueR', 1)
    mc.setAttr(node_ik + '.colorIfFalseR', 0)

    # node_blendIKFK
    mc.setAttr(node_blendIKFK + '.operation', 3)

    # node_blend_FK
    mc.setAttr(node_blend_FK + '.operation', 1)
    mc.setAttr(node_blend_FK + '.colorIfTrueR', 0)
    mc.setAttr(node_blend_FK + '.colorIfFalseR', 1)

    # add both controls vis attribute
    mc.addAttr(attrHolder, k=True, shortName='bothVis', longName='ShowBothSys', at='bool', defaultValue=1)

    # make connections
    mc.connectAttr(attrHolder + '.IK_0_FK_1', node_ik + '.firstTerm', force=True)
    mc.connectAttr(attrHolder + '.IK_0_FK_1', node_fk + '.firstTerm', force=True)
    #
    mc.connectAttr(node_ik + '.outColorR', node_blendIKFK + '.colorIfFalseR', force=True)
    mc.connectAttr(node_fk + '.outColorR', node_blendIKFK + '.colorIfTrueR', force=True)

    # connect inputs to blend condition node
    mc.connectAttr(attrHolder + '.IK_0_FK_1', node_blendIKFK + '.firstTerm', force=True)
    mc.connectAttr(attrHolder + '.ShowBothSys', node_blendIKFK + '.secondTerm', force=True)

    # connect inputs condition blend FK
    mc.connectAttr(node_blendIKFK + '.outColorR', node_blend_FK + '.secondTerm', force=True)
    mc.connectAttr(attrHolder + '.ShowBothSys', node_blend_FK + '.firstTerm', force=True)

    # connect blend node to Fk controls
    for ctrl in controlsFK:
        mc.connectAttr(node_blendIKFK + '.outColorR', ctrl + '.lodVisibility', force=True)
    # connect blend node to Fk controls
    for ctrl in controlsIK:
        mc.connectAttr(node_blend_FK + '.outColorR', ctrl + '.lodVisibility', force=True)


###################################################################################################


def get_last_file_version(path_to, file_name, incremental=False):
    """
    :param path_to: Path to check. OS path structure
    :param file_name: File name example to check
    :param incremental: Get incremental version from file name or not
    :return: Latest file name string format
    """
    if os.path.exists(path_to):
        raw_name = os.path.splitext(file_name)[0]
        listed_files = os.listdir(path_to)
        if not listed_files and not incremental:
            return False

        files = [os.path.splitext(itm)[0] for itm in listed_files if itm.startswith(raw_name[:-4])
                 and itm.endswith(".json") or itm.endswith(".mb") or itm.endswith(".ma")]

        if not files and not incremental:
            return False
        elif not files and incremental:
            return file_name

        else:
            files.sort(reverse=True,
                       key=lambda x: int(re.findall(r'\d+', os.path.splitext(os.path.split(x)[1])[0])[-1]))

            latest_file = files[0]
            extention = [os.path.splitext(itm)[-1] for itm in listed_files if latest_file == os.path.splitext(itm)[0]][0]

            if not incremental:
                return "{}{}".format(latest_file, extention)

            else:
                file_no_idx = latest_file[:-3]
                index = str(int(latest_file[-3:]) + 1).zfill(3)
                return "{}{}".format(file_no_idx + index, extention)


######################################################################################################

def create_deformation_joints_for_module(module=None):
    relative_joints = [itm for itm in mc.listRelatives(module, ad=True, type="joint")
                       if "FK" not in itm and  "IK" not in itm]

    skell_grp_name = module.replace("_rig_", "_skell_")
    skell_grp = mc.createNode("transform", n=skell_grp_name)
    #
    for jnt in relative_joints:
        new_name = jnt.replace("_JNT", "_DEF")
        mc.duplicate(jnt, n=new_name, po=True)
        mc.parent(new_name, skell_grp)
        #
        mc.parentConstraint(jnt, new_name)

    return skell_grp

######################################################################################################

def re_open_current_file():
    current_file = mc.file(q=True, sceneName=True)
    if os.path.exists(current_file):
        mc.file(new=True, force=True)
        mc.file(current_file, open=True)
        mc.viewFit()
    else:
        mc.file(new=True, force=True)


######################################################################################################
def get_pole_vec_pos(root_pos, mid_pos, end_pos, pv_distance=50):
    #
    pole_vec_pos = None

    root_vec = om.MVector(root_pos[0], root_pos[1], root_pos[2])
    mid_vec = om.MVector(mid_pos[0], mid_pos[1], mid_pos[2])
    end_vec = om.MVector(end_pos[0], end_pos[1], end_pos[2])

    line = (end_vec - root_vec)
    point = (mid_vec - root_vec)
    #
    scale_val = (line * point) / (line * line)
    projected_vector = line * scale_val + root_vec

    # next is for getting the length of the arm in case of use this as distance
    # root_to_mid_len = point.length()
    # mid_to_end_len = (end_vec - mid_vec).length()
    # total_length = root_to_mid_len + mid_to_end_len
    #
    pole_vec_pos = (mid_vec - projected_vector).normal() * pv_distance + mid_vec

    return pole_vec_pos

######################################################################################################

# BUILDER_SCENE_PATH = r"C:\Users\colt-desk\Desktop\biped_2019\biped\scenes"
if __name__ == '__main__':
    # print(list_joint_hier(top_joint="L_upperArm_JNT", with_end_joints=True))
    # print getSideLetter(mc.ls(sl=True)[0])
    # swapJointOrient('l_upperleg_rig')
    # makeTwistJoints('l_lowerleg_rig', 5)
    # print(copySkeleton('hips_jnt', 'rig'))
    # create_deformation_joints_for_module("L_hand_rig_GRP")
    # latest_builder = get_last_file_version(BUILDER_SCENE_PATH, "biped_000", incremental=False)
    # print(latest_builder)
    pass
