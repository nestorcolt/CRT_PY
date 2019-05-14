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
from colt_rigging_tool.engine.setups.bodyParts.body import arms, legs, feet, spine
from colt_rigging_tool.engine.asset.deformation import deformModule
#
reload(tools)
reload(structure)
reload(arms)
reload(legs)
reload(feet)
reload(deformModule)
reload(controls_info)
reload(spine)

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

    # Open latest builder file
    latest_builder = tools.get_last_file_version(BUILDER_SCENE_PATH, "biped_000", incremental=False)
    builder_path = os.path.join(BUILDER_SCENE_PATH, latest_builder)

    if not os.path.exists(builder_path):
        mc.error("Builder path doesn't exist")
        return

    mc.file(new=True, f=True)
    mc.file(builder_path, open=True, f=True)
    mc.viewFit()

    #
    body_modules = []

    # INFO ######################################################################
    rig = structure.Rig_structure(asset_name='kaki',
                                  geometry_group='geometries_grp',
                                  skin_geo="C_body_geo")


    # build rig #################################################################

    ############
    # Build spine
    charSpine = spine.False_IKFK_spine(joints=["C_hip_JNT", "C_spine_05_JNT"], scaleIK=4, scaleFK=20)
    body_modules.append(charSpine)

    ###########
    #  Build limbs

    for idx, side in enumerate("LR"):
        # ARMS
        clavicle_joint = "{}_clavicle_JNT".format(side)
        hand_joint = "{}_hand_JNT".format(side)
        arm = arms.Arm(armJoint=clavicle_joint, scaleFK=8)
        arm.build(hand_join=hand_joint)
        #

        # LEGS
        upperLeg_joint = "{}_upperLeg_JNT".format(side)
        leg = legs.Leg(legJoint=upperLeg_joint, scaleFK=8)
        leg.build()

        # FEET
        hook = "{}_legEnd_JNT".format(side)
        foot = feet.Feet(foot_joint="{}_foot_01_JNT".format(side),
                         hook=hook,
                         hook_fk=hook,
                         hook_ik=hook,
                         attribute_holder="{}_leg_UI_CTL".format(side))

        foot.build()
        #
        if idx == 0:
            foot.flipAndDuplicate(foot.dummyNames)

        else:
            foot.cleanFeet()

        body_modules.append(arm)
        body_modules.append(leg)
        body_modules.append(foot)


    # merge body to rig system
    for module in body_modules:
        rig.include_modules(module=module)

    #
    # DONE!
    sys.stdout.write("\n {} builder operation successfully done \n".format(asset_name))
    mc.select(clear=True)


######################################################################################################

######################################################################################################
# INIT
initChar(asset_name="biped", debug = 1)
