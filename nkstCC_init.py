#=================================================================================================
# SCRIPT : nkstCC_init.py :: Nuke Studio Comp Cleaner
# v1.0
#-------------------------------------------------------------------------------------------------
# Created by Fynn Laue 2016
# Thanks to Mads Hagbarth L. for code snippedts and sparring.
#-------------------------------------------------------------------------------------------------
# - Creates the _Debugprint class, that is used for printing messages by all scripts.
# - Checks things and launches the next script.
#=================================================================================================\
import nuke
import nukescripts
import os

#=================================================================================================
# CLASS : _DebugPrint
# v1.4
#-------------------------------------------------------------------------------------------------
# Used for clean, organized debugging.
# Ideally the print statements in this class should be the only ones in the script.
#=================================================================================================
class _DebugPrint:
    # At the beginning of every function, create an instance of this class like this:
    # >>> Log = _DebugPrint('NameOfFunction')
    # Print stuff like this:
    # >>> Log.msg('something')
    # Result:
    # Function :: NameOfFunction >> something
    def __init__(self,funcName,*enable):
        self.name   = funcName
        self.enable = True if not len(enable)>0 or enable[0]==True else False
        if self.enable : print "\nFunction :: ",self.name,"..."

    def msg(self,msg):
        if self.enable : 
            print "Function :: ",self.name,">>",msg

    def err(self,err):
        if self.enable : 
            import traceback
            import inspect
            callerframerecord = inspect.stack()[1]    # 0 represents this line, 1 represents line at caller
            frame = callerframerecord[0]
            info = inspect.getframeinfo(frame)
            line = info.lineno
            print "Function :: ",self.name,">>","Error at Line:",line,": ",err,"\n{"
            traceback.print_exc()
            print "\n}"

#=================================================================================================
# FUNCTION : ddList
# v 1.2
#-------------------------------------------------------------------------------------------------
# Returns the name of the selected item in the list and value of the checkbox.
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
# FUNCTION : main
# v1.0
#-------------------------------------------------------------------------------------------------
# Checks if all scripts are where they should be.
# Launches the appropriate script according the the type of nuke mode we're in.
#=================================================================================================
def main():
    Log = _DebugPrint('nkstCC_init.main')

    # Python Scripts locations
    exeSD  = os.path.dirname(__file__)
    # Nuke Studio Script
    nkstSN = "nkstCC_nkst.py"
    nkstSP = os.path.join(exeSD,nkstSN)
    # Nuke Script
    nukeSN = "nkstCC_nuke.py"
    nukeSP = os.path.join(exeSD,nukeSN)
    # Commandline Script
    cmdlSN = "nkstCC_cmd.py"
    cmdlSP = os.path.join(exeSD,nukeSN)

    # Check nuke mode and assign script to run
    exeScriptPath = nkstSP if nuke.env['studio'] else nukeSP
    
    # Cancel if python script not found
    if not os.path.exists(exeScriptPath):
        msg = "Can't find the script file at %s"%(exeScriptPath)
        Log.msg(msg)
        nuke.message(msg)
        return
    
    import nkstCC_nkst
    import nkstCC_nuke
    # Launch exescript
    if nuke.env['studio']:
        nkstCC_nkst.main(cmdlSP)
    else:
        nkstCC_nuke.main()

#__INIT__
if __name__ == "__main__":
    main()