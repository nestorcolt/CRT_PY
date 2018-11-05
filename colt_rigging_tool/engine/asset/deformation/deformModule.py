import maya.cmds as cmds
import maya.mel as mel
from engine.asset.deformation import skinSaver
from engine.asset.weights import location
from engine.utils import tools
import os

reload(skinSaver)

###################################################################################################
# GLOBALS:
SW_EXT = '.swt'

###################################################################################################


def make_wrap(wrappedObjs, wrapper):
    cmds.select(wrappedObjs)
    cmds.select(wrapper, add=True)
    mel.eval('doWrapArgList "7" {"1","0","1","2","1","1","0","0"}')


def apply_deltaMush(geometry):
    delta_mush = cmds.deltaMush(geometry, smoothingIterations=50)


def get_model_geo_objects(model_group):
    geo_list = [cmds.listRelatives(obj, p=True)[0] for obj in cmds.listRelatives(model_group, ad=True, type='mesh')]
    return geo_list


###################################################################################################
# skin and weights managin
#

def save_skinWeights(geo_list=[]):
    """

        Description: save weights for character geometry objects

    """

    for obj in geo_list:
        # weights file
        weight_file = os.path.join(location.WEIGHTS_DIR, obj + SW_EXT)
        print('weights file stored in: %s' % weight_file)

        # save skin weights
        cmds.select(obj)
        skinSaver.bSaveSkinValues(weight_file)

###################################################################################################


def load_skinWeights(geo_list=[]):
    """

        Description: load skin weights for character geometry objects

    """

    # geo folders
    weight_dir = location.WEIGHTS_DIR
    print(weight_dir)
    files = os.listdir(weight_dir)

    # load skin weights

    for file in files:
        ext_res = os.path.splitext(file)

        # check for extension format
        if not ext_res > 1:
            continue

        # check skin weight file
        if not ext_res[1] == SW_EXT:
            continue

        # checl geometry list
        if geo_list and not ext_res[0] in geo_list:
            continue

        # check if object exist
        if not cmds.objExists(ext_res[0]):
            continue

        full_path_wg_file = os.path.join(weight_dir, file)
        skinSaver.bLoadSkinValues(loadOnSelection=False, inputFile=full_path_wg_file)

###################################################################################################
