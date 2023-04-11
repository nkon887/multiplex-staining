#!/usr/bin/env sh
clear
echo "MULTIPLEX IMAGE PREPROCESSING"
SCRIPTPATH=$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )
sub=${SCRIPTPATH:0:2}
sub=${sub^^}
sub="${sub/\//''}"
SCRIPTPATH=${sub}:${SCRIPTPATH:2}
SCRIPTPATH="${SCRIPTPATH//\\//}"
VAR1='base_dir="'"$SCRIPTPATH"'"'
VAR2='stitch="'"True"'"'
echo "RUNNING STEP 0 STITCHING"
$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
echo "RUNNING STEP 1 IMAGE PREPARATION"
python image_preparation.py
VAR2='stitch="'"False"'"'
$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
#contrast
#SEGMENTATION
#binary mask
#CELLPROFILER ANALYSIS
#R STATISTICS


