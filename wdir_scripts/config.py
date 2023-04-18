import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.getcwd()))
import pythontools as pt
import numpy as np
base_dir = os.getcwd()
working_dir = pt.setting_directory(base_dir, "workingDir")
stitch_input_dir = pt.setting_directory(working_dir, "00_raw_input")
input_dir = pt.setting_directory(working_dir, "01_input")
alignment_dir = pt.setting_directory(working_dir, "02_alignment_SV")
precrop_input_dir = pt.setting_directory(working_dir, "03_input_to_precrop")
stacks_dir = pt.setting_directory(working_dir, "04_stacks")
cropped_stacks_dir = pt.setting_directory(working_dir, "05_cropped_input")
bg_adjust_dir = pt.setting_directory(working_dir, "06_bg_processed")
merge_channels_dir = pt.setting_directory(working_dir, "07_mergedChannels")
dapi_seg_input_dir = pt.setting_directory(working_dir, "08_dapi_input_folder")

# setting stepOne

info_txt_file = 'infos.txt'
metadata_file = 'metadata.csv'
metadata_file_path = os.path.join(stitch_input_dir, metadata_file)
#channel_list = ["channel 0", "channel 1", "channel 2", "channel 3"]
dates_number = 20
input_dates = 'dates'
if os.path.exists(metadata_file_path):
    table_df = pd.read_csv(metadata_file_path)
    if table_df:
        filtered = table_df.filter(like=r'Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #')
        # Using numpy.unique() to unique values
        default_channels=list(np.unique(filtered.values.ravel()))
        print(default_channels)
#channel_patterns = default_channels
#channel_patterns = ["c0", "c1", "c2", "c3"]
standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["", "", "", "_"]

# settings stepTwo

dapi_str = "dapi"
stack_name = "Stack"

# settings stepTwo, stepThree,  stepFour, stepFive

tiff_ext = ".tif"
cropped_suffix = "_Cropped"
error_subfolder_name = "error_subfolder"
