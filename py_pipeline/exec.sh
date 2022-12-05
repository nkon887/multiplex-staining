#!/usr/bin/env sh
clear
echo "RUNNING STEP COPYING FILES"
python stepZero_copying_files.py
echo "Copying is successfully finished"
echo "RUNNING STEP 1 IMAGE PREPARATION"
python stepOne_imagePreparation.py
echo  "RUNNING STEP 2 GENERATE HYPERSTACKS"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepTwo_generate_hyperstacks.py
echo  "RUNNING STEP 3 CROPPING TIFF IMAGES"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepThree_cropping_tiff_images.py 'param="hyperstack"'
echo "RUNNING STEP 4 CONCATENATE"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepFour_concatenate.py
echo "RUNNING STEP 5 ALIGN CONCATENATES"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepFive_align_concatenates.py
echo  "RUNNING STEP 3 CROPPING TIFF IMAGES"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepThree_cropping_tiff_images.py 'param="alignedStack"'
echo "RUNNING STEP 6 BACKGROUND ADJUSTMENT SUBSTRACTION ALIGNED STACKS"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepSix_background_adjustment_substraction_aligned_stacks.py
echo "RUNNING STEP 7 MERGING OF CHANNELS"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepSeven_channels_merging.py
exit 0