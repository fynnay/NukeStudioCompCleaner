# This script should be run inside a freshly created nuke script
# It will:
# DELETE NODES:
#   - Reformat
#   - Copy
#   - AppendClip
# SET THE PROJECT FORMAT
#   - Will be set to the input value passed from commandline

import nuke
import nukescripts
import os
import sys
import ast # for evaluating string to list

#=================================================================================================
# FUNCTION : ddList
# v 1.2
#-------------------------------------------------------------------------------------------------
# Returns the name of the selected item in the list.
# :param dListName   : str     : Name of the dialog window and the name displayed beside the dropdown menu
# :param dListItems  : list    : [item[,*item]]
# :param defaultItem : str|int : Zero-based index or string for the item to default to
# :param *infoText   : str     : (optional) Text to display at the top of the window.
#=================================================================================================
def ddList(dListName,dListitems,defaultItem,*infoText):
    class DropDownlistWindow(nukescripts.PythonPanel): 
        def __init__(self, name,items,default,*info): 
            # Create the base of the window
            nukescripts.PythonPanel.__init__(self,"Select %s"%name) 
            # Create and populate the dropdown list
            self.dropDownList = nuke.Enumeration_Knob(name.lower(),"%s "%name,items) 
            self.dropDownList.setValue(default)
            # Create info text
            if len(info)>0:
                import textwrap
                # Add some returns to the text, so it doesn't go out of frame.
                modText = "\n".join(textwrap.wrap(info[0],width=40,replace_whitespace=False,drop_whitespace=False))
                self.infoText = nuke.Text_Knob("Info:")
                self.infoText.setValue(modText)
            # Create divider
            self.divider = nuke.Text_Knob("")
            self.divider.setFlag(nuke.STARTLINE)
            # Create Checkboxes
            # Version up
            self.vCheckBox = nuke.Boolean_Knob("versionUp","Version Up .nk Script",1)
            self.vCheckBox.setFlag(nuke.STARTLINE)
            # Add the UI elements to the window.
            if len(info)>0:
                self.addKnob(self.infoText)
            self.addKnob(self.dropDownList)
            self.addKnob(self.divider)
            self.addKnob(self.vCheckBox)
    # Create instance of dropdownlist class
    if len(infoText)>0:
        ddListInstance = DropDownlistWindow(dListName,dListitems,defaultItem,infoText[0])
    else:
        ddListInstance = DropDownlistWindow(dListName,dListitems,defaultItem)
    # Show window
    dialog = ddListInstance.showModalDialog()
    # Return selected item
    if dialog:
        return [ddListInstance.dropDownList.value(),ddListInstance.vCheckBox.value()]
    else:
        return None


# AUTO WRITE FOLDER FIX
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

# DELETE NODES
def deleteNodes():
    Log = _DebugPrint("deleteNodes")
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

# SET ROOT FORMAT
def setRootFormat(inpFormat):
    # Add new format to root and set it
    projectRoot   = nuke.root()
    width    = inpFormat[0]
    height   = inpFormat[1]
    pxAspect = inpFormat[2]
    name     = inpFormat[3]
    # Remove format if it exists
    
    # Add new format
    newRootFormat = "%s %s %s %s"%(width,height,pxAspect,name) # width height aspect name : <int> <int> <float> <str>
    nuke.addFormat(newRootFormat)
    projectRoot['format'].setValue(name)

def runInteractive():
    Log = _DebugPrint('runInteractive',True)
    # Variables
    #-------------------------------------
    inpFormat     = None
    versionUpBool = None
    allReadNodes = []

    # Get all read node's names and input format from metadata
    #-------------------------------------
    for i in nuke.allNodes():
        if i.Class() == "Read":
            # inpW = i.metadata().get("input/width")
            # inpH = i.metadata().get("input/height")
            inpW = i.format().width()
            inpH = i.format().height()
            pxAs = i.format().pixelAspect()
            inpF = "%s %s %s"%(inpW,inpH,pxAs)
            if inpW == None or inpH == None:
                continue
                #inpF = "Invalid input format."
            readInfo = i.name() + " : " + str( inpF )
            allReadNodes.append(readInfo)
    # If no valid read nodes where found
    if not len(allReadNodes) > 0:
        allReadNodes.append("None")
    allReadNodes.reverse()

    # Create the pop-up dialog
    #-------------------------------------
    info = "Select the read node with the format you want to use as the root format."
    userOptions = ddList("Fix Specialcomp",allReadNodes,0,info)
    if userOptions == None:
        Log.msg("Cancelled.")
        return
    
    # Read userOptions
    #-------------------------------------
    # Input Format
    if userOptions[0] == "None":
        inpFormat = None
    else:
        inpReadName = userOptions[0].split(" : ")[0]
        nodeFormat  = nuke.toNode(inpReadName).format()
        inpFormat   = [ nodeFormat.width() , nodeFormat.height() , nodeFormat.pixelAspect() , inpReadName]
    # versionUpBool
    versionUpBool = userOptions[1]


    # Run Functions
    #-------------------------------------
    # Set root format
    if not inpFormat == None:
        setRootFormat(inpFormat)
    # Auto Write Folder
    AutoWriteFolder()
    # Delete Nodes
    nuke.Undo.begin("Delete Unnecessary Nodes")
    with nuke.Undo():
        deleteNodes()
    nuke.Undo.end()

    # Check if script is saved
    #-------------------------------------
    if nuke.root().name() == "Root":
        Log.msg("WARNING: Script is not saved.")
        nuke.message("File could not be saved.\nPlease save it manually to save the changes.")
    else:
        # Save the script
        #-------------------------------------
        if versionUpBool == True:
            Log.msg("Saving Script as new version...")
            nukescripts.script_version_up()
        else:
            Log.msg("Saving Script...")
            nuke.scriptSave(nuke.root().name())
    Log.msg("Done.")

def runCommandLine():
    Log = _DebugPrint('runCommandLine',False)
    Log.msg("arg0: %s" % sys.argv[0])
    Log.msg("arg1: %s" % sys.argv[1])
    Log.msg("arg2: %s" % sys.argv[2])
    Log.msg("arg2: %s" % sys.argv[3])
    
    pythonScript  = sys.argv[0]
    nukeScript    = sys.argv[1]
    inpFormat     = ast.literal_eval(sys.argv[2])
    versionUpBool = ast.literal_eval(sys.argv[3]) # True or False

    # Open the Nuke File
    if not os.path.exists(nukeScript):
        Log.msg("Nuke file doesn't exist: %s"%(nukeScript))
        return

    inScript = nukeScript
    Log.msg("Opening script...")
    nuke.scriptOpen( inScript )
    # Run Functions        
    try:
        setRootFormat(inpFormat)
    except:
        Log.msg("Failed to set root format.")
    try:
        AutoWriteFolder()
    except:
        Log.msg("Failed to fix auto write folder.")
    try:
        deleteNodes()
    except:
        Log.msg("Failed to delete nodes...")


    # Save the script
    if versionUpBool == True:
        Log.msg("Saving Script as new version...")
        nukescripts.script_version_up()
    else:
        Log.msg("Saving Script...")
        nuke.scriptSave( inScript )
    Log.msg("Done.")


#__init__
def main():
    '''
    This script is meant to be run through the nuke commandline.
    It should receive theses sys.argv's:
    arg[0] :: path to this script
    arg[1] :: path to the nuke script to modify
    arg[2] :: Format [width height aspect name] to set for root
    arg[3] :: Create new version of script before saving? : True or False

    If it isn't run through the commandline, there are no special args passed.
    In this case a popup window opens, where the user is asked to make some choices.
    '''
    Log = _DebugPrint("fix_specialcomp")
    if not len ( sys.argv ) > 0:
        Log.msg( "ERROR: Not enough sys.argv's passed to script 'fix_specialcomp.py'. Args passed: %s"%(len ( sys.argv )))
        sys.exit(-1)

    if len(sys.argv)>1:
        Log.msg("Mode: Commandline")
        runCommandLine()
    else:
        Log.msg("Mode: Interactive")
        runInteractive()

main()