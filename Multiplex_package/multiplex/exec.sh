#!/usr/bin/env sh
clear
function pause(){
  read -s -n 1 -p "Press any key to continue . . ."
  echo ""
}

SCRIPTPATH=$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )
sub=${SCRIPTPATH:0:2}
sub=${sub^^}
sub="${sub/\//''}"
SCRIPTPATH=${sub}:${SCRIPTPATH:2}
SCRIPTPATH="${SCRIPTPATH//\\//}"
VAR1='base_dir="'"$SCRIPTPATH"'"'

echo "MULTIPLEX IMAGE PREPROCESSING"
step=$1;
echo "Step: ${step}";
VAR2='step="'"${step}"'"'
echo "RUNNING STEP ${step}"
$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2

#VAR2='step="'"STITCHING"'"'
#echo "RUNNING STEP 0 STITCHING"
#$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
#echo "RUNNING STEP 1 IMAGE PREPARATION"
#source /c/Users/naam11/Anaconda3/etc/profile.d/conda.sh
#echo "PLEASE ADD CHANNEL MARKERS IN INFOS.TXT"
## Pause it ##
#pause
#conda env create -f env_multiplex.yml
#conda activate multiplex
#python image_preparation.py
#VAR2='step="'"ALIGNMENT"'"'
#$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
#echo "SEGMENTATION"
#python preparation_dapi_seg.py
#conda env create -f env_cellsegsegmenter.yml
#conda activate cellsegsegmenter
#python dapi_seg_main.py
#conda activate multiplex
#python postprocessing_dapi_seg.py
#VAR2='step="'"DAPISEG_RESIZER"'"'
#$FIJIPATH --ij2 --run macro.py $VAR1,$VAR2
#CELLPROFILER ANALYSIS
#R STATISTICS