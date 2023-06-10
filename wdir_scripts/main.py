# main.py

import os
import sys
import pandas as pd
import time

from wdir_scripts.results_output import ResultsOutput

import helpertools as ht
import numpy as np
import config
import setup_logger
import logging

# main.py creates its own logger, as a sub logger to 'pipelineGUI'
logger = logging.getLogger('pipelineGUI.main')


def processing(args):
    base_dir, step = args[1:]
    logger.info(step.upper())
    working_dir = ht.correct_path(base_dir, "workingDir")
    # setting stepOne
    if step == "imageCheck":
        from image_preparation import ImagePreparation
        input_dir = ht.correct_path(working_dir, "01_input")
        metadata_file_path = ht.correct_path(working_dir, config.metadata_file)
        if os.path.exists(metadata_file_path):
            table_df = pd.read_csv(metadata_file_path)
            if not table_df.empty:
                filtered = table_df.filter(
                    like=r'Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel'
                         r'|AdditionalDyeInformation|ShortName #')
                # Using numpy.unique() to unique values
                default_channels = list(np.unique(filtered.values.ravel()))
                ImagePreparation(input_dir, config.info_txt_file, config.input_dates, default_channels,
                                 config.standard_search_terms, config.standard_replacements, config.tiff_ext,
                                 config.dates_number, config.dapi_str).processing()
        else:
            logger.warning("The metadata csv file could not be found")
            SystemExit(0)

    elif step == "preparation_dapiSeg":
        from preparation_dapi_seg import PreparationDapiSeg
        bg_adjust_dir = ht.correct_path(working_dir, "03_bg_processed")
        dapi_seg_dir = ht.setting_directory(working_dir, "05_dapi_seg")
        dapi_seg_input_dir = ht.setting_directory(dapi_seg_dir, "01_input_folder")
        PreparationDapiSeg(bg_adjust_dir, dapi_seg_input_dir, config.dapi_str).process()
    elif step == "main_dapiSeg":
        from dapi_seg_main import main
        dapi_seg_dir = ht.correct_path(working_dir, "05_dapi_seg")
        dapi_seg_input_dir = ht.correct_path(dapi_seg_dir, "01_input_folder")
        dapi_seg_output_dir = ht.setting_directory(dapi_seg_dir, "02_seg_output")
        target = dapi_seg_input_dir
        output_path = dapi_seg_output_dir
        for folder in os.listdir(target):
            if os.path.isdir(ht.correct_path(target, folder)):
                logger.info("The following folder " + folder + " will be processed")
                directory_path = ht.correct_path(target, folder)
                filename = folder + config.tiff_ext
                nuclear_channel_name = filename
                autoboost_reference_image = filename
                channelfile = "channelNames_" + folder + ".txt"
                main(target, output_path, directory_path, nuclear_channel_name, autoboost_reference_image, channelfile)
    elif step == "postprocessing_dapiSeg":
        from postprocessing_dapi_seg import PostProcessingDapiSeg
        dapi_seg_dir = ht.correct_path(working_dir, "05_dapi_seg")
        dapi_seg_output_dir = ht.correct_path(dapi_seg_dir, "02_seg_output")
        dapi_seg_binary_dir = ht.setting_directory(dapi_seg_dir, "03_dapi_seg_binary")
        PostProcessingDapiSeg(ht.correct_path(dapi_seg_output_dir, "visual_output"), ht.correct_path(dapi_seg_binary_dir),
                              config.tiff_ext).process()
    elif step == "resultsOutput":
        bg_adjust_dir = ht.correct_path(working_dir, "03_bg_processed")
        merge_channels_dir = ht.correct_path(working_dir, "04_mergedChannels")
        dapi_seg_dir = ht.correct_path(working_dir, "05_dapi_seg")
        dapi_seg_binary_size_correct_dir = ht.correct_path(dapi_seg_dir, "04_binary_size_correct")
        results_output_folder = ht.setting_directory(working_dir, "06_results_output")
        # Calling the ResultsOutput class function
        ResultsOutput(working_dir, bg_adjust_dir, merge_channels_dir, dapi_seg_binary_size_correct_dir,
                      results_output_folder).process()


if __name__ == "__main__":
    start_time = time.time()
    processing(sys.argv)
    end_time = time.time()
    logger.info(f"Duration of the program execution:{ht.convert(end_time - start_time)}")
