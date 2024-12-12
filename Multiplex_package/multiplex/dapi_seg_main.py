# multiplex.dapi_seg_main.py --------------------------- multiplex.dapi_seg_main.py connects segmentation, stitching,
# and output into a single pipeline.  It prints metadata about the run, and then initializes a segmenter and
# stitcher.  Looping over all image files in the directory, each image is segmented, stitched, grown, and overlaps
# resolved.  The data is concatenated if outputting as quantifications, and outputted per file for other output
# methods.  This file can be run by itself by invoking python main.py or the main function imported.
import gc
import logging
import os
import weakref

import numpy as np
import tensorflow as tf
from PIL import Image
from cellsegpackage import cvutils
from cellsegpackage import cvvisualize
from cellsegpackage.cvmask import CVMask
from cellsegpackage.cvsegmenter import CVSegmenter
from cellsegpackage.cvstitch import CVMaskStitcher
from tifffile import imsave
import multiplex.setup_logger
import multiplex.helpertools as ht
from cellsegpackage.cvconfig import CVConfig
from ppconfig import PIPELINEConfig

# multiplex.dapi_seg_main.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.main.main_dapiSeg')


class DapiSeg:
    def __init__(self, target, output_path):
        self.target = target
        self.output_path = output_path
    def process(self):
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
        for folder in os.listdir(self.target):
            if os.path.isdir(ht.correct_path(self.target, folder)):
                logger.info("The following folder " + folder + " will be processed")
                self.segment(folder)

    def segment(self, folder):
        ppc = PIPELINEConfig()
        ppc_ref = weakref.ref(ppc)
        filename = folder + ppc_ref().tiff_ext
        del ppc, ppc_ref
        gc.collect()
        cf = CVConfig(self.target, self.output_path, ht.correct_path(self.target, folder), filename,
                      filename, "channelNames_" + folder + ".txt")
        cf_ref = weakref.ref(cf)
        logger.info(
            "Checking previous segmentation progress...\nThese tiles already segmented: " + str(
                cf_ref().PROGRESS_TABLE))
        filenames_to_process = [item for item in cf_ref().FILENAMES if item not in cf_ref().PROGRESS_TABLE]
        filenames_to_process.sort()
        for filename in filenames_to_process:
            logger.info('Initializing CSSegmenter at ' + str(cf_ref().DIRECTORY_PATH))
            if cf_ref().IS_CODEX_OUTPUT:
                logger.info('Picking channel ' + str(cf_ref().NUCLEAR_CHANNEL_NAME) + ' from ' +
                            str(len(cf_ref().CHANNEL_NAMES)) + ' total to segment on\nChannel names: '
                            + str(cf_ref().CHANNEL_NAMES) + '\nWorking with images of cf.SHAPE: ' + str(cf_ref().SHAPE))
            stitcher = CVMaskStitcher(overlap=cf_ref().OVERLAP, threshold=cf_ref().THRESHOLD)
            # imshape = cf.SHAPE
            # if cf.HALF_RESOLUTION:
            #    imshape = (round(imshape[0] / 2), round(imshape[1] / 2), imshape[2])
            stitcher_ref = weakref.ref(stitcher)
            segmenter = CVSegmenter(
                cf_ref().SHAPE,
                cf_ref().MODEL_PATH,
                cf_ref().OVERLAP,
                cf_ref().INCREASE_FACTOR,
                cf_ref().THRESHOLD
            )
            segmenter_ref = weakref.ref(segmenter)
            ref_path = ''
            image_path = ''
            if cf_ref().BOOST == 'auto':
                ref_path = ht.correct_path(cf_ref().DIRECTORY_PATH, cf_ref().AUTOBOOST_REFERENCE_IMAGE)
                ref_image = np.array(cf_ref().READ_METHOD(ref_path))
                ref_file_name, ref_ext = os.path.splitext(ref_path)
                if cf_ref().tiff_ext in ref_ext:
                    if cf_ref().N_DIMS == 4:
                        ref_image = np.transpose(ref_image, (2, 3, 0, 1))
                    elif cf_ref().N_DIMS == 3:
                        ref_image = np.transpose(ref_image, (1, 2, 0))
                ref_image = ref_image.reshape(cf_ref().SHAPE)
                ref_nuclear_index = None
                if cf_ref().tiff_ext in ref_ext:
                    ref_nuclear_index = cvutils.get_channel_index(cf_ref().NUCLEAR_CHANNEL_NAME, cf_ref().CHANNEL_NAMES)
                ref_nuclear_image = cvutils.get_nuclear_image(cf_ref().N_DIMS - 1, ref_image,
                                                              nuclear_index=ref_nuclear_index)
                del ref_image, ref_nuclear_index
                gc.collect()
                logger.info('Using auto boosting - may be inaccurate for empty or noisy images.')
                ref_image_max = np.percentile(ref_nuclear_image, cf_ref().AUTOBOOST_PERCENTILE)
                del ref_nuclear_image
                gc.collect()
                cf_ref().BOOST = cvutils.EIGHT_BIT_MAX / ref_image_max
                logger.info('Boosting with value of ' + str(cf_ref().BOOST) + ', check that this makes sense.')
                image_path = ht.correct_path(cf_ref().DIRECTORY_PATH, filename)
                image = np.array(cf_ref().READ_METHOD(image_path))
                im_ext = image_path.split('.')[-1]
                if cf_ref().tiff_ext in im_ext:
                    if cf_ref().N_DIMS == 4:
                        image = np.transpose(image, (2, 3, 0, 1))
                    elif cf_ref().N_DIMS == 3:
                        image = np.transpose(image, (1, 2, 0))
                image = image.reshape(cf_ref().SHAPE)
                im_nuclear_index = None
                if cf_ref().tiff_ext in im_ext:
                    im_nuclear_index = cvutils.get_channel_index(cf_ref().NUCLEAR_CHANNEL_NAME, cf_ref().CHANNEL_NAMES)
                im_nuclear_image = cvutils.get_nuclear_image(cf_ref().N_DIMS - 1, image,
                                                             nuclear_index=im_nuclear_index)
                del image, im_nuclear_index
                gc.collect()
                im_nuclear_image = cvutils.boost_image(im_nuclear_image, cf_ref().BOOST)
                logger.info('Segmenting with CellSeg: ' + str(filename))
                if not os.path.exists(cf_ref().VISUAL_OUTPUT_PATH):
                    os.makedirs(cf_ref().VISUAL_OUTPUT_PATH)
                new_path = str(ht.correct_path(cf_ref().VISUAL_OUTPUT_PATH, filename[:-4])) + 'growth' + str(
                    cf_ref().GROWTH_PIXELS) + \
                           'mask' + cf_ref().tiff_ext
                masks, rows, cols = segmenter_ref().segment_image(im_nuclear_image)
                del segmenter, segmenter_ref, im_nuclear_image
                gc.collect()
                logger.info('Stitching: ' + str(filename))
                stitched_mask = CVMask(stitcher_ref().stitch_masks(masks, rows, cols))
                del stitcher, stitcher_ref
                gc.collect()
                if len(masks) == 1:
                    logger.warning(
                        'There was no cropping for segmentation of ' + str(filename) + ', skipping to next')
                    continue
                # inside the stitcher, split the masks back into crops
                del masks, rows, cols
                gc.collect()
                instances = stitched_mask.n_instances()
                logger.info(str(instances) + ' cell masks found by segmenter')
                if instances == 0:
                    # logger.warning('No cells found in ' + filename + ', skipping to next')
                    logger.warning('No cells found in ' + str(filename) + ', skipping to next')
                    h, w, c = cf_ref().SHAPE
                    Image.new(mode='I', size=(w, h)).save(new_path)
                    del h, w, c
                    gc.collect()
                else:
                    logger.info('Growing cells by ' + str(cf_ref().GROWTH_PIXELS) + ' pixels: ' + str(filename) +
                                "\nComputing centroids and bounding boxes for the masks.")
                    # masks = stitched_mask.flatmasks
                    # indices = np.where(masks != 0)
                    # values = masks[indices[0], indices[1]]
                    # if len(values.cf.SHAPE) > 1:
                    #    logger.warning('Image size ', str(cf.SHAPE), ' of the file ', filename, 'is too small to segment, '
                    #                                                                            'skipping to next')
                    #    continue
                    stitched_mask.compute_centroids()
                    stitched_mask.compute_boundbox()
                    if cf_ref().GROWTH_PIXELS > 0:
                        logger.info("Growing masks by " + str(cf_ref().GROWTH_PIXELS) + " pixels")
                        stitched_mask.grow_masks(cf_ref().GROWTH_PIXELS, cf_ref().GROWTH_METHOD)
                    # restitch and squash after growth
                    logger.info('Creating visual overlay output saved to ' + str(cf_ref().VISUAL_OUTPUT_PATH))
                    outlines = cvvisualize.generate_mask_outlines(stitched_mask.flatmasks)
                    del stitched_mask
                    gc.collect()
                    imsave(new_path, outlines, bigtiff=True)
                    del outlines
                    gc.collect()
                del instances
                gc.collect()
                # save intermediate progress in case of mid-run crash
                with open(cf_ref().PROGRESS_TABLE_PATH, "a") as myfile:
                    myfile.write(filename + "\n")
                del myfile, filename
                gc.collect()
            del ref_path, image_path
            gc.collect()
        del cf, cf_ref, filenames_to_process
        gc.collect()
