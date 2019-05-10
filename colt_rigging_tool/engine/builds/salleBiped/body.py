import sys
import maya.cmds as mc
import pymel.core as pm
import maya.OpenMaya as om
import os
import shutil
import json
#
from colt_rigging_tool.engine.utils import tools, controls_info
from colt_rigging_tool.engine.setups.modules import structure
from colt_rigging_tool.engine.setups.bodyParts.body import spine, neck, arms, legs, feet
from colt_rigging_tool.engine.asset.deformation import deformModule
#
reload(tools)
reload(structure)
reload(spine)
reload(neck)
reload(arms)
reload(legs)
reload(feet)
reload(deformModule)
reload(controls_info)


###################################################################################################
# GLOBALS:
CURRENT_RIG = None
ASSET = None
###################################################################################################
# GLOBALS
BUILDER_SCENE_PATH = r"C:\Users\colt-desk\Desktop\biped_2019\biped\scenes"
# CONTROLS_DATA_PATH = r"C:\Users\colt-desk\Desktop\Salle\2019\Abril\II entrega\mech_project\data\builder\controls"
###################################################################################################
#
#

def initChar(asset_name=None, debug = 1):

    if asset_name is None:
        return

    character = asset_name

    # Open latest builder file
    latest_builder = tools.get_last_file_version(BUILDER_SCENE_PATH, "biped_000", incremental=False)
    print(latest_builder)
    builder_path = os.path.join(BUILDER_SCENE_PATH, latest_builder)

    if not os.path.exists(builder_path):
        mc.error("Builder path doesn't exist")
        return

    mc.file(new=True, f=True)
    mc.file(builder_path, open=True, f=True)
    mc.viewFit()

    # INFO

    # build rig

    for side in "R":
        upperArm_joint = "{}_upperArm_JNT".format(side)
        hand_joint = "{}_hand_JNT".format(side)
        #
        arm = arms.Arm(armJoint=upperArm_joint, scaleFK=8)
        arm.build(hand_join=hand_joint)
        #
        #
        # upperLeg_joint = "{}_upperLeg_JNT".format(side)
        # leg = legs.Leg(legJoint=upperLeg_joint, scaleFK=8)
        # leg.build()



    #
    # DONE!
    sys.stdout.write("\n {} builder operation successfully done \n".format(asset_name))
    mc.select(clear=True)



######################################################################################################
# INIT
ASSET = initChar(asset_name="biped", debug = 1)
