# multiplex.main.py
import argparse
import gc
import os
import subprocess
import weakref

import pandas as pd
import time
import multiplex.helpertools as ht
from multiplex.ppconfig import PIPELINEConfig
import multiplex.setup_logger
import logging

# multiplex.main.py creates its own logger, as a sub logger to 'multiplex'
logger = logging.getLogger('multiplex.main')


def processing():
    CLI = argparse.ArgumentParser()
    CLI.add_argument(
        "--target",
        nargs=1,
        type=str,
        default=""
    )
    CLI.add_argument(
        "--working_dir",
        nargs=1,
        type=str,
        default=""
    )
    CLI.add_argument(
        "--env",
        nargs=1,
        type=str,
        default=""
    )
    CLI.add_argument(
        "--step",
        nargs=1,
        type=str,
        default=""
    )
    CLI.add_argument(
        "--pipeline_steps",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--dapiseg_steps",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--merge_channels_steps",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--bg_steps",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--cropping_exp_steps",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--fast_button_step",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--subfolders",
        nargs="*",
        type=str,
        default=[]
    )
    CLI.add_argument(
        "--dapiseg_subfolders",
        nargs="*",
        type=str,
        default=[]
    )

    args = CLI.parse_args()
    base_dir = args.target[0]
    working_dir = args.working_dir[0]
    env = args.env[0]
    step = args.step[0]
    pipeline_steps_list = args.pipeline_steps
    dapiseg_steps_list = args.dapiseg_steps
    merge_channels_steps_list = args.merge_channels_steps
    bg_steps_list = args.bg_steps
    cropping_exp_steps_list = args.cropping_exp_steps
    subfolders_list = args.subfolders
    dapiseg_subfolders_list = args.dapiseg_subfolders
    fast_button_step_list = args.fast_button_step
    logger.info(step.upper())
    work_dir = ht.correct_path(base_dir, working_dir)
    pcf = PIPELINEConfig()
    # setting stepOne
    if step == pipeline_steps_list[1]:
        from multiplex.image_preparation import ImagePreparation
        input_dir = ht.correct_path(base_dir, subfolders_list[0])
        metadata_file_path = ht.correct_path(work_dir, pcf.metadata_file)
        if os.path.exists(metadata_file_path):
            table_df = pd.read_csv(metadata_file_path)
            if not table_df.empty:
                filtered = table_df.filter(
                    like=r'DefaultChannel #')
                # Using numpy.unique() to unique values
                default_channels_values = list(set(list(filtered.values.ravel())))
                default_channels = [x for x in default_channels_values if str(x) != 'nan']
                ImagePreparation(work_dir, input_dir, pcf.info_txt_file, pcf.metadata_file, pcf.input_dates,
                                 default_channels,

                                 pcf.standard_search_terms, pcf.standard_replacements, pcf.tiff_ext,
                                 pcf.dates_number, pcf.dapi_str, pcf.csv_ext).processing()

        else:
            logger.error("The metadata csv file could not be found")
            SystemExit(0)
    elif step == dapiseg_steps_list[0]:
        from multiplex.setting_dapiseg_params import SettingDapisegParams
        bg_adjust_dir = ht.correct_path(base_dir, subfolders_list[2])
        ht.setting_directory(base_dir, subfolders_list[4])
        metadata_csv_file = pcf.metadata_file
        csv_ext = pcf.csv_ext
        SettingDapisegParams(bg_adjust_dir, pcf.tiff_ext, pcf.dapi_str, metadata_csv_file, work_dir,
                             csv_ext).processing()
    elif step == dapiseg_steps_list[1]:
        from multiplex.preparation_dapi_seg import PreparationDapiSeg
        bg_adjust_dir = ht.correct_path(base_dir, subfolders_list[2])
        ht.setting_directory(base_dir, subfolders_list[4])
        dapi_seg_input_dir = ht.setting_directory(base_dir, dapiseg_subfolders_list[0])
        PreparationDapiSeg(bg_adjust_dir, dapi_seg_input_dir, pcf.dapi_str, pcf.tiff_ext, work_dir).process()
    #elif step == dapiseg_steps_list[2]:
    #    # import tracemalloc
    #    # tracemalloc.start()
    #    # from multiplex.dapi_seg_main import DapiSeg
    #    dapi_seg_input_dir = ht.correct_path(base_dir, dapiseg_subfolders_list[0])
    #    dapi_seg_output_dir = ht.setting_directory(base_dir, dapiseg_subfolders_list[1])
    #    for folder in os.listdir(dapi_seg_input_dir):
    #        if os.path.isdir(ht.correct_path(dapi_seg_input_dir, folder)):
    #            logger.info("The following folder " + folder + " will be processed")
    #            root = os.path.dirname(os.path.realpath(__file__))
    #            dapi_main_py_PATH = os.path.join(root, 'dapi_seg_main.py')
    #            result = subprocess.run(
    #                f"conda activate {env} && python {dapi_main_py_PATH}  --input {dapi_seg_input_dir} --out {dapi_seg_output_dir} --folder {folder}", shell=True, check=True)
    #            print(result.stdout)
    #            print(result.stderr)

        # obj = DapiSeg(dapi_seg_input_dir, dapi_seg_output_dir)
        # obj_ref = weakref.ref(obj)
        # obj_ref().process()
        # snapshot = tracemalloc.take_snapshot()
        # top_stats = snapshot.statistics('lineno')
        # for stat in top_stats[:10]:
        #    logger.info(stat)
    #    logger.info("Segmentation Completed")
    elif step == dapiseg_steps_list[3]:
        from multiplex.postprocessing_dapi_seg import PostProcessingDapiSeg
        dapi_seg_output_dir = ht.correct_path(base_dir, dapiseg_subfolders_list[1])
        dapi_seg_binary_dir = ht.setting_directory(base_dir, dapiseg_subfolders_list[2])
        PostProcessingDapiSeg(ht.correct_path(dapi_seg_output_dir, "visual_output"),
                              ht.correct_path(dapi_seg_binary_dir),
                              pcf.tiff_ext).process()
    elif step == pipeline_steps_list[8]:
        from multiplex.results_output import ResultsOutput
        bg_adjust_dir = ht.correct_path(base_dir, subfolders_list[2])
        merge_channels_dir = ht.correct_path(base_dir, subfolders_list[3])
        dapi_seg_binary_size_correct_dir = ht.correct_path(base_dir, dapiseg_subfolders_list[3])
        results_output_folder = ht.setting_directory(base_dir, subfolders_list[5])
        # Calling the ResultsOutput class function
        ResultsOutput(work_dir, bg_adjust_dir, merge_channels_dir, dapi_seg_binary_size_correct_dir,
                      results_output_folder).process()
    elif step == merge_channels_steps_list[0]:
        from multiplex.setting_merge_params import SettingMergeParams
        input_dir = ht.correct_path(base_dir, subfolders_list[2])
        tiff_ext = pcf.tiff_ext
        dapi_str = pcf.dapi_str
        metadata_csv_file = pcf.metadata_file
        csv_ext = pcf.csv_ext
        SettingMergeParams(input_dir, tiff_ext, dapi_str, metadata_csv_file, work_dir, csv_ext).processing()
    elif step == bg_steps_list[0]:
        from multiplex.setting_bg_params import SettingBGParams
        input_dir = ht.correct_path(base_dir, subfolders_list[1])
        tiff_ext = pcf.tiff_ext
        dapi_str = pcf.dapi_str
        metadata_csv_file = pcf.metadata_file
        csv_ext = pcf.csv_ext
        SettingBGParams(input_dir, tiff_ext, dapi_str, metadata_csv_file, work_dir, csv_ext).processing()
    elif step == cropping_exp_steps_list[0]:
        from multiplex.cropping_before_after_alignment_experimental_extracting_coords import \
            Cropping_Before_After_Alignment_Experimental_Extracting_Coords
        pre_input_dir = ht.correct_path(base_dir, subfolders_list[0])
        input_dir = ht.correct_path(base_dir, subfolders_list[1])
        target_dir = ht.correct_path(base_dir, subfolders_list[1])
        error_subfolder_name = "error_subfolder"
        tiff_ext = pcf.tiff_ext
        cropped_suffix = "_Cropped"
        Cropping_Before_After_Alignment_Experimental_Extracting_Coords(pre_input_dir, input_dir, target_dir,
                                                                       error_subfolder_name, tiff_ext,
                                                                   cropped_suffix).processing_after_alignment()
    elif step == cropping_exp_steps_list[1]:
        from multiplex.cropping_before_after_alignment_experimental_with_direct_automatic import \
            Cropping_Before_After_Alignment_Experimental_With_Direct_Automatic_Cut
        pre_input_dir = ht.correct_path(base_dir, subfolders_list[0])
        input_dir = ht.correct_path(base_dir, subfolders_list[1])
        target_dir = ht.correct_path(base_dir, subfolders_list[1])
        error_subfolder_name = "error_subfolder"
        tiff_ext = pcf.tiff_ext
        cropped_suffix = "_Cropped"
        Cropping_Before_After_Alignment_Experimental_With_Direct_Automatic_Cut(pre_input_dir, input_dir, target_dir,
                                                                       error_subfolder_name, tiff_ext,
                                                                   cropped_suffix).processing_after_alignment()

    elif step == fast_button_step_list[0]:
        from multiplex.parameters_for_bg_merge_dapiseg import SettingParams
        bg_input_dir = ht.correct_path(base_dir, subfolders_list[1])
        txt_dir = ht.correct_path(base_dir, subfolders_list[0])
        infos_txt = pcf.info_txt_file
        metadata_csv_file = pcf.metadata_file
        input_dir = ht.correct_path(base_dir, subfolders_list[2])
        tiff_ext = pcf.tiff_ext
        dapi_str = pcf.dapi_str
        SettingParams(bg_input_dir, txt_dir, infos_txt, input_dir, tiff_ext, dapi_str, metadata_csv_file,
                      work_dir, pcf.csv_ext).processing()


if __name__ == "__main__":
    start_time = time.time()
    processing()
    end_time = time.time()
    logger.info(f"Duration of the program execution:{ht.convert(end_time - start_time)}")
