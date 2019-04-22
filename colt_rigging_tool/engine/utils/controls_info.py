import collections
import json
import os

from engine.utils import tools
from engine.utils import api_functions
import maya.OpenMaya as om
import maya.cmds as mc
import pymel.core as pm

######################################################################################################

######################################################################################################


class Export_controls_info(object):

    def __init__(self):
        self.file_name = "controls_data_000.json"

    ######################################################################################################

    def get_scene_controls(self):
        controls = mc.ls("*_ctrl")
        return  controls

    ######################################################################################################

    def do_this(self, import_mode=False, path=""):

        if os.path.exists(path):

            if not import_mode:
                self.export_controls(path)
                print("Controls successfully exported")

            else:
                self.import_controls(path)
                print("Controls successfully imported")

    ######################################################################################################

    # Export
    def export_controls(self, path=""):
        controls = self.get_scene_controls()
        controls_data = {}

        for ctrl in controls:
            node = pm.PyNode(ctrl)
            shapes = [itm.name() for itm in node.getShapes() if isinstance(itm, pm.nt.NurbsCurve)]
            shape_data = collections.defaultdict(dict)
            for shape in shapes:
                position = self.get_cv_points(shape)
                color_index = mc.getAttr("{}.ovc".format(shape))
                shape_data[shape]["position"] = position
                shape_data[shape]["color"] = color_index

            #
            controls_data[ctrl] = shape_data

        # save to json
        self.export_data(path=path, input_data=controls_data)


    # Import
    def import_controls(self, path):
        controls_data = self.import_data(path)

        for shape_name in controls_data:
            inner_dict = controls_data[shape_name]
            for shape in inner_dict.keys():
                shape_dict = inner_dict[shape]
                color = shape_dict.get("color", 0)
                mc.setAttr("{}.ove".format(shape), 1)
                mc.setAttr("{}.ovc".format(shape), color)
                #
                pos_dict = shape_dict["position"]
                self.set_cv_points(shape, pos_dict)

    ######################################################################################################

    def get_cv_points(self, shape):
        m_shape = api_functions.get_m_object(shape)
        curve_iter = om.MItCurveCV(m_shape)
        counter = 0
        position_dict = {}

        while not curve_iter.isDone():
            pos = curve_iter.position(om.MSpace.kObject)
            position_dict[counter] = [pos.x, pos.y, pos.z, pos.w]
            counter += 1
            curve_iter.next()

        return position_dict

    def set_cv_points(self, shape, dictionary):
        m_shape = api_functions.get_m_object(shape)
        curve_iter = om.MItCurveCV(m_shape)
        counter = 0

        while not curve_iter.isDone():
            pos = dictionary[str(counter)]
            point = om.MPoint(pos[0],pos[1],pos[2],pos[-1])
            curve_iter.setPosition(point, om.MSpace.kObject)
            counter += 1
            curve_iter.next()

    ######################################################################################################

    def export_data(self, path="", input_data=None):
        """
        Export to json the weights data
        :param path: OS format - Path to export weights
        """
        file_path = os.path.join(path, tools.get_last_file_version(path, self.file_name, incremental=True))
        json_data = json.dumps(input_data, ensure_ascii=True, indent=4,separators=[",",":"], sort_keys=True)
        #
        with open(file_path, "w") as saving:
            saving.write(json_data)
            saving.close()

    def import_data(self, path=""):
        """
        Import from json the weights data
        :param path: OS format - Path to import weights
        :return: json data converted in python dictionary
        """
        file_name = tools.get_last_file_version(path, self.file_name)

        if not file_name:
            om.MGlobal.displayWarning("No file to import")
            return False

        file_path = os.path.join(path, file_name)
        #
        with open(file_path, "r") as loading:
            data = dict(json.load(loading))
            loading.close()

        return data

######################################################################################################

######################################################################################################
PATH = r"C:\Users\colt-desk\Desktop\Salle\2019\Abril\II entrega\mech_project\data\builder\controls"

if __name__ == '__main__':
    instance = Export_controls_info()
    instance.do_this(path=PATH, import_mode=True)