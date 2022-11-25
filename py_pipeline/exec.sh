#!/usr/bin/env sh
clear
echo "Running the step copying_files "
python copying_files.py
echo "Copying is successfully finished"
echo "Running stepOne_imagePreparation"
python stepOne_imagePreparation.py
echo  "Running stepTwo_generate_hyperstacks"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe -macro stepTwo_generate_hyperstacks.py
echo  "Running stepThree_cropping_tiff_images"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepThree_cropping_tiff_images.py 'param="hyperstack"'
echo "Running stepFour_concatenate"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe -macro stepFour_concatenate.py
echo "Running stepFive_aligb_concatenates"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe -macro stepFive_align_concatenates.py
echo  "Running stepThree_cropping_tiff_images"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe --ij2 --run stepThree_cropping_tiff_images.py 'param="alignedStack"'
echo "Running stepSix_background_adjustment_substraction_aligned_stacks"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe -macro stepSix_background_adjustment_substraction_aligned_stacks.py
echo "Running stepSeven_merging_of_channels"
C:/Users/nko88/Desktop/Fiji.app/ImageJ-win64.exe -macro stepSeven_channels_merging.py
exit 0