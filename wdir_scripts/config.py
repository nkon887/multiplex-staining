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
pipeline_steps = ["", "STITCHING", "DATACHECK", "ALIGNMENT", "REALIGNMENT", "CROPPING", "BACKGROUNDADJUSTMENT",
                  "MERGING CHANNELS", "DAPI SEGMENTATION", "OUTPUT"]
dapiseg_steps = ["preparation_dapiSeg", "main_dapiSeg", "postprocessing_dapiSeg"]
command_arguments = ["package", "env", "step"]
packages = ["fiji", "python"]
envs = {"": "", "multiplex": "env_multiplex.yml", "cellsegsegmenter": "env_cellsegsegmenter.yml"}
pipeline_params = {
    (pipeline_steps[1], pipeline_steps[2], "", subfolders_list[0]): [
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[1]}],
    (pipeline_steps[2], pipeline_steps[3], subfolders_list[0], subfolders_list[0]): [
        {command_arguments[0]: packages[1], command_arguments[1]: list(envs)[1], command_arguments[2]: pipeline_steps[2]}],
    (pipeline_steps[3], pipeline_steps[4] + "," + pipeline_steps[5], subfolders_list[0],
     realignment_subfolder_list[0] + "," + subfolders_list[1]): [
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[3]}],
    (pipeline_steps[4], pipeline_steps[5], realignment_subfolder_list[0] + ","
     + subfolders_list[1], subfolders_list[1]): [
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[4]}],
    (pipeline_steps[5], pipeline_steps[6], subfolders_list[1], subfolders_list[1]): [
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[5]}],
    (pipeline_steps[6], pipeline_steps[7] + "," + pipeline_steps[8] + "," + pipeline_steps[9],
     subfolders_list[1], subfolders_list[2]): [
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[6]}],
    (pipeline_steps[7], pipeline_steps[0], subfolders_list[2], subfolders_list[3]): [
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[7]}],
    (pipeline_steps[8], pipeline_steps[0], subfolders_list[2], dapiseg_subfolder_list[3]): [
        {command_arguments[0]: packages[1], command_arguments[1]: list(envs)[1], command_arguments[2]: dapiseg_steps[0]},
        {command_arguments[0]: packages[1], command_arguments[1]: list(envs)[2], command_arguments[2]: dapiseg_steps[1]},
        {command_arguments[0]: packages[1], command_arguments[1]: list(envs)[1], command_arguments[2]: dapiseg_steps[2]},
        {command_arguments[0]: packages[0], command_arguments[1]: list(envs)[0], command_arguments[2]: pipeline_steps[8]}],
    (pipeline_steps[9], pipeline_steps[0], subfolders_list[2], subfolders_list[5]): [
        {command_arguments[0]: packages[1], command_arguments[1]: list(envs)[1], command_arguments[2]: pipeline_steps[9]}]
}
