# @String base_dir
# @String target_dir
# @String step
# TODO: unit tests, integration tests, add comments params
import logging
import os
import sys

from java.lang import System

from alignment import Alignment
from background_processing import BackgroundAdjustment
from correct_imagesize import DapiSeg_Resizer
from cropping import Cropping
from hyperstack_generation import HyperstackGeneration
from merging_channels import MergingChannels
from stitching import stitchingTools

sys.path.append(os.path.abspath(os.getcwd()))
import config
import helpertools as ht

# main.py creates its own logger, as a sub logger to 'pipelineGUI.macro.main'
logger = logging.getLogger('pipelineGUI.macro.main')


def processing(base_dir, target_dir, step):
    logger.info(step)
    stitch_input_dir = base_dir
    args = []
    if step == "STITCHING":
        working_dir = ht.setting_directory(target_dir, "workingDir")
        input_dir = ht.setting_directory(working_dir, "input")
        args = stitchingTools(stitch_input_dir, input_dir, working_dir, config.czi_ext, config.tiff_ext).process
    else:
        working_dir = ht.correct_path(target_dir, "workingDir")
        if step == "ALIGNMENT":
            input_dir = ht.correct_path(working_dir, "input")
            alignment_dir = ht.setting_directory(working_dir, "alignment_SV")
            precrop_input_dir = ht.setting_directory(working_dir, "input_to_precrop")
            args = Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, input_dir,
                             precrop_input_dir).aligning
        elif step == "REALIGNMENT":
            alignment_dir = ht.correct_path(working_dir, "alignment_SV")
            precrop_input_dir = ht.correct_path(working_dir, "input_to_precrop")
            stacks_dir = ht.setting_directory(working_dir, "stacks")
            cropped_stacks_dir = ht.setting_directory(working_dir, "cropped_input")
            logger.info("1. GENERATION OF HYPERSTACKS")
            ht.step_execution(HyperstackGeneration(precrop_input_dir, stacks_dir, config.tiff_ext).generate_hyperstack)
            logger.info("2. CROPPING BEFORE ALIGNMENT")
            ht.step_execution(Cropping(stacks_dir, cropped_stacks_dir, config.error_subfolder_name,
                                       config.tiff_ext, config.cropped_suffix).processing_before_alignment)
            logger.info("3. REALIGNMENT")
            args = Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, cropped_stacks_dir,
                             precrop_input_dir).aligning
        elif step == "CROPPING AFTER ALIGNMENT":
            alignment_dir = ht.correct_path(working_dir, "alignment_SV")
            args = Cropping(alignment_dir, alignment_dir, config.error_subfolder_name, config.tiff_ext,
                            config.cropped_suffix).processing_after_alignment
        elif step == "BACKGROUNDADJUSTMENT":
            alignment_dir = ht.correct_path(working_dir, "alignment_SV")
            bg_adjust_dir = ht.setting_directory(working_dir, "bg_processed")
            args = BackgroundAdjustment(alignment_dir, bg_adjust_dir, config.tiff_ext).processing
        elif step == "MERGING CHANNELS":
            bg_adjust_dir = ht.correct_path(working_dir, "bg_processed")
            merge_channels_dir = ht.setting_directory(working_dir, "mergedChannels")
            args = MergingChannels(bg_adjust_dir, merge_channels_dir, config.tiff_ext, config.dapi_str).processing
        elif step == "DAPISEG_RESIZER":
            bg_adjust_dir = ht.correct_path(working_dir, "bg_processed")
            dapi_seg_dir = ht.correct_path(working_dir, "dapi_seg")
            dapi_seg_binary_dir = ht.correct_path(dapi_seg_dir, "dapi_seg_binary")
            dapi_seg_binary_size_correct_dir = ht.setting_directory(dapi_seg_dir, "binary_size_correct")
            args = \
                DapiSeg_Resizer, config.tiff_ext, dapi_seg_binary_dir, bg_adjust_dir, dapi_seg_binary_size_correct_dir
    ht.step_execution(args)


if __name__ in ['__builtin__', '__main__']:
    processing()

    System.exit(0)
