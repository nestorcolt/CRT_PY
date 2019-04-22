import sys

import maya.cmds as mc
import pymel.core as pm
import maya.OpenMaya as om
import os
import shutil
import json

from engine.utils import tools
from engine.utils import controls_info
from engine.setups.modules import structure
from engine.setups.bodyParts.body import spine
from engine.setups.bodyParts.body import neck
from engine.setups.bodyParts.body import arms
from engine.setups.bodyParts.body import legs
from engine.setups.bodyParts.body import feet
from engine.asset.deformation import deformModule
from engine import builder

reload(tools)
reload(structure)
reload(spine)
reload(neck)
reload(arms)
reload(legs)
reload(feet)
reload(deformModule)
reload(builder)
reload(controls_info)



###################################################################################################
# GLOBALS:
CURRENT_RIG = None
ASSET = None
###################################################################################################
# GLOBALS
BUILDER_SCENE_PATH = r"C:\Users\colt-desk\Desktop\Salle\2019\Abril\II entrega\mech_project\data\builder\builder"
CONTROLS_DATA_PATH = r"C:\Users\colt-desk\Desktop\Salle\2019\Abril\II entrega\mech_project\data\builder\controls"
###################################################################################################
#
#

def initChar(asset_name=None, debug = 1):

    if asset_name is None:
        return

    character = asset_name


    # Open latest builder file
    latest_builder = tools.get_last_file_version(BUILDER_SCENE_PATH, "builder_000", incremental=False)
    builder_path = os.path.join(BUILDER_SCENE_PATH, latest_builder)

    if not os.path.exists(builder_path):
        mc.error("Builder path doesn't exist")
        return

    mc.file(new=True, f=True)
    mc.file(builder_path, i=True, f=True, mnc=True)
    mc.viewFit()

    # INFO
    geo = 'mech_geo'
    builder_elements = tools.getBuilder()

    # SPINE
    HIPS = 'hips_jnt'
    SPINE_END = 'spine_end_jnt'

    # ARMS
    # l_arm = 'l_upperarm_rig'
    # r_arm = 'r_upperarm_rig'

    # LEGS
    l_leg = 'l_upperleg_rig'
    r_leg = 'r_upperleg_rig'

    # call character builder object
    charObj = builder.BuildCharacterRig()
    charObj.populateProperties(geometry=geo, character=character, builder=builder_elements)

    # rig structure
    charObj.rigging = charObj.makeRig(charObj.character, charObj.geometry, charObj.builder)
    charObj.getSkeletons(structure=charObj.rigging)

    # # make spine
    charObj.buildSpine(charObj.rigging, HIPS, SPINE_END, neck=False)
    # charObj.spineSqandSt()
    #
    # # make arms:
    # charObj.l_arm = charObj.buildArm(l_arm, True, True, True)
    # charObj.r_arm = charObj.buildArm(r_arm, True, True, True)

    # make legs:
    charObj.l_leg = charObj.buildLeg(l_leg, ikSys=True, fkSys=True, twist=False, twistValue=5)
    charObj.r_leg = charObj.buildLeg(r_leg, ikSys=True, fkSys=True, twist=False, twistValue=5)

    # feet
    charObj.createFootGuideLocators(charObj.footDummies)
    charObj.buildFeet()

    # leg visibility
    charObj.makeLegVisSys()
    charObj.doClean()

    # connect rig to spine targes
    charObj.connectRigToSpine()

    # connect both joint systems
    charObj.connectDefJoints(charObj.defJoints, charObj.rigJoints)

    # # match twist sytems
    # charObj.matchTwistSystem()

    # Skin cluster
    # charObj.buildSkin(meshes=['mark_body_geo', 'l_eye_geo', 'r_eye_geo'])

    # hide show joints
    # charObj.jointsVisibility()

    # calibrate spine curve for squach and stretch
    # charObj.calibrateSpineStretch()

    # MANAGING WEIGHTS
    # charObj.manageWeights(geometries=['mark_body_geo', 'l_eye_geo', 'r_eye_geo'], save=False)

    # Load control shapes
    controls_shapes = controls_info.Export_controls_info()
    controls_shapes.do_this(path=CONTROLS_DATA_PATH, import_mode=True)


    # Hide controls
    to_hide = [u'spine_1_FK_ctrl', u'spine_2_IK_ctrl', u'spine_3_IK_ctrl', u'spine_1_IK_ctrl', u'spine_4_IK_ctrl']
    for ctrl in to_hide:
        node = pm.PyNode(ctrl)
        shapes = [itm.name() for itm in node.getShapes() if isinstance(itm, pm.nt.NurbsCurve)]
        for shape in shapes:
            mc.setAttr("{}.lodVisibility".format(shape), 0)

    # finish attributes
    mc.setAttr("{}.jointsVis".format("mech_global_ctrl"), debug)
    mc.setAttr("{}.jointsDisplay".format("mech_global_ctrl"), 2)
    mc.setAttr("{}.modelDisplay".format("mech_global_ctrl"), 2)

    # DONE!
    sys.stdout.write("\n {} builder operation successfully done \n".format(asset_name))
    mc.select(clear=True)

    return charObj

######################################################################################################
# INIT
ASSET = initChar(asset_name="mech", debug = 0)