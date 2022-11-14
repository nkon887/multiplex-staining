#!/usr/bin/env sh
clear
echo "Running the step copying_files "
python copying_files.py
echo "Copying is successfully finished"
echo "Running stepOne_imagePreparation"
python stepOne_imagePreparation.py
echo  "Running stepTwo_generate_hyperstacks"
C:/Users/nko88/Desktop/fiji-win64/Fiji.app/ImageJ-win64.exe -macro stepTwo_generate_hyperstacks.py
echo  "Running stepThree_cropping_hyperstacks"
C:/Users/nko88/Desktop/fiji-win64/Fiji.app/ImageJ-win64.exe -macro stepThree_cropping_hyperstacks.py
echo "Running stepFour_concatenate"
C:/Users/nko88/Desktop/fiji-win64/Fiji.app/ImageJ-win64.exe -macro stepFour_concatenate.py
echo "Running stepFive_aligb_concatenates"
C:/Users/nko88/Desktop/fiji-win64/Fiji.app/ImageJ-win64.exe -macro stepFive_aligb_concatenates.py
exit 0