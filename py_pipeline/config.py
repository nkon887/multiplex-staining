import os
import sys

sys.path.append(os.path.abspath(os.getcwd()))
import pythontools as pt

baseDir = pt.find_existing_location(["J:/", "D:/bigImg"])
workingDir = pt.setting_directory(baseDir, "workingDir")
inputDir = pt.setting_directory(workingDir, "01_input")
alignmentDirSV = pt.setting_directory(workingDir, "02_alignment_SV")
precrop_input_dir = pt.setting_directory(workingDir, "03_input_to_precrop")
stacksDir = pt.setting_directory(workingDir, "04_stacks")
croppedStacksDir = pt.setting_directory(workingDir, "05_cropped_input")
contrastBgAdjustDir = pt.setting_directory(workingDir, "06_bg_processed")
mergeChannelsDir = pt.setting_directory(workingDir, "07_mergedChannels")

# setting stepOne

info_txt_file = 'infos.txt'
table_dapi_title = "Dapi Channel"
table_dapi_entry = "0dapi"
channel_list = ["channel 1", "channel 2", "channel 3"]
dates_number = 20
dapi_channel = "c0"
input_dates = 'dates'
channel_patterns = ["c1", "c2", "c3"]
standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["", "", "", "_"]

# settings stepTwo

dapi_str = "dapi"
stack_name = "Stack"

# settings stepTwo, stepThree,  stepFour, stepFive

tiff_ext = ".tif"
cropped_suffix = "_Cropped"
error_subfolder_name = "error_subfolder"
