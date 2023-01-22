#!/usr/bin/env sh
clear
echo "MULTIPLEX IMAGE PREPROCESSING"
#STITCHING
echo "RUNNING STEP 1 IMAGE PREPARATION"
python image_preparation.py
echo  "RUNNING STEP 2 ALIGNMENT"
$FIJIPATH --ij2 --run alignment.py
echo  "RUNNING STEP 3 HYPERSTACK GENERATION OF NOT ALIGNED DATA"
$FIJIPATH --ij2 --run hyperstack_generation.py
echo  "RUNNING STEP 4 CROPPING TIFF IMAGES"
$FIJIPATH --ij2 --run cropping_for_alignment.py
echo  "RUNNING STEP 5 ALIGNMENT PRECROP"
$FIJIPATH --ij2 --run alignment.py
echo  "RUNNING STEP 6 CROPPING ALIGNED HYPERSTACKS"
$FIJIPATH --ij2 --run cropping_aligned_hyperstacks.py
echo "RUNNING STEP 7 BACKGROUND ADJUSTMENT SUBSTRACTION ALIGNED STACKS"
$FIJIPATH --ij2 --run background_processing.py
echo "RUNNING STEP 8 MERGING OF CHANNELS"
$FIJIPATH --ij2 --run merging_channels.py
#contrast
#SEGMENTATION
#binary mask
#CELLPROFILER ANALYSIS
#R STATISTICS
exit 0
