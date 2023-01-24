import os
import sys

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

tiff_ext = ".tif"
cropped_suffix = "_Cropped"
error_subfolder_name = "error_subfolder"
