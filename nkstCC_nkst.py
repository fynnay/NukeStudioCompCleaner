#=================================================================================================
# FUNCTION : FixNukeStudioComps
# v 1.0
#-------------------------------------------------------------------------------------------------
# For all selected items in the timeline:
# - Find the associated nuke script (in filesource's name or tags['script'])
# - Find the mainPlate's format
# - Run the "nkstCC_cmd.py" script for every nukeScript:
# TODO: Version up the clip if versionUpBool is True
#=================================================================================================
import os
import nuke
import subprocess
import hiero
import nkstCC_init

def main(exeScriptPath):
    Log = nkstCC_init._DebugPrint('nkstCC_nkst.main')
    
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Active Sequence
    activeSequence = hiero.ui.activeSequence()
    if activeSequence == None:
        msg = "No active sequence. Please open a sequence and try again"
        Log.msg(msg)
        nuke.message(msg)
        return
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
    userOptions = nkstCC_init.ddList("Fix NukeStudio Comps",allTrackNames,0,info)
    if userOptions == None:
        Log.msg("Cancelled.")
        return
    mainTrack     = userOptions[0]
    versionUpBool = str(userOptions[1])
    Log.msg("Versionup : %s"%versionUpBool)
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Process selected timeline items:
    versionMismatch = []
    failedItems     = []
    processedItems  = []
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
            if versionUpBool == True:
                item.nextVersion()
        except:
            failedItems.append(itemName)
            Log.err("Failed to run subprocess.")
    msg = "OUTPUT:\n"
    msg+= "ProcessedItems: %s"%("\n".join(processedItems))
    msg+= "\n\n"
    msg+= "Failed Items: %s"%("\n".join(failedItems))
    msg+= "Version Mismatch: "
    if len(versionMismatch) > 0:
        msg+= """When 'Version Up .nk Script' is checked, but the selected clip isn't linked to the latest version, the item can't be processed.
        There are 2 solutions to this:
        Handle this with care!! You might mess up a nuke script that has already been worked on. Remember that you should generally only run this script on newly created comps.
        [1] Max the version on the selected comp clips and try again with them selected.
        [2] Uncheck 'Version Up .nk Script'.
        """
    msg+= "\n",join(versionMismatch)
    Log.msg(msg)
    nuke.message("Done Processing.\n%s Items Processed.\n%s Items Failed\n\nSee script editor for more information."%(len(processedItems),len(failedItems)))