'''
Created by Luke Caruana, Geoscience Australia
Date created: 2 March 2015
Last Updated: 5 June 2015

This script is not desinged to be run in isolation from its parent script. 
It is a sub process, called from the repathMXD python script.
Spawning this script as a sub process has proven to reduce a memory leak
problem arcpy was creating when processing large quantities of .mxd files
and other spatial data.

This script takes a single .mxd file from the parent script and repaths the 
layers to a new, user defined directory, from an old, user defined directory 
'''

import os, arcpy, string, shutil, sys, time

# define variables from spawnv process
# os.spawnv deliminates strings on spaces
# return the spaces to spawned varibles 
TN = sys.argv[1]
txtName = string.replace(TN, "~`", " ")

# open text file and set to append, rather than re-write
txtFile = open(txtName, "a")

MP = sys.argv[2]
mxdPath = string.replace(MP,r"~`", " ")

OR = sys.argv[3]
NR = sys.argv[4]
oldRoot = string.replace(OR, "~`", " ")
newRoot = string.replace(NR, "~`", " ") 

def datetime():
    '''returns a time and date stamp tuple from current local time'''
    
    date = time.strftime('%Y%m%d', time.localtime())
    clock = time.strftime('%H%M', time.localtime())
 
    return(date, clock)

def crawlmxd(mxdPath):
    '''creates a backup copy, then attempts to repath each layer 
    of the .mxd file, saves mxd upon completion'''

    # creates a backup file of the original .mxd file (retains original metadata)
    # backup file is timestamped so it is not overwritten if script is run multiple times
    copy = mxdPath + "." + datetime()[0] + "_" + datetime()[1] + ".bak"

    # attempt to create backup file
    try:
        shutil.copy2(mxdPath, copy)
        print "Backup of mxd created: " + copy
        txtFile.write("Backup of mxd created: " + copy + "\n")

    # if backup cannot be created, repath of this mxd is aborted
    except:
        print "\tCannot create mxd backup, mxd not updated"
        txtFile.write("\tCannot create mxd backup, mxd not updated" + "\n")
        sys.exit()

    # creates map document object from the current mxd file path
    try:
        mxd = arcpy.mapping.MapDocument(mxdPath)
    
    # aborts script if arcpy cannot handle .mxd file as a map document
    except:
        print "\tCannot open mxd, mxd not updated"
        txtFile.write("\tCannot open mxd, mxd not updated" + "\n")
        sys.exit()       

    # within the current mxd, find all spatial layers
    print "\tScanning layers within mxd..."
    txtFile.write("\tScanning layers within mxd..." + "\n")

    # check spatial layers one-by-one
    for lyr in arcpy.mapping.ListLayers(mxd):
        lyrName = lyr.name

        txtFile.write("\t" + lyrName + "\n")
        arcpy.AddMessage("\t" + lyrName)

        # Only valid layers will be have repath attempted
        try:
            # if layer is a grounp layer, skip and check next layer
            if lyr.isGroupLayer == True:
                print "\t\t" + "Group Layer..."
                txtFile.write("\t\t" + "Group Layer..." + "\n")
                continue
            
            # if layer is not a group layer, attempt to run the repathlayer function
            else:
                repathlayer(lyr, oldRoot, newRoot)

        # if repathlayer funciton cannot be run on current layer, list as an error in text file report
        except:
            print "\t" + lyrName
            txtFile.write("\t" + lyrName + "\n")   
            print "\t\tLayer skipped - Error in getting source information for layer, check layer manually"
            txtFile.write("\t\tLayer skipped - Error in getting source information for layer, check layer manually" + "\n")

    # Check for existence of tables within mxds
    if arcpy.mapping.ListTableViews(mxd) != []:
        print "\n\tNon-spatial, Table Layers: "
        txtFile.write("\n\tNon-spatial, Table Layers: " + "\n")

        # if table layers exist, attempt to run through the repathlayer function
        for lyr in arcpy.mapping.ListTableViews(mxd):
            lyrName = lyr.name
            print "\t" + lyrName
            txtFile.write("\t" + lyrName + "\n")
            
            try:
                repathlayer(lyr, oldRoot, newRoot)

            # if repathlayer funciton cannot be run on current layer, list as an error in text file report
            except:
                print "\t" + lyrName
                txtFile.write("\t" + lyrName + "\n")                 
                print "\t\t" + "Error in getting source information for layer"
                txtFile.write("\t\t" + "Error in getting source information for layer" + "\n")

    # save mxd
    try:
        # Save relative paths
        mxd.relativePaths = False
        
        # to avoid errors with saving a currently opened mxd which potentially has database connections active
        # a temporary copy of the mxd is saved. Timestamp is used so the script can be run multiple times.
        temp = string.replace(mxdPath, ".mxd", "_" + datetime()[0] + "_" + datetime()[1] + ".mxd")
        mxd.saveACopy(temp)
        del mxd

        # delete the original mxd file from the directory
        os.remove(mxdPath)

        # rename the temp mxd so it matches the original mxdpath 
        os.rename(temp, mxdPath)
        del temp

        print "MXD saved successfully"
        txtFile.write("MXD saved successfully" + "\n")

    # if mxd cannot be re-saved, list as an error in the text file report   
    except:
        print "\tERROR: mxd not updated, unable to save updates to mxd"
        txtFile.write("\tERROR: mxd not updated, unable to save updates to mxd" + "\n")

# repathlayer function attempts to change the data source path of and input layer from the crawlmxds function
def repathlayer(lyr, oldRoot, newRoot):
    '''Attempts to change the data source path of and input layer from the crawlmxds function'''
    
    # get workspace path of current layer
    workspacePath = lyr.workspacePath

    # attempt to define a new workspace pathed by replacing the old root directory with the new root directory
    newPath = string.replace(workspacePath, oldRoot, newRoot)

    # if original workspace path matches the newly defined workspace path, layer will not be updated
    if newPath == workspacePath:
        return

    # if original and new workspace paths are different, layer can be updated    
    else:
        # arcpy function to replace old workspace path with new workspace path
        lyr.findAndReplaceWorkspacePath(workspacePath, newPath, False)
        
        print "\t\tOld workspace path: " + workspacePath
        txtFile.write("\t\tOld workspace path: " + workspacePath + "\n")
        print "\t\tNew workspace path: " + newPath
        txtFile.write("\t\tNew workspace path: " + newPath + "\n")
        return

if __name__ == "__main__":
    ''' Start the repath mxd process from spawned variables'''
    
    print "\nStarting: " + mxdPath
    txtFile.write("\nStarting: " + mxdPath + "\n")
    
    # Before progressing on current mxd, tests its validity by attempting to open and look at layers within
    try:
        mxd = arcpy.mapping.MapDocument(mxdPath)
        arcpy.mapping.ListLayers(mxd)
        del mxd
    
    # if validation test fails, abort process and return to parent script, list error in text file report
    except:
        print "\t" + mxdPath + " is not a valid mxd"
        txtFile.write("\t" + mxdPath + " is not a valid mxd" + "\n")
        sys.exit()
    
    # If mxd passes validation test, run the crawl mxd function using current mxd path as input  
    crawlmxd(mxdPath)
    
    # Spawned scirpt is complete, return to parent script
    print "\nMXD Repath Complete..."
    txtFile.write("\nMXD Repath Complete..." + "\n")
