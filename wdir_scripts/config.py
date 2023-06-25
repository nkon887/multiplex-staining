import os
import helpertools as ht

info_txt_file = 'infos.txt'
metadata_file = 'metadata.csv'
dates_number = 20
input_dates = 'dates'
standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["" if i < (len(standard_search_terms) - 2) else "_" for i in range(len(standard_search_terms))]
dapi_str = "dapi"
stack_name = "Stack"
tiff_ext = ".tif"
main_work_dir = "workingDir"
subfolders_list = [ht.correct_path(main_work_dir, str(i + 1).zfill(2) + "_" + subfolder) for i, subfolder in
                   enumerate(["input", "alignment", "bg_processed", "mergedChannels", "dapi_seg", "results_output"])]
dapiseg_subfolder_list = [ht.correct_path(subfolders_list[4], str(i + 1).zfill(2) + "_" + subfolder) for i, subfolder in
                          enumerate(["input_folder", "seg_output", "dapi_seg_binary", "binary_size_correct"])]
realignment_subfolder_list = [
    ht.correct_path(main_work_dir, str(2).zfill(2) + "_" + str(i + 1).zfill(2) + "_" + subfolder) for i, subfolder in
    enumerate(["input_to_precrop", "stacks", "cropped_input"])]

pipeline_params = {("STITCHING", "DATACHECK", "", subfolders_list[0]): [
    {"package": "fiji", "env": "", "step": "STITCHING"}],
    ("DATACHECK", "ALIGNMENT", subfolders_list[0], subfolders_list[0]): [
        {"package": "python", "env": "multiplex", "step": "DATACHECK"}],
    ("ALIGNMENT", "REALIGNMENT,CROPPING", subfolders_list[0],
     realignment_subfolder_list[0] + "," + subfolders_list[1]): [
        {"package": "fiji", "env": "", "step": "ALIGNMENT"}],
    ("REALIGNMENT", "CROPPING", realignment_subfolder_list[0] + ","
     + subfolders_list[1], subfolders_list[1]): [
        {"package": "fiji", "env": "", "step": "REALIGNMENT"}],
    ("CROPPING", "BACKGROUNDADJUSTMENT", subfolders_list[1], subfolders_list[1]): [
        {"package": "fiji", "env": "", "step": "CROPPING"}],
    ("BACKGROUNDADJUSTMENT", "MERGING CHANNELS,DAPI SEGMENTATION,OUTPUT",
     subfolders_list[1],
     subfolders_list[2]): [
        {"package": "fiji", "env": "", "step": "BACKGROUNDADJUSTMENT"}],
    (
        "MERGING CHANNELS", "", subfolders_list[2],
        subfolders_list[3]): [
        {"package": "fiji", "env": "", "step": "MERGING CHANNELS"}],
    ("DAPI SEGMENTATION", "", subfolders_list[2], dapiseg_subfolder_list[3]): [
        {"package": "python", "env": "multiplex",
         "step": "preparation_dapiSeg"},
        {"package": "python", "env": "cellsegsegmenter",
         "step": "main_dapiSeg"},
        {"package": "python", "env": "multiplex",
         "step": "postprocessing_dapiSeg"},
        {"package": "fiji", "env": "", "step": "DAPI SEGMENTATION"}],
    ("OUTPUT", "",
     subfolders_list[2],
     subfolders_list[5]): [
        {"package": "python", "env": "multiplex", "step": "OUTPUT"}]
}
