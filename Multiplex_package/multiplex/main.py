# multiplex.main.py
import argparse
import os
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
    step = args.step[0]
    pipeline_steps_list = args.pipeline_steps
    dapiseg_steps_list = args.dapiseg_steps
    merge_channels_steps_list = args.merge_channels_steps
    subfolders_list = args.subfolders
    dapiseg_subfolders_list = args.dapiseg_subfolders
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
                ImagePreparation(input_dir, pcf.info_txt_file, pcf.input_dates, default_channels,

                                 pcf.standard_search_terms, pcf.standard_replacements, pcf.tiff_ext,
                                 pcf.dates_number, pcf.dapi_str).processing()

        else:
            logger.warning("The metadata csv file could not be found")
            SystemExit(0)
    elif step == dapiseg_steps_list[0]:
        from multiplex.preparation_dapi_seg import PreparationDapiSeg
        bg_adjust_dir = ht.correct_path(base_dir, subfolders_list[2])
        ht.setting_directory(base_dir, subfolders_list[4])
        dapi_seg_input_dir = ht.setting_directory(base_dir, dapiseg_subfolders_list[0])
        PreparationDapiSeg(bg_adjust_dir, dapi_seg_input_dir, pcf.dapi_str).process()
    elif step == dapiseg_steps_list[1]:
        from multiplex.dapi_seg_main import main
        dapi_seg_input_dir = ht.correct_path(base_dir, dapiseg_subfolders_list[0])
        dapi_seg_output_dir = ht.setting_directory(base_dir, dapiseg_subfolders_list[1])
        target = dapi_seg_input_dir
        output_path = dapi_seg_output_dir
        for folder in os.listdir(target):
            if os.path.isdir(ht.correct_path(target, folder)):
                logger.info("The following folder " + folder + " will be processed")
                directory_path = ht.correct_path(target, folder)
                filename = folder + pcf.tiff_ext
                nuclear_channel_name = filename
                autoboost_reference_image = filename
                channelfile = "channelNames_" + folder + ".txt"
                main(target, output_path, directory_path, nuclear_channel_name, autoboost_reference_image, channelfile)
    elif step == dapiseg_steps_list[2]:
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
        from multiplex.setting_merge_params import SettingParams
        input_dir = ht.correct_path(base_dir, subfolders_list[2])
        tiff_ext = pcf.tiff_ext
        dapi_str = pcf.dapi_str
        SettingParams(input_dir, tiff_ext, dapi_str).processing()


if __name__ == "__main__":
    start_time = time.time()
    processing()
    end_time = time.time()
    logger.info(f"Duration of the program execution:{ht.convert(end_time - start_time)}")
