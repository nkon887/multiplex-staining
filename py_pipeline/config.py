import os
import sys

sys.path.append(os.path.abspath(os.getcwd()))
import pythontools as pt

base_dir = pt.find_existing_location(["J:/", "D:/bigImg"])
working_dir = pt.setting_directory(base_dir, "workingDir")
stitch_input_dir = pt.setting_directory(working_dir, "00_raw_input")
input_dir = pt.setting_directory(working_dir, "01_input")
alignment_dir = pt.setting_directory(working_dir, "02_alignment_SV")
precrop_input_dir = pt.setting_directory(working_dir, "03_input_to_precrop")
stacks_dir = pt.setting_directory(working_dir, "04_stacks")
cropped_stacks_dir = pt.setting_directory(working_dir, "05_cropped_input")
bg_adjust_dir = pt.setting_directory(working_dir, "06_bg_processed")
merge_channels_dir = pt.setting_directory(working_dir, "07_mergedChannels")

# setting stepOne

info_txt_file = 'infos.txt'
channel_list = ["channel 0", "channel 1", "channel 2", "channel 3"]
dates_number = 20
input_dates = 'dates'
channel_patterns = ["c0", "c1", "c2", "c3"]
standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["", "", "", "_"]

# settings stepTwo

dapi_str = "dapi"
stack_name = "Stack"

# settings stepTwo, stepThree,  stepFour, stepFive
czi_ext = ".czi"
tiff_ext = ".tif"
cropped_suffix = "_Cropped"
error_subfolder_name = "error_subfolder"
