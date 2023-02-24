#!/usr/bin/env sh
clear
echo "MULTIPLEX IMAGE PREPROCESSING"
#STITCHING
echo "RUNNING STEP 1 IMAGE PREPARATION"
python image_preparation.py
SCRIPTPATH=$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )
sub=${SCRIPTPATH:0:2}
sub=${sub^^}
sub="${sub/\//''}"
SCRIPTPATH=${sub}:${SCRIPTPATH:2}
SCRIPTPATH="${SCRIPTPATH//\\//}"
VAR='base_dir="'"$SCRIPTPATH"'"'
$FIJIPATH --ij2 --run macro.py $VAR
python preparation_dapi_seg.py
#SEGMENTATION
#binary mask
#CELLPROFILER ANALYSIS
#R STATISTICS

