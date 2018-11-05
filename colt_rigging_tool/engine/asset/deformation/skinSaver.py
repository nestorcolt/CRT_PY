import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.mel
import maya.cmds as cmds
import sys

###################################################################################################

bSkinPath = OpenMaya.MDagPath()
###################################################################################################


def bFindSkinCluster(objectName):
    it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kSkinClusterFilter)
    while not it.isDone():
        fnSkinCluster = OpenMayaAnim.MFnSkinCluster(it.item())
        fnSkinCluster.getPathAtIndex(0, bSkinPath)

        if OpenMaya.MFnDagNode(bSkinPath.node()).partialPathName() == objectName or OpenMaya.MFnDagNode(OpenMaya.MFnDagNode(bSkinPath.node()).parent(0)).partialPathName() == objectName:
            return it.item()
        it.next()
    return False

###################################################################################################


def bSaveSkinValues(inputFile):

    output = open(inputFile, 'w')

    selection = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selection)

    iterate = OpenMaya.MItSelectionList(selection)

    while not iterate.isDone():
        node = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        iterate.getDagPath(node, component)
        if not node.hasFn(OpenMaya.MFn.kTransform):
            print(OpenMaya.MFnDagNode(node).name() + ' is not a Transform node (need to select transform node of polyMesh)')
        else:
            objectName = OpenMaya.MFnDagNode(node).name()
            newTransform = OpenMaya.MFnTransform(node)
            for childIndex in range(newTransform.childCount()):
                childObject = newTransform.child(childIndex)
                if childObject.hasFn(OpenMaya.MFn.kMesh) or childObject.hasFn(OpenMaya.MFn.kNurbsSurface) or childObject.hasFn(OpenMaya.MFn.kCurve):
                    skinCluster = bFindSkinCluster(OpenMaya.MFnDagNode(childObject).partialPathName())
                    if skinCluster is not False:
                        bSkinPath = OpenMaya.MDagPath()
                        fnSkinCluster = OpenMayaAnim.MFnSkinCluster(skinCluster)
                        fnSkinCluster.getPathAtIndex(0, bSkinPath)
                        influenceArray = OpenMaya.MDagPathArray()
                        fnSkinCluster.influenceObjects(influenceArray)
                        influentsCount = influenceArray.length()
                        #output.write(bSkinPath.partialPathName() + '\n')
                        output.write(objectName + '\n')

                        for k in range(influentsCount):
                            jointTokens = str(influenceArray[k].fullPathName()).split('|')
                            jointTokens = jointTokens[len(jointTokens) - 1].split(':')
                            output.write(jointTokens[len(jointTokens) - 1] + '\n')

                        output.write('============\n')

                        vertexIter = OpenMaya.MItGeometry(bSkinPath)

                        saveString = ''
                        counterValue = 0
                        while not vertexIter.isDone():
                            counterValue = counterValue + 1
                            vertex = vertexIter.component()

                            scriptUtil = OpenMaya.MScriptUtil()
                            infCountPtr = scriptUtil.asUintPtr()
                            vtxComponents = OpenMaya.MObject()
                            weightArray = OpenMaya.MDoubleArray()

                            fnSkinCluster.getWeights(bSkinPath, vertex, weightArray, infCountPtr)

                            saveString = ''

                            for j in range(OpenMaya.MScriptUtil.getUint(infCountPtr)):
                                saveString += str(weightArray[j])
                                saveString += ' '

                            output.write(saveString + '\n')

                            vertexIter.next()
                        output.write('\n')

        iterate.next()

    output.close()
    print("done saving weights")

###################################################################################################


def bSkinObject(objectName, joints, weights):

    if not cmds.objExists(objectName):
        print(objectName, " doesn't exist - skipping. ")
        return

    allInfluencesInScene = True
    jointsCheck = []
    for i in range(len(joints)):
        jointsCheck = joints[i]

    sceneJointTokens = []
    fileJointTokens = []

    it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kJoint)
    # quick check:
    for jointIndex in range(len(joints)):
        jointHere = False
        it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kJoint)
        while not it.isDone():
            sceneJointTokens = str(OpenMaya.MFnDagNode(it.item()).fullPathName()).split('|')
            if str(joints[jointIndex]) == str(sceneJointTokens[len(sceneJointTokens) - 1]):
                jointHere = True

            it.next()

        if not jointHere:
            allInfluencesInScene = False
            print('missing influence: ', joints[jointIndex])

    if not allInfluencesInScene:
        print(objectName, " can't be skinned because of missing influences.")
        return

    #maya.mel.eval("undoInfo -st 0")

    if type(bFindSkinCluster(objectName)) != type(True):
        maya.mel.eval("DetachSkin " + objectName)

    cmd = "select "
    for i in range(len(joints)):
        cmd += " " + joints[i]

    cmd += " " + objectName
    maya.mel.eval(cmd)

    maya.mel.eval("skinCluster -tsb -mi 10")
    maya.mel.eval("select `listRelatives -p " + objectName + "`")
    maya.mel.eval("refresh")
    #maya.mel.eval("undoInfo -st 1")

    skinCluster = bFindSkinCluster(objectName)
    fnSkinCluster = OpenMayaAnim.MFnSkinCluster(skinCluster)
    InfluentsArray = OpenMaya.MDagPathArray()
    fnSkinCluster.influenceObjects(InfluentsArray)

    bSkinPath = OpenMaya.MDagPath()
    fnSkinCluster.getPathAtIndex(fnSkinCluster.indexForOutputConnection(0), bSkinPath)

    weightStrings = []
    vertexIter = OpenMaya.MItGeometry(bSkinPath)

    weightDoubles = OpenMaya.MDoubleArray()

    singleIndexed = True
    vtxComponents = OpenMaya.MObject()
    fnVtxComp = OpenMaya.MFnSingleIndexedComponent()
    fnVtxCompDouble = OpenMaya.MFnDoubleIndexedComponent()

    if bSkinPath.node().apiType() == OpenMaya.MFn.kMesh:
        vtxComponents = fnVtxComp.create(OpenMaya.MFn.kMeshVertComponent)
    elif bSkinPath.node().apiType() == OpenMaya.MFn.kNurbsSurface:
        singleIndexed = False
        vtxComponents = fnVtxCompDouble.create(OpenMaya.MFn.kSurfaceCVComponent)
    elif bSkinPath.node().apiType() == OpenMaya.MFn.kNurbsCurve:
        vtxComponents = fnVtxComp.create(OpenMaya.MFn.kCurveCVComponent)

    # mapping joint-indices
    influenceIndices = OpenMaya.MIntArray()
    checkInfluences = []

    for k in range(InfluentsArray.length()):
        checkInfluences.append(0)
    for i in range(len(joints)):
        influenceIndices.append(-1)

    for i in range(len(joints)):
        fileJointTokens = joints[i].split('|')

        for k in range(InfluentsArray.length()):

            sceneJointTokens = str(OpenMaya.MFnDagNode(InfluentsArray[k]).fullPathName()).split('|')
            if fileJointTokens[len(fileJointTokens) - 1] == sceneJointTokens[len(sceneJointTokens) - 1]:  # changed from joints
                influenceIndices[i] = k
                checkInfluences[k] = 1

    counterValue = 0
    if not singleIndexed:
        currentU = 0
        currentV = 0

        cvsU = OpenMaya.MFnNurbsSurface(bSkinPath.node()).numCVsInU()
        cvsV = OpenMaya.MFnNurbsSurface(bSkinPath.node()).numCVsInV()
        formU = OpenMaya.MFnNurbsSurface(bSkinPath.node()).formInU()
        formV = OpenMaya.MFnNurbsSurface(bSkinPath.node()).formInV()

        if formU == 3:
            cvsU -= 3
        if formV == 3:
            cvsV -= 3

    vertexIter = OpenMaya.MItGeometry(bSkinPath)
    while not vertexIter.isDone():
        weightStrings = []
        if singleIndexed:
            fnVtxComp.addElement(counterValue)
        else:
            fnVtxCompDouble.addElement(currentU, currentV)
            currentV += 1
            if currentV >= cvsV:
                currentV = 0
                currentU += 1

        weightStrings = weights[counterValue].split(' ')
        for i in range(len(weightStrings)):
            weightDoubles.append(float(weightStrings[i]))
        counterValue += 1
        vertexIter.next()

    # SET WEIGHTS
    print ("setting weights for  ", objectName)
    fnSkinCluster.setWeights(bSkinPath, vtxComponents, influenceIndices, weightDoubles, 0)
    #Maya.mel.eval("skinPercent -normalize true " + fnSkinCluster.name() + " " + objectName)

    influenceIndices.clear()
    weightDoubles.clear()

###################################################################################################


def bLoadSkinValues(loadOnSelection, inputFile):
    joints = []
    weights = []
    PolygonObject = ""

    if loadOnSelection == True:
        selectionList = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList(selectionList)
        node = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        if selectionList.length():
            selectionList.getDagPath(0, node, component)
            if node.hasFn(OpenMaya.MFn.kTransform):
                NewTransform = OpenMaya.MFnTransform(node)
                if NewTransform.childCount():
                    if NewTransform.child(0).hasFn(OpenMaya.MFn.kMesh):
                        PolygonObject = str(OpenMaya.MFnDagNode(NewTransform.child(0)).partialPathName())

    if loadOnSelection and len(PolygonObject) == 0:
        print("You need to select a polygon object")
        return

    input = open(inputFile, 'r')

    FilePosition = 0
    while True:
        line = input.readline()
        if not line:
            break

        line = line.strip()

        if FilePosition is not 0:
            if not line.startswith("============"):
                if FilePosition is 1:
                    joints.append(line)
                elif FilePosition is 2:
                    if len(line) > 0:
                        weights.append(line)
                    else:
                        bSkinObject(PolygonObject, joints, weights)
                        PolygonObject = ""
                        joints = []
                        weights = []
                        FilePosition = 0
                        if loadOnSelection == True:
                            break

            else:  # it's ========
                FilePosition = 2

        else:  # FilePosition is 0
            if not loadOnSelection:
                PolygonObject = line
            FilePosition = 1

            if cmds.objExists(PolygonObject):
                maya.mel.eval("select " + PolygonObject)
                maya.mel.eval("refresh")
