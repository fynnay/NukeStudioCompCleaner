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
import os
import sys
import ast # for evaluating string to list
import nkstCC_init

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

    Log = nkstCC_init._DebugPrint("fix_specialcomp")
    Log.msg("number of args: %s"%(len(sys.argv)))

    # Cancel if number of arguments is invalid
    if not len( sys.argv ) > 1:
        Log.msg( "ERROR: Not enough sys.argv's passed to script 'fix_specialcomp.py'. Args passed: %s"%(len ( sys.argv )))
        sys.exit(-1)

    Log = nkstCC_init._DebugPrint('runCommandLine',True)
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

main()