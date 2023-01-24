import os
import sys
import time
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import config
import pythontools as pt
from alignment import Alignment
from cropping import Cropping
from hyperstack_generation import HyperstackGeneration
from background_processing import BackgroundAdjustment
from merging_channels import MergingChannels


def processing():

    print("ALIGNMENT")
    # start
    start_time = time.time()
    Alignment(config.alignment_dir, config.tiff_ext, config.error_subfolder_name, config.input_dir).aligning()
    end_time = time.time()
    print("\nDuration of the program execution:")
    alignment_time = pt.convert(end_time - start_time)
    print(alignment_time)
    # End of alignment
    print("GENERATION OF HYPERSTACKS")
    start_time = time.time()
    HyperstackGeneration(config.precrop_input_dir, config.stacks_dir, config.tiff_ext).generate_hyperstack()
    end_time = time.time()
    print("\nDuration of the program execution:")
    hyperstack_generation_time = pt.convert(end_time - start_time)
    print(hyperstack_generation_time)
    print("CROPPING BEFORE ALIGNMENT")
    start_time = time.time()
    Cropping(config.stacks_dir, config.cropped_stacks_dir, config.error_subfolder_name,
             config.tiff_ext, config.cropped_suffix).processing_before_alignment()
    end_time = time.time()
    print("\nDuration of the program execution:")
    cropping_time_before_alignment = pt.convert(end_time - start_time)
    print(cropping_time_before_alignment)
    print("REALIGNMENT")
    # start
    start_time = time.time()
    Alignment(config.alignment_dir, config.tiff_ext, config.error_subfolder_name, config.cropped_stacks_dir).aligning()
    end_time = time.time()
    print("\nDuration of the program execution:")
    realignment_time = pt.convert(end_time - start_time)
    print(realignment_time)
    # End of alignment
    print("CROPPING AFTER ALIGNMENT")
    start_time = time.time()
    Cropping(config.alignment_dir, config.alignment_dir, config.error_subfolder_name, config.tiff_ext,
             config.cropped_suffix).processing_after_alignment()
    end_time = time.time()
    print("\nDuration of the program execution:")
    cropping_time_after_alignment = pt.convert(end_time - start_time)
    print(cropping_time_after_alignment)
    print("BACKGROUNDADJUSTMENT")
    start_time = time.time()
    BackgroundAdjustment(config.alignment_dir, config.bg_adjust_dir, config.tiff_ext).processing()
    end_time = time.time()
    print("\nDuration of the program execution:")
    background_adjust_time = pt.convert(end_time - start_time)
    print(background_adjust_time)
    print("MERGING CHANNELS")
    start_time = time.time()
    MergingChannels(config.bg_adjust_dir, config.merge_channels_dir, config.tiff_ext, config.dapi_str).processing()
    end_time = time.time()
    print("\nDuration of the program execution:")
    merging_channels_time = pt.convert(end_time - start_time)
    print(merging_channels_time)
    print("execution time overview")
    print("alignment " + str(alignment_time))
    print("hyperstack " + str(hyperstack_generation_time))
    print("cropping " + str(cropping_time_before_alignment))
    print("realign " + str(realignment_time))
    print("cropping " + str(cropping_time_after_alignment))
    print("bg adjust " + str(background_adjust_time))
    print("channels merge " + str(merging_channels_time))


if __name__ in ['__builtin__', '__main__']:
    # Start time
    start_time = time.time()
    processing()
    # End time
    end_time = time.time()
    # Total time
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
