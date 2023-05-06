#!/usr/bin/env sh
clear
function pause(){
  read -s -n 1 -p "Press any key to continue . . ."
  echo ""
}

echo "MULTIPLEX IMAGE PREPROCESSING"
SCRIPTPATH=$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )
sub=${SCRIPTPATH:0:2}
sub=${sub^^}
sub="${sub/\//''}"
SCRIPTPATH=${sub}:${SCRIPTPATH:2}
SCRIPTPATH="${SCRIPTPATH//\\//}"
VAR1='base_dir="'"$SCRIPTPATH"'"'
VAR2='step="'"stitch"'"'
echo "RUNNING STEP 0 STITCHING"
$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
echo "RUNNING STEP 1 IMAGE PREPARATION"
source /c/Users/nko88/anaconda3/etc/profile.d/conda.sh
echo "PLEASE ADD CHANNEL MARKERS IN INFOS.TXT"
## Pause it ##
pause
conda activate multiplex
python image_preparation.py
VAR2='step="'"alignment"'"'
$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
echo "SEGMENTATION"
python preparation_dapi_seg.py
conda activate cellsegsegmenter
python dapi_seg_main.py
conda activate multiplex
python postprocessing_dapi_seg.py
VAR2='step="'"segmentation"'"'
$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
#CELLPROFILER ANALYSIS
#R STATISTICS


