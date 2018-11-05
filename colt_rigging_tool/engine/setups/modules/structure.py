###################################################################################################
import maya.cmds as cmds
import pymel.core as pm
from engine.setups.controls import control
from engine.utils import tools
reload(control)
reload(tools)
"""

    Description: This module will construct the rig base folder structure and will handle
    the basic folder structure for rig parts as well.

"""

###################################################################################################
# Globals:
GLOBAL_SCALE = 1.0
SCENE_OBJECT_TYPE = 'rig'

###################################################################################################


class Base():

    def __init__(self, characterName, scale=GLOBAL_SCALE, mesh='', parentJoint='', geoList=[], builder=''):
        # Sanity check
        print('__init__ from "Base" class to build rig folder structure')

        # create "folder structure"
        self.global_group = cmds.group(name=characterName + '_globalSystem_grp', em=True)
        self.components_group = cmds.group(name=characterName + '_components_grp', em=True)
        self.geometry_group = cmds.group(name=characterName + '_geometries_grp', em=True)
        self.rigging_group = cmds.group(name=characterName + '_rigging_grp', em=True)
        self.joints_group = cmds.group(name=characterName + '_joints_grp', em=True)
        self.noXform_group = cmds.group(name=characterName + '_noXform_grp', em=True)
        self.noXformHead_group = cmds.group(name=characterName + '_noXformHead_grp', em=True)
        self.noXformBodybody_group = cmds.group(name=characterName + '_noXformBody_grp', em=True)
        self.facialRig_group = cmds.group(name=characterName + '_facialRig_grp', em=True)
        self.bodyRig_group = cmds.group(name=characterName + '_bodyRig_grp', em=True)

        # parenting I
        cmds.parent(self.components_group, self.global_group)
        cmds.parent(self.geometry_group, self.rigging_group, self.joints_group, self.noXform_group, self.components_group)
        cmds.parent(self.noXformHead_group, self.noXformBodybody_group, self.noXform_group)
        cmds.parent(self.facialRig_group, self.bodyRig_group, self.rigging_group)

        # no xform group set attribute
        cmds.setAttr(self.noXform_group + '.it', False, lock=True)

        reorder = [self.geometry_group, self.joints_group, self.noXform_group, self.rigging_group]
        for grp in reorder:
            cmds.reorder(grp, back=True)

        char_name_attr = 'characterName'
        scene_objectType_attr = 'scene_objectType'

        for att in [char_name_attr, scene_objectType_attr]:
            cmds.addAttr(self.global_group, ln=att, dt='string')

        cmds.setAttr(self.global_group + '.' + char_name_attr, characterName, type='string', lock=True)
        cmds.setAttr(self.global_group + '.' + scene_objectType_attr, SCENE_OBJECT_TYPE, type='string', lock=True)

        # make controls
        global_control_obj = None

        if mesh and cmds.objExists(mesh):
            global_control_obj = control.Control(prefix=characterName + '_global', scale=tools.get_boundingBoxSize(mesh), translateTo=mesh, parent=self.bodyRig_group, lockChannels=['v'])
        else:
            global_control_obj = control.Control(prefix=characterName + '_global', scale=scale * 40, parent=self.bodyRig_group, lockChannels=['v'])

        # add global scale attribute
        cmds.addAttr(global_control_obj.control, ln='globalScale', at='float', k=True, defaultValue=1.0)
        for axis in 'xyz':
            cmds.connectAttr(global_control_obj.control + '.globalScale', global_control_obj.control + '.s%s' % axis)

        main_visibility_attr = ['modelVis', 'jointsVis']
        main_display_attr = ['modelDisplay', 'jointsDisplay']
        obj_to_add_attrs = [self.geometry_group, self.joints_group]

        # add rig visibility connections
        for at, obj in zip(main_visibility_attr, obj_to_add_attrs):
            cmds.addAttr(global_control_obj.control, ln=at, at='enum', enumName='off:on', k=True, defaultValue=True)
            cmds.setAttr(global_control_obj.control + '.' + at, cb=True)
            cmds.connectAttr(global_control_obj.control + '.' + at, obj + '.v')

        # add rig display connections
        for at, obj in zip(main_display_attr, obj_to_add_attrs):
            cmds.addAttr(global_control_obj.control, ln=at, at='enum', enumName='normal:template:reference', k=True)
            cmds.setAttr(global_control_obj.control + '.' + at, cb=True)
            cmds.setAttr(obj + '.ove', True)
            cmds.connectAttr(global_control_obj.control + '.' + at, obj + '.ovdt')

        global_control_obj.lockChannels = ['s']
        global_control_obj.lock_control_channels()

        cmds.addAttr(global_control_obj.control, shortName='cntRig', longName='ConnectRig', at='bool', defaultValue=1, k=True)
        cmds.setAttr(global_control_obj.control + '.ConnectRig', cb=True)

        if parentJoint:
            cmds.parent(parentJoint, self.joints_group)

        if geoList:
            cmds.parent(geoList, self.geometry_group)

        if builder:
            cmds.delete(builder)

        ############
        # Public members
        self.global_control_obj = global_control_obj


###################################################################################################



###################################################################################################
if __name__ == '__main__':
    run = Base
    build = tools.getBuilder()
    run('Mark', mesh='mark_body_geo', parentJoint=build['joint'], geoList=build['geos'], builder=build['builder'])
    cmds.select(clear=True)
