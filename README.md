# repathMXDs

This tool repaths data sources for layers within MXDs.

The tool consists of a set of Pyhton scripts and corresponding ArcToolbox, with user interface, which allow the user to update the data source paths for a set of mxd files.

The user may input a single data source path to be replaced within the mxd files, and a single, equivilant data source path where each layer will be sourced to.

Alternatively a CSV input option is available where the user can create an old-to-new data source path map csv file which lists the old/current top level directories in column A, and the new equivilant data source paths in column B.
