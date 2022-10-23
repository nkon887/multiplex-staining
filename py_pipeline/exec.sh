#!/usr/bin/env sh
clear
echo "Running Step 01_image_preparation"
python 01_image_preparation.py
echo  "Running Step 02_generate_hyperstacks"
C:/Users/nko88/Desktop/fiji-win64/Fiji.app/ImageJ-win64.exe -macro 02_generate_hyperstacks.py
exit 0