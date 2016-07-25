#=================================================================================================
# SCRIPT : nkstCC_nuke
# v 1.0
#-------------------------------------------------------------------------------------------------
# This script is meant to be run inside of nuke.
# It creates a popup dialog for the user to make decisions.
# It uses the functions from nkstCC_actions to modify the script.
#=================================================================================================
import nuke
import nukescripts
import nkstCC_init
import nkstCC_actions

def main():
    Log = nkstCC_init._DebugPrint('nkstCC_nuke.main',True)
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
    userOptions = nkstCC_init.ddList("Fix Specialcomp",allReadNodes,0,info)
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
        nkstCC_actions.setRootFormat(inpFormat)
    # Auto Write Folder
    nkstCC_actions.AutoWriteFolder()
    # Delete Nodes
    nuke.Undo.begin("Delete Unnecessary Nodes")
    with nuke.Undo():
        nkstCC_actions.deleteNodes()
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