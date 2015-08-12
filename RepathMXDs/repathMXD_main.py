'''
Created by Luke Caruana, Geoscience Australia
Date created: 2 March 2015
Last Updated: 29 June 2015

This script searches a folder or directory strucutre for .mxd files and spawns
a sub-process which repaths each layer of the .mxd file to a new data source.

This script is modified to be run from a custom ArcGIS tool, in ArcCatalog.

A single, 'old' data source path and equivilant 'new' data source path are defined
by the user and used in the sub-process to repath layers in mxds.

This script assumes that the data structure within the current and new data source
paths have not changed, only the top level folder location/name/drive-letter
has changed.
'''

# Import modules
import os, arcpy, string, sys, time

# define python paths for spawn process, this path should be common for all users
python = r"C:\Python27\ArcGIS10.2\python.exe"
exe = os.path.basename(python)

# location of spawned python script: mxdPrepper.py
current = sys.argv[0]
mxdPrepper = os.path.join(os.path.dirname(current), "repathMXD_spawn.py")

# Import and name parameters from ArcGIS Tool 
topLevel = arcpy.GetParameterAsText(0)   
oldRoot = arcpy.GetParameterAsText(1)
newRoot = arcpy.GetParameterAsText(2)
reportFolder = arcpy.GetParameterAsText(3)
subfolder = arcpy.GetParameter(4)

# Ensure consistency in folder directory name. Both Old and New Root strings will end with a '\'
if not oldRoot.endswith("\\"):
    oldRoot = oldRoot + "\\"
    
if not newRoot.endswith("\\"):
    newRoot = newRoot + "\\"


def checksubfolders(topLevel):
    '''Finds all .mxd files in all subfolders starting from the top 
    level user input folder'''
    for root, dirs, files in os.walk(topLevel):

    # "~snapshot" folders are automated backup folders at Geoscience Australia. 
    # This excludes them as subfolders to ensure they are not included in the mxd search
        dirs[:] = [d for d in dirs if d not in "~snapshot"]

        # for each folder and subfolder, find .mxd files
        for f in files:
            if f.endswith(".mxd"):
                # spawn the mxdPrepper pyhton script for each .mxd file
                mxdpath = os.path.join(root, f)
                spawnv(mxdpath)                

def nosubfolders(topLevel):
    ''' Finds all .mxd files within the user defined top level folder'''
     
    for f in os.listdir(topLevel):
        if f.endswith(".mxd"):
            # spawn the mxdPrepper pyhton script for each .mxd file
            mxdpath = os.path.join(topLevel, f)
            spawnv(mxdpath)

def spawnv(mxdpath):
    '''spawns a subprocess to repath layer within the current mxd'''
    
    arcpy.AddMessage("spawning " + os.path.basename(mxdpath))
    # os.spawnv deliminates strings based on spaces
    # temporarily replaces spaces with a set of uncommon characters
    MP = string.replace(mxdpath, " ", "~`")
    OR = string.replace(oldRoot, " ", "~`")
    NR = string.replace(newRoot, " ", "~`")
    TN = string.replace(txtName, " ", "~`")
            
    # send the .mxd file and required variables to the mxdPrepper python script 
    # os.P_WAIT will pause this script until the spawned script has completed
    os.spawnv(os.P_WAIT, python, [exe,
                                  mxdPrepper, 
                                  TN, 
                                  MP, 
                                  OR, 
                                  NR
                                  ])
    
def datetime():
    '''returns a time and date stamp tuple from current local time'''
    
    date = time.strftime('%Y%m%d', time.localtime())
    clock = time.strftime('%H%M', time.localtime())
 
    return(date, clock)

if __name__ == "__main__":

    # create a text file to log the script statistics
    txtName = os.path.join(reportFolder, "{base}_Repath_MXD_Log_{date}_{time}.txt".format(
    base = string.split(topLevel, "\\")[-1],
    date = datetime()[0],
    time = datetime()[1]
    ))
    
    txtFile = open(txtName, "w")
    
    txtFile.write("Script started: {date} {time}\n".format(
    date = datetime()[0],
    time = datetime()[1]
    ))
    
    arcpy.AddMessage("Script started: {date} {time}".format(
    date = datetime()[0],
    time = datetime()[1]
    ))
    
    # Directs the script to the correct function based on whether subfolders are selected or not
    if subfolder == True:
        arcpy.AddMessage("Searching for mxds in {} and subfolders...".format(
        topLevel))
        txtFile.write("Searching for mxds in {} and subfolders...\n".format(
        topLevel))
        
        checksubfolders(topLevel)

    if subfolder == False:
        arcpy.AddMessage("Searching for mxds in {} only (no subfolders)...".format(
        topLevel))
        txtFile.write("Searching for mxds in {} only (no subfolders)...\n".format(
        topLevel))
        
        nosubfolders(topLevel)

    # close text file at script completion
    txtFile.write("\nScript log created: {}\n".format(txtName)) 
    txtFile.write("Script completed: {date} {time}\n".format(
    date = datetime()[0],
    time = datetime()[1]
    ))
    arcpy.AddMessage("\nScript log created: {}".format(txtName))
    txtFile.write("Script completed: {date} {time}".format(
    date = datetime()[0],
    time = datetime()[1]
    ))
    txtFile.close()