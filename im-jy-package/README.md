# multiplex-staining Preprocessing of images

## Description
This pipeline enables the user to process and prepare multiplex staining
microscopy images for further cell population analysis
It works for the tiff images

3, 4 channel images per date corresponding to one experiment are handled
individually. As the position of the region of interest changes from date
to date, channel images are treated as a stack. It is possible to process
more than one stack with one run.

## Requirements

1. Python > 3.3
2. Fiji + Turboreg + Hyperstackreg (Jython)
3. Git Bash

## Set-Up

+ configure the config.py file
  
        
[
       "J:/", "I:/master/Test"
  ]
  


+ to run the pipeline type /bin/sh exec.sh in GitBash. Open GitBash.
Navigate to the folder with the pipeline scripts using cd
+ the execution creates a directory-structure for the processed image
files
        workingDir/
                  /01_input
                  /02_hyperstacks
                  /03_concatenates
                  /04_alignment
                  /05_contrastBG
                  /06_mergedChannels
+ if errors are occurring while the execution, there are outputs on the 
console of FiJi and in GitBash 
+ if the execution is done completely, there is also an output on the FiJi console