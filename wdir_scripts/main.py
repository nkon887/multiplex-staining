import os
import sys
import pandas as pd
import time

from wdir_scripts.results_output import ResultsOutput

sys.path.append(os.path.abspath(os.getcwd()))
import pythontools as ht
import numpy as np
import config





def processing(args):
    base_dir, step = args[1:]
    print(step.upper())
    working_dir = os.path.join(base_dir, "workingDir")
    # setting stepOne
    if step == "imageCheck":
        from image_preparation import ImagePreparation
        input_dir = os.path.join(working_dir, "input")
        metadata_file_path = os.path.join(working_dir, config.metadata_file)
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
            print("The metadata csv file could not be found")
            SystemExit(0)

    elif step == "preparation_dapiSeg":
        from preparation_dapi_seg import PreparationDapiSeg
        bg_adjust_dir = os.path.join(working_dir, "bg_processed")
        dapi_seg_dir = ht.setting_directory(working_dir, "dapi_seg")
        dapi_seg_input_dir = ht.setting_directory(dapi_seg_dir, "input_folder")
        PreparationDapiSeg(bg_adjust_dir, dapi_seg_input_dir, config.dapi_str).process()
    elif step == "main_dapiSeg":
        from dapi_seg_main import main
        dapi_seg_dir = os.path.join(working_dir, "dapi_seg")
        dapi_seg_input_dir = os.path.join(dapi_seg_dir, "input_folder")
        dapi_seg_output_dir = ht.setting_directory(dapi_seg_dir, "seg_output")
        target = dapi_seg_input_dir
        output_path = dapi_seg_output_dir
        for folder in os.listdir(target):
            if os.path.isdir(os.path.join(target, folder)):
                print("The following folder " + folder + " will be processed")
                directory_path = os.path.join(target, folder)
                filename = folder + config.tiff_ext
                nuclear_channel_name = filename
                autoboost_reference_image = filename
                channelfile = "channelNames_" + folder + ".txt"
                main(target, output_path, directory_path, nuclear_channel_name, autoboost_reference_image, channelfile)
    elif step == "postprocessing_dapiSeg":
        from postprocessing_dapi_seg import PostProcessingDapiSeg
        dapi_seg_dir = os.path.join(working_dir, "dapi_seg")
        dapi_seg_output_dir = os.path.join(dapi_seg_dir, "seg_output")
        dapi_seg_binary_dir = ht.setting_directory(dapi_seg_dir, "dapi_seg_binary")
        PostProcessingDapiSeg(os.path.join(dapi_seg_output_dir, "visual_output"), os.path.join(dapi_seg_binary_dir),
                              config.tiff_ext).process()
    elif step == "resultsOutput":
        bg_adjust_dir = os.path.join(working_dir, "bg_processed")
        merge_channels_dir = os.path.join(working_dir, "mergedChannels")
        dapi_seg_dir = os.path.join(working_dir, "dapi_seg")
        dapi_seg_binary_size_correct_dir = os.path.join(dapi_seg_dir, "binary_size_correct")
        results_output_folder = ht.setting_directory(working_dir, "results_output")
        # Calling the ResultsOutput class function
        ResultsOutput(working_dir, bg_adjust_dir, merge_channels_dir, dapi_seg_binary_size_correct_dir,
                      results_output_folder).process()


if __name__ == "__main__":
    start_time = time.time()
    processing(sys.argv)
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(ht.convert(end_time - start_time))
