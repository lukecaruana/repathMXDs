'''
Created by Luke Caruana, Geoscience Australia
Date created: 2 March 2015
Last Updated: 14 August 2015

This script is not desinged to be run in isolation from its parent script. 
It is a sub process, called from the repathMXD python script.
Spawning this script as a sub process has proven to reduce a memory leak
problem arcpy was creating when processing large quantities of .mxd files
and other spatial data.

This script takes a single .mxd file from the parent script and repaths the 
layers to a new, user defined directory, from an old, user defined directory 
'''

import os, arcpy, string, shutil, sys, time, csv

# define variables from spawnv process
# os.spawnv deliminates strings on spaces
# return the spaces to spawned varibles 
TN = sys.argv[1]
txtName = string.replace(TN, "~`", " ")

# open text file and set to append, rather than re-write
txtFile = open(txtName, "a")

MP = sys.argv[2]
mxdPath = string.replace(MP,r"~`", " ")

CM = sys.argv[3]
csvMap = string.replace(CM, "~`", " ") 


def datetime():
    '''returns a time and date stamp tuple from current local time'''
    
    date = time.strftime('%Y%m%d', time.localtime())
    clock = time.strftime('%H%M', time.localtime())
 
    return(date, clock)
    

def createMapDict(csvMap):
    '''Creates a dictionary from a csv input, mapping old to new directory paths'''
    
    # Open the input csv file and enable it for reading
    with open(csvMap, "rb") as csvinput:
        reader = csv.reader(csvinput)
        
        # create an empty dictionary for each row in the csv to append its values
        d = {}
        
        # Cycle through each row in the csv and assign the new and old paths
        for row in reader:
            
            # first row in the csv is the old directory path to be updated
            o = row[0]
            
            # second row in the csv is the new equivilant directory path 
            n = row[1]
            
            # for each row, append the new and equivilant old path to the dictionary
            d[o] = n
    
    # Once all rows have
    return d


def matchWithDict(workspacePath, pathDict):
    '''Matches a layers workspace path with corresponding dictionary values'''
    
    # this loop function steps up from a layers workspace path until it 
    # matches with a key in the dictionary, created by the csv input
    
    # Search loop starts at the workspace path and works up through each directory
    startPath = workspacePath
    
    # lastRoot is the path checked in the previous iteration of the loop
    lastRoot = startPath
    
    # currentRoot is the current path being checked in the loop 
    currentRoot = startPath
    
    # matchedRoot and oldRoot start with 'None' assigned values
    matchedRoot = None
    oldRoot = None
    
    # the loop runs until a match is found and matchedRoot is assigned a value
    while matchedRoot is None and currentRoot:
        
        # trys to find a match between currentRoot and dictionary keys
        try:
            # if match is found, matchedRoot is assigned a value
            # matchedRoot value is the value retuned by the currentRoot key in the dictionary
            matchedRoot = pathDict[currentRoot]
            
            # oldRoot is the key used to find the matchedRoot value in the dictionary
            oldRoot = currentRoot
        
        # if no match is found on currentRoot, step up one directory level
        except:
            # reassign the lastRoot value for the next loop iteration
            lastRoot = currentRoot
                # save mxd
    try:
        # Save relative paths
        mxd.relativePaths = False
        
        # to avoid errors with saving a currently opened mxd which potentially has database connections active
        # a temporary copy of the mxd is saved. Timestamp is used so the script can be run multiple times.
        temp = string.replace(mxdPath, ".mxd", "_{date}_{time}.mxd".format(
        date = datetime()[0],
        time = datetime()[1]
        ))
        
        mxd.saveACopy(temp)
        del mxd

        # delete the original mxd file from the directory
        os.remove(mxdPath)

        # rename the temp mxd so it matches the original mxdpath 
        os.rename(temp, mxdPath)
        del temp

        print "MXD saved successfully"
        txtFile.write("MXD saved successfully\n")

    # if mxd cannot be re-saved, list as an error in the text file report   
    except:
        print "\tERROR: mxd not updated, unable to save updates to mxd"
        txtFile.write("\tERROR: mxd not updated, unable to save updates to mxd\n")
            # reassign the currentRoot value, to step up one directory level
            # re-run the loop
            currentRoot = os.path.dirname(lastRoot)
            
            # when the top level path of the directory is reached, stop the loop
            # and return empty valued variable            
            if currentRoot == lastRoot:
                break
    
    # upon complettion, return the key and its value found from the dictionary 
    return (oldRoot, matchedRoot)
    

def crawlmxd(mxdPath):
    '''creates a backup copy, then attempts to repath each layer 
    of the .mxd file, saves mxd upon completion'''

    # creates a backup file of the original .mxd file (retains original metadata)
    # backup file is timestamped so it is not overwritten if script is run multiple times
    copy = "{path}.{date}_{time}.bak".format(
    path = mxdPath,
    date = datetime()[0],
    time = datetime()[1]
    )

    # attempt to create backup file
    try:
        shutil.copy2(mxdPath, copy)
        print "Backup of mxd created: {}".format(copy)
        txtFile.write("Backup of mxd created: {}\n".format(copy))

    # if backup cannot be created, repath of this mxd is aborted
    except:
        print "\tCannot create mxd backup, mxd not updated"
        txtFile.write("\tCannot create mxd backup, mxd not updated\n")
        sys.exit()

    # creates map document object from the current mxd file path
    try:
        mxd = arcpy.mapping.MapDocument(mxdPath)
    
    # aborts script if arcpy cannot handle .mxd file as a map document
    except:
        print "\tCannot open mxd, mxd not updated"
        txtFile.write("\tCannot open mxd, mxd not updated\n")
        sys.exit()       

    # within the current mxd, find all spatial layers
    print "\tScanning layers within mxd..."
    txtFile.write("\tScanning layers within mxd...\n")

    # check spatial layers one-by-one
    for lyr in arcpy.mapping.ListLayers(mxd):
        lyrName = lyr.name

        txtFile.write("\t{}\n".format(lyrName))
        arcpy.AddMessage("\t{}".format(lyrName))

        # attempt to repath all layers
        try:
            repathlayer(lyr)

        # if repathlayer funciton cannot be run on current layer, list as an error in text file report
        except:
            print "\t{}".format(lyrName)
            txtFile.write("\t{}\n".format(lyrName))   
            print "\t\tLayer skipped - Error in getting source information for layer",
            " check layer manually"
            txtFile.write("\t\tLayer skipped - Error in getting source information for layer,")
            txtFile.write(" check layer manually\n")

    # Check for existence of tables within mxds
    if arcpy.mapping.ListTableViews(mxd) != []:
        print "\n\tNon-spatial, Table Layers: "
        txtFile.write("\n\tNon-spatial, Table Layers: \n")

        # if table layers exist, attempt to run through the repathlayer function
        for lyr in arcpy.mapping.ListTableViews(mxd):
            lyrName = lyr.name
            print "\t{}".format(lyrName)
            txtFile.write("\t{}\n".format(lyrName))
            
            try:
                repathlayer(lyr)

            # if repathlayer funciton cannot be run on current layer, list as an error in text file report
            except:
                print "\t{}".format(lyrName)
                txtFile.write("\t{}\n".format(lyrName))                 
                print "\t\tError in getting source information for layer"
                txtFile.write("\t\tError in getting source information for layer\n")

    # save mxd
    try:
        # Save relative paths
        mxd.relativePaths = False
        
        # to avoid errors with saving a currently opened mxd which potentially has database connections active
        # a temporary copy of the mxd is saved. Timestamp is used so the script can be run multiple times.
        temp = string.replace(mxdPath, ".mxd", "_{date}_{time}.mxd".format(
        date = datetime()[0],
        time = datetime()[1]
        ))
        
        mxd.saveACopy(temp)
        del mxd

        # delete the original mxd file from the directory
        os.remove(mxdPath)

        # rename the temp mxd so it matches the original mxdpath 
        os.rename(temp, mxdPath)
        del temp

        print "MXD saved successfully"
        txtFile.write("MXD saved successfully\n")

    # if mxd cannot be re-saved, list as an error in the text file report   
    except:
        print "\tERROR: mxd not updated, unable to save updates to mxd"
        txtFile.write("\tERROR: mxd not updated, unable to save updates to mxd\n")

# repathlayer function attempts to change the data source path of and input layer from the crawlmxds function
def repathlayer(lyr):
    '''Attempts to change the data source path of and input layer from the crawlmxds function'''
        
    pathDict = createMapDict(csvMap)
    # get workspace path of current layer
    workspacePath = lyr.workspacePath

    oldRoot = matchWithDict(workspacePath, pathDict)[0]
    newRoot = matchWithDict(workspacePath, pathDict)[1]
    
    if newRoot is None:
        return
    
    if not oldRoot.endswith("\\"):
        oldRoot = oldRoot + "\\"
    
    if not newRoot.endswith("\\"):
        newRoot = newRoot + "\\"
        
    # attempt to define a new workspace pathed by replacing the old root directory with the new root directory
    newPath = string.replace(workspacePath, oldRoot, newRoot)

    # if original workspace path matches the newly defined workspace path, layer will not be updated
    if newPath == workspacePath:
        return

    # if original and new workspace paths are different, layer can be updated    
    else:
        # arcpy function to replace old workspace path with new workspace path
        lyr.findAndReplaceWorkspacePath(workspacePath, newPath, False)
        
        print "\t\tOld workspace path: {}".format(workspacePath)
        txtFile.write("\t\tOld workspace path: {}\n".format(workspacePath))
        print "\t\tNew workspace path: {}".format(newPath)
        txtFile.write("\t\tNew workspace path: {}\n".format(newPath))
        return

if __name__ == "__main__":    # save mxd
    try:
        # Save relative paths
        mxd.relativePaths = False
        
        # to avoid errors with saving a currently opened mxd which potentially has database connections active
        # a temporary copy of the mxd is saved. Timestamp is used so the script can be run multiple times.
        temp = string.replace(mxdPath, ".mxd", "_{date}_{time}.mxd".format(
        date = datetime()[0],
        time = datetime()[1]
        ))
        
        mxd.saveACopy(temp)
        del mxd

        # delete the original mxd file from the directory
        os.remove(mxdPath)

        # rename the temp mxd so it matches the original mxdpath 
        os.rename(temp, mxdPath)
        del temp

        print "MXD saved successfully"
        txtFile.write("MXD saved successfully\n")

    # if mxd cannot be re-saved, list as an error in the text file report   
    except:
        print "\tERROR: mxd not updated, unable to save updates to mxd"
        txtFile.write("\tERROR: mxd not updated, unable to save updates to mxd\n")
    ''' Start the repath mxd process from spawned variables'''
    
    print "\nStarting: {}".format(mxdPath)
    txtFile.write("\nStarting: {}\n".format(mxdPath))
    
    # Before progressing on current mxd, tests its validity by attempting to open and look at layers within
    try:
        mxd = arcpy.mapping.MapDocument(mxdPath)
        arcpy.mapping.ListLayers(mxd)
        del mxd
    
    # if validation test fails, abort process and return to parent script, list error in text file report
    except:
        print "\t{} is not a valid mxd".format(mxdPath)
        txtFile.write("\t{} is not a valid mxd\n".format(mxdPath))
        sys.exit()
    
    # If mxd passes validation test, run the crawl mxd function using current mxd path as input  
    crawlmxd(mxdPath)
    
    # Spawned scirpt is complete, return to parent script
    print "\nMXD Repath Complete..."
    txtFile.write("\nMXD Repath Complete...\n")