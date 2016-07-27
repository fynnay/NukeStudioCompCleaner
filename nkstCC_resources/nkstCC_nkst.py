#=================================================================================================
# FUNCTION : FixNukeStudioComps
# v 1.0
#-------------------------------------------------------------------------------------------------
# For all selected items in the timeline it will:
# - Find the associated nuke script (in filesource's name)
# - Find the mainPlate's format
# - Run the "nkstCC_cmd.py" script for every nukeScript:
# TODO: - Version up the clip if versionUpBool is True
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
        msg = "Nothing selected.\nSelect some comp clips (.nk scripts).\n\nHow to build comp clips tracks:\nhttp://help.thefoundry.co.uk/nuke/content/timeline_environment/exporting/building_vfx_tracks.html"
        Log.msg(msg)
        nuke.message(msg)
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
    versionUpBool = userOptions[1]
    Log.msg("Version Up : %s"%(versionUpBool))
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Process selected timeline items:
    noNukeScript    = []
    noMainPlate     = []
    versionMismatch = []
    failedToProcess = []
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
        # Fail item if nkScriptPath can't be found or doesn't exist
        if nkScriptPath == None or not os.path.exists(nkScriptPath):
            Log.msg("Can't find .nk script for %s"%itemName)
            noNukeScript.append(itemName)
            continue
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Check version
        curVersion = item.currentVersion()
        maxVersion = item.maxVersion()
        if not curVersion == maxVersion:
            Log.msg("Version mismatch for %s"%itemName)
            versionMismatch.append(itemName)
            item.setCurrentVersion(curVersion)
            continue
        item.setCurrentVersion(curVersion)

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Get mainPlate from mainTrack
        inPoint       = item.timelineIn()
        outPoint      = item.timelineOut()-1
        midPoint      = inPoint+(outPoint-inPoint)/2
        mainPlate = None
        def getMainPlate(TLtime):
            brotherItems  = activeSequence.trackItemsAt(TLtime)
            for clip in brotherItems:
                if clip.parentTrack().name() == mainTrack:
                    return clip
            return None
        # Check for mainplate at midPoint
        mainPlate = getMainPlate(midPoint)
        # If nothing was found, try the inPoint
        if mainPlate == None:
            mainPlate = getMainPlate(inPoint)
        # If nothing was still found, try the outPoint
        if mainPlate == None:
            mainPlate = getMainPlate(outPoint)
        # If mainPlate can't be found on mainTrack, fail item.
        if mainPlate == None:
            Log.msg("Can't find main plate for '%s' on track '%s'"%(itemName,mainTrack))
            noMainPlate.append(itemName)    
            continue
        # Get mainPlate's format
        #srcFile     = clip.source()
        srcFile     = mainPlate.source()
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
            exe = subprocess.Popen([nuke.EXE_PATH,'-t',exeScriptPath, nkScriptPath, rootFormat, str(versionUpBool)],stdout = subprocess.PIPE)
            # Enable the next two lines for debugging the subprocess' stdout. The script will run significantly slower! 
            # txt = exe.communicate()[0]
            # Log.msg("subprocess stdout: >>> %s <<<"%txt)

            # BUG: nextVersion() or maxVersion() does NOT work here. If run seperately, the function works. WHY?!
            if versionUpBool == True:
                item.nextVersion()
            processedItems.append(itemName)
        except:
            failedToProcess.append(itemName)
            Log.err("Failed to run subprocess.")
    
    # Print result of processing to script editor
    Log.enable = True
    msg = "\nOUTPUT:\n"
    msg+= "Processed Items: \n%s"%("\n".join(processedItems))
    msg+= "\n\n"
    msg+= "Nuke Script not found: \n%s"%("\n".join(noNukeScript))
    msg+= "\n\n"
    msg+= "No Main Plate found: \n%s"%("\n".join(noMainPlate))
    msg+= "\n\n"
    msg+= "Failed to process: \n%s"%("\n".join(failedToProcess))
    msg+= "\n\n"
    msg+= "Version Mismatch: \n%s"%("\n".join(versionMismatch))
    if len(versionMismatch) > 0:
        msg+= """\nWhen 'Version Up .nk Script' is checked, but the selected clip isn't linked to the latest version, the item can't be processed.
There are 2 solutions to this:
Handle this with care!! You might mess up a nuke script that has already been worked on. Remember that you should generally only run this script on newly created comps.
[1] Max the version on the selected comp clips and try again with them selected.
[2] Uncheck 'Version Up .nk Script'.\n"""
    Log.msg(msg)
    allFailedItems = noNukeScript + noMainPlate + versionMismatch + failedToProcess
    nuke.message("Done Processing.\n%s Items Processed.\n%s Items Failed\n\nSee script editor for more information."%(len(processedItems),len(allFailedItems)))
