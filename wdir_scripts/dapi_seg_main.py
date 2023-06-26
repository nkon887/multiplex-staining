# dapi_seg_main.py
# ---------------------------
# dapi_seg_main.py connects segmentation, stitching, and output into a single pipeline.  It prints metadata about
# the run, and then initializes a segmenter and stitcher.  Looping over all image files in the directory,
# each image is segmented, stitched, grown, and overlaps resolved.  The data is concatenated if outputting
# as quantifications, and outputted per file for other output methods.  This file can be run by itself by
# invoking python main.py or the main function imported.

import logging
import os

import numpy as np
import tensorflow as tf
from cellsegpackage import cvutils
from cellsegpackage import cvvisualize
from cellsegpackage.cvmask import CVMask
from cellsegpackage.cvsegmenter import CVSegmenter
from cellsegpackage.cvstitch import CVMaskStitcher
from tifffile import imsave
import setup_logger
import helpertools as ht
from cvconfig import CVConfig

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
        path = ''

        if cf.BOOST == 'auto':
            path = ht.correct_path(cf.DIRECTORY_PATH, cf.AUTOBOOST_REFERENCE_IMAGE)
            image = np.array(cf.READ_METHOD(path))
            file_name, ext = os.path.splitext(path)

            if cf.tiff_ext in ext:
                if cf.N_DIMS == 4:
                    image = np.transpose(image, (2, 3, 0, 1))
                elif cf.N_DIMS == 3:
                    image = np.transpose(image, (1, 2, 0))

            image = image.reshape(cf.SHAPE)
            nuclear_index = None
            if cf.tiff_ext in ext:
                nuclear_index = cvutils.get_channel_index(cf.NUCLEAR_CHANNEL_NAME, cf.CHANNEL_NAMES)
            nuclear_image = cvutils.get_nuclear_image(cf.N_DIMS - 1, image, nuclear_index=nuclear_index)
            logger.info('Using auto boosting - may be inaccurate for empty or noisy images.')
            image_max = np.percentile(nuclear_image, cf.AUTOBOOST_PERCENTILE)
            cf.BOOST = cvutils.EIGHT_BIT_MAX / image_max
            logger.info('Boosting with value of ' + str(cf.BOOST) + ', check that this makes sense.')
            path = ht.correct_path(cf.DIRECTORY_PATH, filename)
            image = np.array(cf.READ_METHOD(path))
            ext = path.split('.')[-1]
            if cf.tiff_ext in ext:
                if cf.N_DIMS == 4:
                    image = np.transpose(image, (2, 3, 0, 1))
                elif cf.N_DIMS == 3:
                    image = np.transpose(image, (1, 2, 0))
            image = image.reshape(cf.SHAPE)
            nuclear_index = None
            if cf.tiff_ext in ext:
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
            logger.info('Creating visual overlay output saved to ' + str(cf.VISUAL_OUTPUT_PATH))
            new_path = ht.correct_path(cf.VISUAL_OUTPUT_PATH, filename[:-4]) + 'growth' + str(growth) + \
                       'mask' + cf.tiff_ext
            outlines = cvvisualize.generate_mask_outlines(stitched_mask.flatmasks)
            imsave(new_path, outlines, bigtiff=True)
            # save intermediate progress in case of mid-run crash
            with open(cf.PROGRESS_TABLE_PATH, "a") as myfile:
                myfile.write(filename + "\n")
    logger.info("Segmentation Completed")
