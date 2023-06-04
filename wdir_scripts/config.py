import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.getcwd()))
import pythontools as pt
import numpy as np

base_dir = str(sys.argv[1])
working_dir = pt.setting_directory(base_dir, "workingDir")
input_dir = os.path.join(working_dir, "input")
bg_adjust_dir = os.path.join(working_dir, "bg_processed")
merge_channels_dir = os.path.join(working_dir, "mergedChannels")
dapi_seg_dir = pt.setting_directory(working_dir, "08_dapi_seg")
dapi_seg_input_dir = pt.setting_directory(dapi_seg_dir, "input_folder")
dapi_seg_output_dir = pt.setting_directory(dapi_seg_dir, "seg_output")
dapi_seg_binary_dir = pt.setting_directory(dapi_seg_dir, "dapi_seg_binary")
dapi_seg_binary_size_correct_dir = os.path.join(dapi_seg_dir, "binary_size_correct")
results_output_folder = pt.setting_directory(working_dir, "09_results_output")
# setting stepOne

info_txt_file = 'infos.txt'
metadata_file = 'metadata.csv'
metadata_file_path = os.path.join(working_dir, metadata_file)
dates_number = 20
input_dates = 'dates'
if os.path.exists(metadata_file_path):
    table_df = pd.read_csv(metadata_file_path)
    if not table_df.empty:
        filtered = table_df.filter(
            like=r'Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel'
                 r'|AdditionalDyeInformation|ShortName #')
        # Using numpy.unique() to unique values
        default_channels = list(np.unique(filtered.values.ravel()))
else:
    print("The metadata csv file could not be found")
    SystemExit(0)

standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["", "", "", "_"]

# settings stepTwo

dapi_str = "dapi"
stack_name = "Stack"

# settings stepTwo, stepThree,  stepFour, stepFive

tiff_ext = ".tif"
cropped_suffix = "_Cropped"
error_subfolder_name = "error_subfolder"
