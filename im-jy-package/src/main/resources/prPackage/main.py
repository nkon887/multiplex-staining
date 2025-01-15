# @String base_dir
# @String target_dir
# @String working_dir
# @String step
# @String pipeline_steps
# @String subfolders
# @String realignment_subfolders
# @String dapiseg_subfolders
# @String crop_option
# @String forceSave
# @String alignment_option
# TODO: unit tests, integration tests, add comments params
import logging
import os
import sys

from java.lang import System
from ij import IJ

from alignment import Alignment
from background_processing import BackgroundAdjustment
from correct_imagesize import DapiSeg_Resizer
from cropping import Cropping
from exp_cropping import Cropping_Experimental
from hyperstack_generation import HyperstackGeneration
from merging_channels import MergingChannels
from stitching import stitchingTools

sys.path.append(os.path.abspath(os.getcwd()))
import config
import helpertools as ht

# im-jy-package.main.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package'
logger = logging.getLogger('multiplex.macro.im-jy-package.main')


def processing(base_dir, target_dir, working_dir, step, pipeline_steps, subfolders, realignment_subfolders,
               dapiseg_subfolders, crop_option, forceSave, alignment_option):
    logger.info(step)
    stitch_input_dir = base_dir
    args = []
    pipeline_steps_list = pipeline_steps.split(",")
    subfolders_list = subfolders.split(",")
    realignment_subfolders_list = realignment_subfolders.split(",")
    dapiseg_subfolders_list = dapiseg_subfolders.split(",")
    if step == pipeline_steps_list[0]:
        work_dir = ht.setting_directory(target_dir, working_dir)
        input_dir = ht.setting_directory(target_dir, subfolders_list[0])
        args = stitchingTools(stitch_input_dir, input_dir, work_dir, config.czi_ext, config.tiff_ext,
                              config.info_txt_file, config.metadata_csv_file, config.no_shading_file,
                              config.shading_word, config.TIFF_ext, forceSave).process
    elif step == pipeline_steps_list[2]:
        #logger.info(pipeline_steps_list[2])
        input_dir = ht.correct_path(target_dir, subfolders_list[0])
        alignment_dir = ht.setting_directory(target_dir, subfolders_list[1])
        precrop_input_dir = ht.setting_directory(target_dir, realignment_subfolders_list[0])
        stacks_dir = ht.setting_directory(target_dir, realignment_subfolders_list[1])
        cropped_stacks_dir = ht.setting_directory(target_dir, realignment_subfolders_list[2])
        #logger.info(precrop_input_dir)
        #logger.info(len(os.listdir(precrop_input_dir)))
        if alignment_option == 'align':
            logger.info("ALIGNMENT")
            args = Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, input_dir,
                             precrop_input_dir, forceSave).aligning
        elif alignment_option == 'realign':
            logger.info("REALIGNMENT")
            if len(os.listdir(precrop_input_dir)) != 0:
                logger.info("1. GENERATION OF HYPERSTACKS")
                ht.step_execution(step,
                                  HyperstackGeneration(precrop_input_dir, stacks_dir, config.tiff_ext,
                                                       forceSave).generate_hyperstack)
                logger.info("2. CROPPING BEFORE ALIGNMENT")
                ht.step_execution(step, Cropping("REALIGNMENT", stacks_dir, cropped_stacks_dir,
                                                 config.error_subfolder_name,
                                                 config.tiff_ext, config.cropped_suffix, crop_option,
                                                 forceSave).processing_before_alignment)
                logger.info("3. REALIGNMENT")
                args = Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, cropped_stacks_dir,
                                 precrop_input_dir, forceSave).aligning
            else:
                logger.info("The realignment will not be executed as there is no input data for it")

        # ht.step_execution(Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, cropped_stacks_dir,
        #                            precrop_input_dir).aligning)
    #    args = Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, input_dir,
    #                     precrop_input_dir).aligning
    # elif step == pipeline_steps_list[3]:
    #    alignment_dir = ht.correct_path(target_dir, subfolders_list[1])
    #    precrop_input_dir = ht.correct_path(target_dir, realignment_subfolders_list[0])
    #    stacks_dir = ht.setting_directory(target_dir, realignment_subfolders_list[1])
    #    cropped_stacks_dir = ht.setting_directory(target_dir, realignment_subfolders_list[2])
    #    logger.info("1. GENERATION OF HYPERSTACKS")
    #    ht.step_execution(HyperstackGeneration(precrop_input_dir, stacks_dir, config.tiff_ext).generate_hyperstack)
    #    logger.info("2. CROPPING BEFORE ALIGNMENT")
    #    ht.step_execution(Cropping(step, stacks_dir, cropped_stacks_dir, config.error_subfolder_name,
    #                               config.tiff_ext, config.cropped_suffix).processing_before_alignment)
    #    logger.info("3. REALIGNMENT")
    #    args = Alignment(alignment_dir, config.tiff_ext, config.error_subfolder_name, cropped_stacks_dir,
    #                     precrop_input_dir).aligning
    elif step == pipeline_steps_list[3]:
        alignment_dir = ht.correct_path(target_dir, subfolders_list[1])
        args = Cropping(step, alignment_dir, alignment_dir, config.error_subfolder_name, config.tiff_ext,
                        config.cropped_suffix, crop_option, forceSave).processing_after_alignment
    elif step == pipeline_steps_list[4]:
        # alignment_dir = ht.correct_path(target_dir, subfolders_list[1])
        # args = Cropping_Experimental(step, alignment_dir, alignment_dir, config.error_subfolder_name,
        #                             config.tiff_ext, config.cropped_suffix, forceSave).processing_after_alignment
        # elif step == pipeline_steps_list[5]:
        alignment_dir = ht.correct_path(target_dir, subfolders_list[1])
        bg_adjust_dir = ht.setting_directory(target_dir, subfolders_list[2])
        txt_dir = ht.correct_path(target_dir, subfolders_list[0])
        work_dir = ht.setting_directory(target_dir, working_dir)
        args = BackgroundAdjustment(txt_dir, config.info_txt_file, work_dir, config.metadata_csv_file,
                                    alignment_dir, bg_adjust_dir,
                                    config.tiff_ext, config.csv_ext, forceSave).processing
    elif step == pipeline_steps_list[5]:
        bg_adjust_dir = ht.correct_path(target_dir, subfolders_list[2])
        merge_channels_dir = ht.setting_directory(target_dir, subfolders_list[3])
        work_dir = ht.setting_directory(target_dir, working_dir)
        args = MergingChannels(bg_adjust_dir, merge_channels_dir, config.tiff_ext, config.dapi_str,
                               work_dir, forceSave).processing
    elif step == pipeline_steps_list[6]:
        bg_adjust_dir = ht.correct_path(target_dir, subfolders_list[2])
        dapi_seg_binary_dir = ht.correct_path(target_dir, dapiseg_subfolders_list[2])
        dapi_seg_binary_size_correct_dir = ht.setting_directory(target_dir, dapiseg_subfolders_list[3])
        args = DapiSeg_Resizer(step, config.tiff_ext, dapi_seg_binary_dir, bg_adjust_dir,
                               dapi_seg_binary_size_correct_dir, forceSave).processing
    if not args == []:
        ht.step_execution(step, args)
    IJ.run("Quit")


if __name__ in ['__builtin__', '__main__']:
    processing()
    System.exit(0)
