import maya.cmds as mc
import maya.OpenMaya as om


######################################################################################################


def get_m_object(string_name):
    """
    :param string_name: Object name in string format
    :return: MObject
    """
    MObject = om.MObject()
    MSelList = om.MSelectionList()
    MSelList.add(string_name)
    MSelList.getDependNode(0, MObject)
    return MObject


def get_dag(stringName):
    """
    :param stringName: Object name in string format
    :return: MDag Object
    """
    MSelList = om.MSelectionList()
    MSelList.add(stringName)
    MDag = om.MDagPath()
    MSelList.getDagPath(0, MDag)
    return MDag

######################################################################################################
