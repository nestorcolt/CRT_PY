"""

    Description: Module for making the Rig controls.

"""

import maya.cmds as cmds
from colt_rigging_tool.engine.utils import tools

##################################################################################################


class Control(object):
    """

        @param prefix, str, prefix to name new control object
        @param scale, float, scale for size of control shapes
        @param translateTo, str, reference object for position
        @param rotateTo, str, reference object for rotation
        @param parent, str, object to be parent of new control
        @param lockChannels, list(str), list with channels of control to be locked or non-keable
        @param angle: normal orientation

    """

    def __init__(
            self,
            prefix='new',
            scale=1.0,
            translateTo='',
            rotateTo='',
            parent='',
            shape=1,
            angle='y',
            lockChannels=['s', 'v']):

        ###################################################################################################
        # @param shape : 1 = circle
        # @param shape : 2 = square
        # @param shape : 2 = sphere

        control_object = None
        self.angle = angle

        if shape == 1:
            control_object = cmds.circle(n=prefix + '_CTL', normal=[0, 1, 0], ch=False, radius=1.0)[0]
        elif shape == 2:
            control_object = cmds.curve(n=prefix + '_CTL', d=1, p=[(-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1)], k=[0, 1, 2, 3, 4])
        elif shape == 3:
            control_object = cmds.circle(n=prefix + '_CTL', ch=False, normal=[1, 0, 0], radius=1.0)[0]
            add_shape = cmds.circle(n=prefix + '_CTL2', ch=False, normal=[0, 0, 1], radius=1.0)[0]
            cmds.parent(cmds.listRelatives(add_shape, shapes=True), control_object, r=True, s=True)
            cmds.delete(add_shape)

        elif shape == 4:
            control_object = cmds.circle(n=prefix + '_CTL', ch=False, normal=[1, 0, 0], radius=1.0)[0]
            add_shape_2 = cmds.circle(n=prefix + '_CTL3', ch=False, normal=[0, 1, 0], radius=1.0)[0]
            add_shape = cmds.circle(n=prefix + '_CTL2', ch=False, normal=[0, 0, 1], radius=1.0)[0]
            cmds.parent(cmds.listRelatives(add_shape, shapes=True), control_object, r=True, s=True)
            cmds.parent(cmds.listRelatives(add_shape_2, shapes=True), control_object, r=True, s=True)
            cmds.delete(add_shape)
            cmds.delete(add_shape_2)
        #
        result = tools.create_groups(control_object)
        cmds.scale(scale, scale, scale, control_object + ".cv[*]", relative=True)

        # public members:
        self.control = control_object
        self.root = result[0]
        self.auto = result[1]
        self.lockChannels = lockChannels
        self._angle = angle

        # translate control
        if cmds.objExists(translateTo):
            cmds.delete(cmds.pointConstraint(translateTo, self.root))

        # rotate control
        if cmds.objExists(rotateTo):
            cmds.delete(cmds.orientConstraint(rotateTo, self.root))

        # parent control
        if cmds.objExists(parent):
            cmds.parent(self.root, parent)

        # execute methods
        self.overide_color()
        self.lock_control_channels()
        self.setAngle(self._angle)

    ###################################################################################################
    # lock control channels

    def lock_control_channels(self):
        singleAttributeLockList = []

        for lockChan in self.lockChannels:
            if lockChan in ['t', 'r', 's']:
                for axis in ['x', 'y', 'z']:
                    at = lockChan + axis
                    singleAttributeLockList.append(at)

            else:
                singleAttributeLockList.append(lockChan)

            for attr in singleAttributeLockList:

                cmds.setAttr(self.control + '.' + attr, l=True, k=False)

    ###################################################################################################
    # control color

    def overide_color(self, side=None, index=0):
        control_shape = cmds.listRelatives(self.control, shapes=True)
        [cmds.setAttr(shape + '.ove', True) for shape in control_shape]

        if index > 0:
            side = None
            [cmds.setAttr(shape + '.ovc', index) for shape in cmds.listRelatives(self.control, shapes=True)]
            return

        if side is None and index == 0:
            if '_IK_' in self.control[:]:
                [cmds.setAttr(shape + '.ovc', 17) for shape in control_shape]

            elif '_FK_' in self.control[:]:
                [cmds.setAttr(shape + '.ovc', 13) for shape in control_shape]

            else:
                [cmds.setAttr(shape + '.ovc', 14) for shape in control_shape]
                # print('test')

    ###################################################################################################
    # rotate shape

    def setAngle(self, angle):
        angle = angle.lower()
        obj = self.control

        if angle == "x":
            cmds.rotate(90, obj + ".cv[*]", rotateZ=True, relative=True)
        elif angle == "y":
            cmds.rotate(90, obj + ".cv[*]", rotateY=True, relative=True)
        elif angle == "z":
            cmds.rotate(90, obj + ".cv[*]", rotateX=True, relative=True)

    ###################################################################################################

###################################################################################################


if __name__ == '__main__':
    print('\n __init__ ')
    control = Control
    control(prefix='hips', shape=1, scale=2.5, angle='x')
    # control(prefix='hips', shape=1, angle='x')
