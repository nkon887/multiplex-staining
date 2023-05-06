# @String base_dir
# @String step
# TODO: unit tests, integration tests, add comments params
import os
import sys
import time
from datetime import datetime
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import config
import helpertools as ht
from alignment import Alignment
from cropping import Cropping
from hyperstack_generation import HyperstackGeneration
from background_processing import BackgroundAdjustment
from merging_channels import MergingChannels
from stitching import stitchingTools
from correct_imagesize import DapiSeg_Resizer


def processing(base_dir, step):
    working_dir = ht.setting_directory(base_dir, "workingDir")
    stitch_input_dir = ht.setting_directory(working_dir, "00_raw_input")
    input_dir = ht.setting_directory(working_dir, "01_input")
    alignment_dir = ht.setting_directory(working_dir, "02_alignment_SV")
    precrop_input_dir = ht.setting_directory(working_dir, "03_input_to_precrop")
    stacks_dir = ht.setting_directory(working_dir, "04_stacks")
    cropped_stacks_dir = ht.setting_directory(working_dir, "05_cropped_input")
    bg_adjust_dir = ht.setting_directory(working_dir, "06_bg_processed")
    merge_channels_dir = ht.setting_directory(working_dir, "07_mergedChannels")
    dapi_seg_dir = ht.setting_directory(working_dir, "08_dapi_seg")
    dapi_seg_binary_dir = ht.setting_directory(dapi_seg_dir, "dapi_seg_binary")
    dapi_seg_binary_size_correct_dir = ht.setting_directory(dapi_seg_dir, "binary_size_correct")

    stitching_time = ""
    alignment_time = ""
    hyperstack_generation_time = ""
    cropping_time_before_alignment = ""
    realignment_time = ""
    cropping_time_after_alignment = ""
    background_adjust_time = ""
    merging_channels_time = ""
    segmentation_time = ""
    if step == "stitch":
        print("STITCHING")
        # start
        # dd/mm/YY H:M:S
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        stitchingTools(stitch_input_dir, input_dir, config.czi_ext, config.tiff_ext).process()
        end_time = time.time()
        print("\nDuration of the program execution:")
        stitching_time = ht.convert(end_time - start_time)
        print(stitching_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        # End of stitching
    elif step == "alignment":
        print("ALIGNMENT")
        # start
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, input_dir, precrop_input_dir).aligning()
        end_time = time.time()
        print("\nDuration of the program execution:")
        alignment_time = ht.convert(end_time - start_time)
        print(alignment_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        # End of alignment
        print("GENERATION OF HYPERSTACKS")
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        HyperstackGeneration(precrop_input_dir, stacks_dir, config.tiff_ext).generate_hyperstack()
        end_time = time.time()
        print("\nDuration of the program execution:")
        hyperstack_generation_time = ht.convert(end_time - start_time)
        print(hyperstack_generation_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        print("CROPPING BEFORE ALIGNMENT")
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        Cropping(stacks_dir, cropped_stacks_dir, config.error_subfolder_name,
                 config.tiff_ext, config.cropped_suffix).processing_before_alignment()
        end_time = time.time()
        print("\nDuration of the program execution:")
        cropping_time_before_alignment = ht.convert(end_time - start_time)
        print(cropping_time_before_alignment)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        print("REALIGNMENT")
        # start
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, cropped_stacks_dir,
                  precrop_input_dir).aligning()
        end_time = time.time()
        print("\nDuration of the program execution:")
        realignment_time = ht.convert(end_time - start_time)
        print(realignment_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        # End of alignment
        print("CROPPING AFTER ALIGNMENT")
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        Cropping(alignment_dir, alignment_dir, config.error_subfolder_name, config.tiff_ext,
                 config.cropped_suffix).processing_after_alignment()
        end_time = time.time()
        print("\nDuration of the program execution:")
        cropping_time_after_alignment = ht.convert(end_time - start_time)
        print(cropping_time_after_alignment)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        print("BACKGROUNDADJUSTMENT")
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        BackgroundAdjustment(alignment_dir, bg_adjust_dir, config.tiff_ext).processing()
        end_time = time.time()
        print("\nDuration of the program execution:")
        background_adjust_time = ht.convert(end_time - start_time)
        print(background_adjust_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        print("MERGING CHANNELS")
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        MergingChannels(bg_adjust_dir, merge_channels_dir, config.tiff_ext, config.dapi_str).processing()
        end_time = time.time()
        print("\nDuration of the program execution:")
        merging_channels_time = ht.convert(end_time - start_time)
        print(merging_channels_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
    elif step == "segmentation":
        print("DAPISEG_RESIZER")
        print("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
        start_time = time.time()
        DapiSeg_Resizer(config.tiff_ext, dapi_seg_binary_dir, bg_adjust_dir, dapi_seg_binary_size_correct_dir)
        end_time = time.time()
        print("\nDuration of the program execution:")
        segmentation_time = ht.convert(end_time - start_time)
        print(segmentation_time)
        print("End time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
    print("execution time overview")
    if stitching_time != "":
        print("stitching " + str(stitching_time))
    print("alignment " + str(alignment_time))
    print("hyperstack " + str(hyperstack_generation_time))
    print("cropping " + str(cropping_time_before_alignment))
    print("realign " + str(realignment_time))
    print("cropping " + str(cropping_time_after_alignment))
    print("bg adjust " + str(background_adjust_time))
    print("channels merge " + str(merging_channels_time))
    if segmentation_time != "":
        print("dapi segmentation resize" + str(segmentation_time))


if __name__ in ['__builtin__', '__main__']:
    # Start time
    start_time = time.time()
    processing()
    # End time
    end_time = time.time()
    # Total time
    print("\nDuration of the program execution:")
    print(ht.convert(end_time - start_time))
    System.exit(0)
