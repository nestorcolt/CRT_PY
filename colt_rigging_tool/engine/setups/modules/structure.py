###################################################################################################
import maya.cmds as cmds
import pymel.core as pm
from colt_rigging_tool.engine.setups.controls import control
from colt_rigging_tool.engine.utils import tools
reload(control)
reload(tools)
"""

    Description: This module will construct the rig base folder structure and will handle
    the basic folder structure for rig parts as well.

"""

###################################################################################################
# Globals:
GLOBAL_SCALE = 1.0

class Rig_structure():

    def __init__(self,
                 asset_name,
                 scale=GLOBAL_SCALE,
                 geometry_group='',
                 skin_geo=None):

        # Sanity check
        print('__init__ from "Base" class to build rig folder structure')

        self.skin = skin_geo

        if not skin_geo or skin_geo is None:
            cmds.error("Must pass main skin geometry name")
            return

        # create "folder structure"
        self.root_group = cmds.group(name=asset_name + '_rig_GRP', em=True)
        self.geometry_group = cmds.group(name= 'C_geometries_GRP', em=True)
        self.modules_group = cmds.group(name='C_modules_GRP', em=True)
        #
        self.body_rig_group = cmds.group(name='C_body_rig_GRP', em=True)
        self.body_skell_group = cmds.group(name='C_body_skell_GRP', em=True)
        #
        self.face_rig_group = cmds.group(name='C_face_rig_GRP', em=True)
        self.face_skell_group = cmds.group(name='C_face_skell_GRP', em=True)
        #
        self.face_geometries_group = cmds.createNode("transform", n="C_face_geo_GRP")
        self.rig_blend_group = cmds.createNode("transform", n="C_rigBlend_GRP")
        self.controls_group = cmds.createNode("transform", n="C_controls_GRP")

        cmds.parent(self.modules_group, self.root_group)
        cmds.parent(self.geometry_group, self.root_group)
        cmds.parent(self.face_rig_group, self.modules_group)
        cmds.parent(self.face_skell_group, self.modules_group)
        cmds.parent(self.body_rig_group, self.modules_group)
        cmds.parent(self.body_skell_group, self.modules_group)
        cmds.parent(self.rig_blend_group, self.root_group)
        cmds.parent(self.face_geometries_group, self.root_group)


        char_name_attr = 'assetName'

        for att in [char_name_attr]:
            cmds.addAttr(self.root_group, ln=att, dt='string')

        cmds.setAttr(self.root_group + '.' + char_name_attr, asset_name, type='string', lock=True)


        # geometry version
        cmds.addAttr(self.root_group, ln="rigVersion", dt='string', k=False)
        cmds.addAttr(self.root_group, ln="geometryVersion", dt='string', k=False)

        # connect messages
        cmds.addAttr(self.root_group, ln="skinGeo", at='message', k=False)
        if self.skin and cmds.objExists(self.skin):
            cmds.connectAttr("{}.message".format(self.skin), "{}.skinGeo".format(self.root_group), f=True)
            cmds.setAttr("{}.skinGeo".format(self.root_group), lock=True)

        # make controls
        self.main_control = None


        self.main_control = control.Control(prefix='C_main',
                                            scale=tools.get_boundingBoxSize(skin_geo) * 1.5,
                                            parent=self.root_group,
                                            lockChannels=['v'],
                                            color=13)

        self.walk_control = control.Control(prefix='C_anim_walk',
                                            scale=tools.get_boundingBoxSize(skin_geo) * 1.1,
                                            parent=self.main_control.control, lockChannels=['v'])




        # separator user defiine attrs
        cmds.addAttr(self.main_control.control, ln='UserDefineAttrs', at='enum', enumName='________:__', k=True)
        cmds.setAttr("{}.UserDefineAttrs".format(self.main_control.control), lock=True)

        # add global scale attribute
        cmds.addAttr(self.main_control.control, ln='globalScale', at='float', k=True, defaultValue=1.0, minValue=0.2)
        for axis in 'xyz':
            cmds.connectAttr(self.main_control.control + '.globalScale', self.main_control.control + '.s%s' % axis)

        main_visibility_attr = ['geoVisibility']
        main_display_attr = ['geoDisplayType']

        obj_to_add_attrs = [self.geometry_group]

        # add rig visibility connections
        for at, obj in zip(main_visibility_attr, obj_to_add_attrs):
            cmds.addAttr(self.main_control.control, ln=at, at='enum', enumName='off:on', k=True, defaultValue=True)
            cmds.setAttr(self.main_control.control + '.' + at, cb=True)
            cmds.connectAttr(self.main_control.control + '.' + at, obj + '.v')

        # add rig display connections
        for at, obj in zip(main_display_attr, obj_to_add_attrs):
            cmds.addAttr(self.main_control.control, ln=at, at='enum', enumName='normal:template:reference', k=True)
            cmds.setAttr(self.main_control.control + '.' + at, cb=True)
            cmds.setAttr(obj + '.ove', True)
            cmds.connectAttr(self.main_control.control + '.' + at, obj + '.ovdt')

        self.main_control.lockChannels = ['s']
        self.main_control.lock_control_channels()
        cmds.parent(self.controls_group, self.walk_control.control)

        # reorder main groups
        cmds.reorder(self.modules_group, front=True)
        cmds.reorder(self.main_control.root, front=True)
        cmds.reorder(self.geometry_group, front=True)

        if geometry_group and cmds.objExists(geometry_group):
            cmds.parent(geometry_group, self.geometry_group)

    ###################################################################################################

    def include_modules(self, body=True, module=None):
        if module is not None:
            directories = vars(module).keys()
            rig = [itm for itm in directories if itm.endswith("rig_group")]
            skell = [itm for itm in directories if itm.endswith("skell_group")]
            controls = [getattr(module, itm) for itm in directories if itm.endswith("controls_group")]
            print(module)
            print(rig)
            print(skell)
            print(controls)
            [cmds.parent(itm, self.controls_group) for itm in controls]

            if body:
               [cmds.parent(getattr(module, itm), self.body_rig_group) for itm in rig]
               [cmds.parent(getattr(module, itm), self.body_skell_group) for itm in skell]
            else:
                [cmds.parent(getattr(module, itm), self.face_rig_group) for itm in rig]
                [cmds.parent(getattr(module, itm), self.face_skell_group) for itm in skell]

###################################################################################################
if __name__ == '__main__':
    run = Rig_structure('Mark', geometry_group='geos')
    cmds.select(clear=True)
