#=================================================================================================
# SCRIPT : nkstCC_actions
# v 1.0
#-------------------------------------------------------------------------------------------------
# This script holds all functions used by nkstCC_nuke and nkstCC_cmd
#=================================================================================================
import nuke
import nkstCC_init

#=================================================================================================
# FUNCTION : AutoWriteFolder
# v 1.0
#-------------------------------------------------------------------------------------------------
# Puts a small python snippet into the "before render" field in all write nodes.
# This checks if the folder for the file exists, and creates it if it does't.
#=================================================================================================
def AutoWriteFolder():
    def RecursiveFindNodes(nodeClass, startNode):
        if startNode.Class() == nodeClass:
            yield startNode
        elif isinstance(startNode, nuke.Group):
            for child in startNode.nodes():
                for foundNode in RecursiveFindNodes(nodeClass, child):
                    yield foundNode
    allWriteNodes = [w for w in RecursiveFindNodes('Write', nuke.root())]
    for write in allWriteNodes:
        write['beforeRender'].setValue( """if not os.path.exists(os.path.dirname(nuke.thisNode().knob("file").value())): os.makedirs(os.path.dirname(nuke.thisNode().knob("file").value()))""" )

#=================================================================================================
# FUNCTION : deleteNodes
# v 1.0
#-------------------------------------------------------------------------------------------------
# Deletes unnecessary nodes, that NukeStudio creates for almost all SpecialComps:
# Nodes: Reformat, AppendClip, Copy, Constant
# While deleting it tries to keep the main pipe's flow intact.
#=================================================================================================
def deleteNodes():
    Log = nkstCC_init._DebugPrint("deleteNodes")
    for node in nuke.allNodes():
        # Delete Reformats
        if node.Class() == "Reformat":
            Log.msg("Deleting Node: %s"%(node.name()))
            nuke.delete(node)
        # Delete AppendClip
        elif node.Class() == "Copy":
            inp1 = node.input(0)
            inp2 = node.input(1)
            if inp1 == None or inp1.Class() == "Constant":
                node.setInput(0,inp2)
            nuke.delete(node)
        # Delete Copy
        elif node.Class() == "AppendClip":
            inp1 = node.input(0)
            inp2 = node.input(1)
            if inp1 == None or inp1.Class() == "Constant":
                node.setInput(0,inp2)
            nuke.delete(node)
        # Delete Constants
        elif node.Class() == "Constant":
            nuke.delete(node)

#=================================================================================================
# FUNCTION : setRootFormat
# v 1.0
#-------------------------------------------------------------------------------------------------
# Creates a new format for the project and selects it as the root format.
#=================================================================================================
def setRootFormat(inpFormat):
    # Add new format to root and set it
    projectRoot   = nuke.root()
    width    = inpFormat[0]
    height   = inpFormat[1]
    pxAspect = inpFormat[2]
    name     = inpFormat[3]
    
    # Add new format
    newRootFormat = "%s %s %s %s"%(width,height,pxAspect,name) # width height aspect name : <int> <int> <float> <str>
    nuke.addFormat(newRootFormat)
    projectRoot['format'].setValue(name)
