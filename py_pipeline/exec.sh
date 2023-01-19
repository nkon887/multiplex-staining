#!/usr/bin/env sh
clear
echo "MULTIPLEX IMAGE PREPROCESSING"
#STITCHING
echo "RUNNING STEP 1 IMAGE PREPARATION"
python ImagePreparation.py
echo  "RUNNING STEP 2 ALIGNMENT"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run Alignment.py
echo  "RUNNING STEP 3 GENERATE HYPERSTACKS"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run stepThree_generate_hyperstacks.py
echo  "RUNNING STEP 4 CROPPING TIFF IMAGES"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run stepFour_cropping.py
echo  "RUNNING STEP 5 ALIGNMENT PRECROP"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run stepTwo_sv_alignment.py
echo  "RUNNING STEP 6 CROPPING ALIGNED HYPERSTACKS"
C:/Program\ Files\ \(x86\)/fiji-win64/Fiji.app/ImageJ-win64.exe --ij2 --run stepFive_cropping_aligned_hyperstacks.py
echo "RUNNING STEP 7 BACKGROUND ADJUSTMENT SUBSTRACTION ALIGNED STACKS"
C:/Program\ Files\ \(x86\)/fiji-win64/Fiji.app/ImageJ-win64.exe --ij2 --run stepSeven_background_adjustment_substraction_aligned_stacks.py
echo "RUNNING STEP 8 MERGING OF CHANNELS"
C:/Program\ Files\ \(x86\)/fiji-win64/Fiji.app/ImageJ-win64.exe --ij2 --run stepEight_channels_merging.py
#contrast
#SEGMENTATION
#binary mask
#CELLPROFILER ANALYSIS
#R STATISTICS
exit 0
