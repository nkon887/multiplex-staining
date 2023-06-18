# dapi_seg_main.py
# ---------------------------
# dapi_seg_main.py connects segmentation, stitching, and output into a single pipeline.  It prints metadata about
# the run, and then initializes a segmenter and stitcher.  Looping over all image files in the directory,
# each image is segmented, stitched, grown, and overlaps resolved.  The data is concatenated if outputting
# as quantifications, and outputted per file for other output methods.  This file can be run by itself by
# invoking python main.py or the main function imported.

import os
from collections import defaultdict

import numpy as np
import pandas as pd
import tensorflow as tf
from cellsegpackage.cvmask import CVMask
from cellsegpackage.cvsegmenter import CVSegmenter
from cellsegpackage.cvstitch import CVMaskStitcher
from tifffile import imsave

import config
from cvconfig import CVConfig
from cellsegpackage import cvutils
from cellsegpackage import cvvisualize
from cellsegpackage import fcswrite
import setup_logger
import logging
import helpertools as ht

# dapi_seg_main.py creates its own logger, as a sub logger to 'pipelineGUI.main'
logger = logging.getLogger('pipelineGUI.main.main_dapiSeg')


def main(target, output_path, directory_path, nuclear_channel_name, autoboost_reference_image, channelfile):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    cf = CVConfig(target, output_path, directory_path, nuclear_channel_name, autoboost_reference_image, channelfile)
    logger.info("Checking previous segmentation progress...")
    progress_table = cf.PROGRESS_TABLE
    logger.info("These tiles already segmented: ")
    logger.info(progress_table)
    cf.FILENAMES = [item for item in cf.FILENAMES if item not in progress_table]
    cf.FILENAMES.sort()
    count = 0
    for filename in cf.FILENAMES:
        count += 1

        logger.info('Initializing CSSegmenter at ' + str(cf.DIRECTORY_PATH))
        if cf.IS_CODEX_OUTPUT:
            logger.info('Picking channel', cf.NUCLEAR_CHANNEL_NAME, 'from',
                        len(cf.CHANNEL_NAMES), 'total to segment on')
            logger.info('Channel names:')
            logger.info(cf.CHANNEL_NAMES)
        logger.info("Working with images of shape: " + str(cf.SHAPE))
        stitcher = CVMaskStitcher(overlap=cf.OVERLAP, threshold=cf.THRESHOLD)
        # imshape = cf.SHAPE
        # if cf.HALF_RESOLUTION:
        #    imshape = (round(imshape[0] / 2), round(imshape[1] / 2), imshape[2])
        segmenter = CVSegmenter(
            cf.SHAPE,
            cf.MODEL_PATH,
            cf.OVERLAP,
            cf.INCREASE_FACTOR,
            cf.THRESHOLD
        )
        growth = cf.GROWTH_PIXELS
        rows, cols = None, None
        dataframe_regs = defaultdict(list)
        columns = []
        path = ''
        if cf.OUTPUT_METHOD not in ['imagej_text_file', 'statistics', 'visual_image_output', 'visual_overlay_output',
                                    'all']:
            raise NameError(
                'Output method is not supported.  Check the OUTPUT_METHOD variable in cvconfig.py.')

        if cf.BOOST == 'auto':
            path = ht.correct_path(cf.DIRECTORY_PATH, cf.AUTOBOOST_REFERENCE_IMAGE)
            image = np.array(cf.READ_METHOD(path))
            file_name, ext = os.path.splitext(path)
            if config.tiff_ext in ext:
                if cf.N_DIMS == 4:
                    image = np.transpose(image, (2, 3, 0, 1))
                elif cf.N_DIMS == 3:
                    image = np.transpose(image, (1, 2, 0))

            image = image.reshape(cf.SHAPE)
            nuclear_index = None
            if config.tiff_ext in ext:
                nuclear_index = cvutils.get_channel_index(cf.NUCLEAR_CHANNEL_NAME, cf.CHANNEL_NAMES)
            nuclear_image = cvutils.get_nuclear_image(cf.N_DIMS - 1, image, nuclear_index=nuclear_index)
            logger.info('Using auto boosting - may be inaccurate for empty or noisy images.')
            image_max = np.percentile(nuclear_image, cf.AUTOBOOST_PERCENTILE)
            cf.BOOST = cvutils.EIGHT_BIT_MAX / image_max
            logger.info('Boosting with value of ' + str(cf.BOOST) + ', check that this makes sense.')
            path = ht.correct_path(cf.DIRECTORY_PATH, filename)
            image = np.array(cf.READ_METHOD(path))
            ext = path.split('.')[-1]
            if config.tiff_ext in ext:
                if cf.N_DIMS == 4:
                    image = np.transpose(image, (2, 3, 0, 1))
                elif cf.N_DIMS == 3:
                    image = np.transpose(image, (1, 2, 0))
            image = image.reshape(cf.SHAPE)
            nuclear_index = None
            if config.tiff_ext in ext:
                nuclear_index = cvutils.get_channel_index(cf.NUCLEAR_CHANNEL_NAME, cf.CHANNEL_NAMES)
            nuclear_image = cvutils.get_nuclear_image(cf.N_DIMS - 1, image, nuclear_index=nuclear_index)
            nuclear_image = cvutils.boost_image(nuclear_image, cf.BOOST)
            logger.info('Segmenting with CellSeg: ' + str(filename))
            masks, rows, cols = segmenter.segment_image(nuclear_image)
            logger.info('Stitching: ' + str(filename))
            stitched_mask = CVMask(stitcher.stitch_masks(masks, rows, cols))
            # inside the stitcher, split the masks back into crops
            del masks
            instances = stitched_mask.n_instances()
            logger.info(str(instances) + ' cell masks found by segmenter')
            if instances == 0:
                logger.warning('No cells found in', filename, ', skipping to next')
                continue
            logger.info('Growing cells by ' + str(growth) + ' pixels: ' + str(filename))
            logger.info("Computing centroids and bounding boxes for the masks.")
            stitched_mask.compute_centroids()
            stitched_mask.compute_boundbox()
            if cf.GROWTH_PIXELS > 0:
                print(f"Growing masks by {cf.GROWTH_PIXELS} pixels")
                stitched_mask.grow_masks(cf.GROWTH_PIXELS, cf.GROWTH_METHOD)
            # restitch and squash after growth
            if not os.path.exists(cf.IMAGEJ_OUTPUT_PATH):
                os.makedirs(cf.IMAGEJ_OUTPUT_PATH)
            if not os.path.exists(cf.VISUAL_OUTPUT_PATH):
                os.makedirs(cf.VISUAL_OUTPUT_PATH)
            if not os.path.exists(cf.QUANTIFICATION_OUTPUT_PATH):
                os.makedirs(cf.QUANTIFICATION_OUTPUT_PATH)
            if cf.OUTPUT_METHOD == 'imagej_text_file':
                logger.info('Sort into strips and outputting:', filename)
                new_path = ht.correct_path(
                    cf.IMAGEJ_OUTPUT_PATH, (filename[:-4] + '-coords.txt'))
                stitched_mask.sort_into_strips()
                stitched_mask.output_to_file(new_path)
            if cf.OUTPUT_METHOD == 'visual_image_output' or cf.OUTPUT_METHOD == 'all':
                logger.info('Creating visual output saved to', cf.VISUAL_OUTPUT_PATH)
                new_path = ht.correct_path(cf.VISUAL_OUTPUT_PATH, filename[:-4]) + 'visual_growth' + str(
                    growth) + ".png"
                figsize = (cf.SHAPE[1] // 25, cf.SHAPE[0] // 25)
                outlines = cvvisualize.generate_mask_outlines(stitched_mask.flatmasks)
                # cvvisualize.overlay_outlines_and_save(nuclear_image, outlines, new_path, figsize=figsize)
            if cf.OUTPUT_METHOD == 'visual_overlay_output' or cf.OUTPUT_METHOD == 'all':
                logger.info('Creating visual overlay output saved to ' + str(cf.VISUAL_OUTPUT_PATH))
                new_path = ht.correct_path(cf.VISUAL_OUTPUT_PATH, filename[:-4]) + 'growth' + str(growth) + \
                           'mask' + config.tiff_ext
                outlines = cvvisualize.generate_mask_outlines(stitched_mask.flatmasks)
                imsave(new_path, outlines, bigtiff=True)
            if cf.OUTPUT_METHOD == 'statistics' or cf.OUTPUT_METHOD == 'all':
                logger.info('Calculating statistics:', filename)
                reg, tile_row, tile_col, tile_z = 0, 1, 1, 0
                regname = ''
                if cf.IS_CODEX_OUTPUT:
                    reg, tile_row, tile_col, tile_z = cvutils.extract_tile_information(
                        filename)
                    regname = filename.split("_")[0]
                size = None
                channel_means_comp, channel_means_uncomp, size = stitched_mask.compute_channel_means_sums_compensated(
                    image)
                centroids = stitched_mask.centroids
                absolutes = stitched_mask.absolute_centroids(tile_row, tile_col)
                semi_dataframe_comp = 1
                semi_dataframe = 1
                if centroids:
                    metadata_list = np.array([reg, tile_row, tile_col, tile_z])
                    metadata = np.broadcast_to(
                        metadata_list, (stitched_mask.n_instances(), len(metadata_list)))
                    semi_dataframe = np.concatenate(
                        [metadata, np.array(centroids), absolutes, size[:, None], channel_means_uncomp], axis=1)
                    semi_dataframe_comp = np.concatenate(
                        [metadata, np.array(centroids), absolutes, size[:, None], channel_means_comp], axis=1)
                descriptive_labels = [
                    'Reg',
                    'Tile Row',
                    'Tile Col',
                    'Tile Z',
                    'In-Tile Y',
                    'In-Tile X',
                    'Absolute Y',
                    'Absolute X',
                    'Cell Size'
                ]
                # Output to CSV
                if not cf.IS_CODEX_OUTPUT:
                    regname = filename.replace("." + filename.split(".")[-1], "")
                    if not config.tiff_ext in ext:
                        cf.CHANNEL_NAMES = ['single-channel']
                        n_channels = cf.SHAPE[2]
                        if n_channels == 3:
                            cf.CHANNEL_NAMES = ['Red', 'Green', 'Blue']
                columns = descriptive_labels + [s for s in cf.CHANNEL_NAMES]
                dataframe = None
                path = ''
                if cf.SHOULD_COMPENSATE:
                    dataframe = pd.DataFrame(semi_dataframe_comp, columns=columns)
                    path = ht.correct_path(cf.QUANTIFICATION_OUTPUT_PATH,
                                           regname + '_statistics_growth' + str(growth) + '_comp')
                else:
                    dataframe = pd.DataFrame(semi_dataframe, columns=columns)
                    path = ht.correct_path(cf.QUANTIFICATION_OUTPUT_PATH,
                                           regname + '_statistics_growth' + str(growth) + '_uncomp')
                if os.path.exists(path + '.csv'):
                    dataframe.to_csv(path + '.csv', mode='a', header=False)
                else:
                    dataframe.to_csv(path + '.csv')

            # save intermediate progress in case of mid-run crash
            with open(cf.PROGRESS_TABLE_PATH, "a") as myfile:
                myfile.write(filename + "\n")

        # duplicate existing csv files in fcs format at the end of run
        if cf.OUTPUT_METHOD == 'statistics' or cf.OUTPUT_METHOD == 'all':
            logger.info("Duplicating existing csv files in fcs format")
            descriptive_labels = [
                'Reg',
                'Tile Row',
                'Tile Col',
                'Tile Z',
                'In-Tile Y',
                'In-Tile X',
                'Absolute Y',
                'Absolute X',
                'Cell Size'
            ]
            columns = descriptive_labels + [s for s in cf.CHANNEL_NAMES]
            filenames = os.listdir(cf.QUANTIFICATION_OUTPUT_PATH)
            filenames = [f for f in filenames if f.endswith("csv")]
            for filename in filenames:
                path = ht.correct_path(cf.QUANTIFICATION_OUTPUT_PATH, filename)
                dataframe = pd.read_csv(path, index_col=0)
                path = path.replace('.csv', '')
                fcswrite.write_fcs(path + '.fcs', columns, dataframe)
    logger.info("Segmentation Completed")
