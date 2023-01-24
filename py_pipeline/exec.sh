#!/usr/bin/env sh
clear
echo "MULTIPLEX IMAGE PREPROCESSING"
#STITCHING
echo "RUNNING STEP 1 IMAGE PREPARATION"
python image_preparation.py
$FIJIPATH --ij2 --run main.py
#contrast
#SEGMENTATION
#binary mask
#CELLPROFILER ANALYSIS
#R STATISTICS
exit 0
