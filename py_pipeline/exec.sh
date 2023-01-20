#!/usr/bin/env sh
clear
echo "MULTIPLEX IMAGE PREPROCESSING"
#STITCHING
echo "RUNNING STEP 1 IMAGE PREPARATION"
python ImagePreparation.py
echo  "RUNNING STEP 2 ALIGNMENT"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run Alignment.py
echo  "RUNNING STEP 3 GENERATE HYPERSTACKS"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run HyperstackGeneration.py
echo  "RUNNING STEP 4 CROPPING TIFF IMAGES"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run CroppingForAlignment.py
echo  "RUNNING STEP 5 ALIGNMENT PRECROP"
"C:\Users\nko88\Desktop\Fiji.app\ImageJ-win64.exe" --ij2 --run Alignment.py
echo  "RUNNING STEP 6 CROPPING ALIGNED HYPERSTACKS"
C:/Program\ Files\ \(x86\)/fiji-win64/Fiji.app/ImageJ-win64.exe --ij2 --run CroppingAlignedHyperstacks.py
echo "RUNNING STEP 7 BACKGROUND ADJUSTMENT SUBSTRACTION ALIGNED STACKS"
C:/Program\ Files\ \(x86\)/fiji-win64/Fiji.app/ImageJ-win64.exe --ij2 --run BackgroundProcessing.py
echo "RUNNING STEP 8 MERGING OF CHANNELS"
C:/Program\ Files\ \(x86\)/fiji-win64/Fiji.app/ImageJ-win64.exe --ij2 --run MergingChannels.py
#contrast
#SEGMENTATION
#binary mask
#CELLPROFILER ANALYSIS
#R STATISTICS
exit 0
