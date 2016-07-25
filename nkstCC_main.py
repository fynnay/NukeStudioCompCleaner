#=================================================================================================
# SCRIPT : nkstCC_main.py :: Nuke Studio Comp Cleaner
# v1.0
#-------------------------------------------------------------------------------------------------
# Created by Fynn Laue 2016
# Thanks to Mads Hagbarth L. for code snippedts and sparring.
#-------------------------------------------------------------------------------------------------
# Cleans up "special comps" created by NukeStudio. See function description below for more details.
# "nkstCC_slave.py" has to be in the same folder as this script !
#=================================================================================================\

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

#=================================================================================================
# FUNCTION : FixNukeStudioComps
# v 1.0
#-------------------------------------------------------------------------------------------------
# For all selected items in the timeline:
# - Find the associated nuke script (in filesource's name or tags['script'])
# - Find the mainPlate's format
# - Run the "nkstCC_slave.py" script for every nukeScript:
#   - Delete unneccessary/annoying nodes:
#       - Reformat
#       - Copy
#       - AppendClip
#       - Constant
#   - Add a python snippet to any write node: It creates missing folders before rendering.
#   - 
#=================================================================================================
def FixNukeStudioComps():
    import subprocess
    import hiero
    Log = _DebugPrint('FixNukeStudioComps')
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Python Script location
    #exeScriptDir   = Settings.getScriptsDir('nuke')
    exeScriptDir   = os.path.dirname(__file__)
    exeScriptName  = 'nkstCC_slave.py'
    exeScriptPath  = os.path.join(exeScriptDir,exeScriptName)
    # Cancel if python script not found
    if not os.path.exists(exeScriptPath):
        Log.msg("Can't find the '%s' script file at %s"%(exeScriptName,exeScriptDir))
        nuke.message("Can't find the '%s' script file at %s"%(exeScriptName,exeScriptDir))
        return
    
    def runNukeStudio():
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Active Sequence
        activeSequence = hiero.ui.activeSequence()
        selectedItems  = hiero.ui.getTimelineEditor(activeSequence).selection()
        # Cancel if nothing is selected
        if not len(selectedItems) > 0:
            Log.msg('Nothing selected.\nSelect some clips that are .nk scripts or have a "Nuke Project File"-tag.')
            nuke.message('Nothing selected.\nSelect some clips that are .nk scripts or have a "Nuke Project File"-tag.')
            return
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # User selects a 'mainTrack' that contains the mainPlate
        seqVidTracks = activeSequence.videoTracks()
        allTrackNames = [ i.name() for i in seqVidTracks ]
        info = "Select the track that holds the footage you want to use as the root format in each .nk Script."
        userOptions = ddList("Fix NukeStudio Comps",allTrackNames,0,info)
        if userOptions == None:
            Log.msg("Cancelled.")
            return
        mainTrack     = userOptions[0]
        versionUpBool = str(userOptions[1])
        Log.msg("Versionup : %s"%versionUpBool)
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Process selected timeline items:
        failedItems    = []
        processedItems = []
        for item in selectedItems:
            Log.msg('Current item: %s '%(item.name()))
            itemName = item.name()
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Get path to Nuke Script
            nkScriptPath = None
            # Check if selected clip is a .nk script
            mediaSrc  = item.source().mediaSource()
            srcExt    = os.path.splitext(mediaSrc.filename())[1]
            if srcExt == ".nk":
                nkScriptPath = mediaSrc.firstpath()
            # If not, check tags for ['script']
            else:
                if len(item.tags()) > 0:
                    for tag in item.tags():
                        tagMeta = tag.metadata()
                        if not tagMeta.hasKey("script"):
                            continue
                        nkScriptPath  = tagMeta.value("script")
            # Fail item if nkScriptPath can't be found or doesn't exist
            if nkScriptPath == None or not os.path.exists(nkScriptPath):
                failedItems.append(itemName)
                continue
            
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Get mainPlate from mainTrack
            inPoint       = item.timelineIn()
            brotherItems  = activeSequence.trackItemsAt(inPoint)
            mainPlate = None
            for clip in brotherItems:
                if clip.parentTrack().name() == mainTrack:
                    mainPlate = clip
            # Fail item if mainPlate clip can't be found on mainTrack
            if mainPlate == None:
                Log.msg("Can't find main plate for '%s' on track '%s'"%(itemName,mainTrack))
                failedItems.append(itemName)    
                continue
            # Get mainPlate's format
            srcFile     = clip.source()
            srcName     = srcFile.name()
            srcFormat   = srcFile.format()
            srcWidth    = srcFormat.width()
            srcHeight   = srcFormat.height()
            srcPxAsp    = srcFormat.pixelAspect()
            mpFormat    = [srcWidth, srcHeight, srcPxAsp, srcName] 
            mpFormat[3] = mainTrack
            rootFormat  = str(mpFormat) # [width, height, pxAspect, mainTrackName]
            
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Open nuke script through command line and execute python script with arguments
            try:
                exe = subprocess.Popen([nuke.EXE_PATH,'-t',exeScriptPath, nkScriptPath, rootFormat, versionUpBool],stdout = subprocess.PIPE)
                # Enable the next two lines for debugging the subprocess' stdout. The script will run significantly slower! 
                # txt = exe.communicate()[0]
                # Log.msg("subprocess stdout: >>> %s <<<"%txt)
                processedItems.append(itemName)
            except:
                failedItems.append(itemName)
                Log.err("Failed to run subprocess.")
        msg = "\n\nOUTPUT:\n"
        msg+= "ProcessedItems: %s"%("\n".join(processedItems))
        msg+= "\n\n"
        msg+= "Failed Items: %s"%("\n".join(failedItems))
        Log.msg(msg)
        nuke.message("Done Processing.\n%s Items Processed.\n%s Items Failed\n\nSee script editor for more information."%(len(processedItems),len(failedItems)))

    def runNuke():
        try:
            nuke.load(exeScriptPath)
        except:
            Log.err("Failed to run script '%s'"%exeScriptName)

    if nuke.env['studio']:
        runNukeStudio()
    else:
        runNuke()

#__INIT__
if __name__ == "__main__":
    FixNukeStudioComps()