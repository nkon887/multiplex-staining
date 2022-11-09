#!/usr/bin/env sh
clear
echo "Running the step copying_files "
python copying_files.py
echo "Copying is successfully finished"
echo "Running stepOne_imagePreparation"
python stepOne_imagePreparation.py
echo  "Running stepTwo_generate_hyperstacks"
C:/Users/nko88/Desktop/fiji-win64/Fiji.app/ImageJ-win64.exe -macro stepTwo_generate_hyperstacks.py
exit 0