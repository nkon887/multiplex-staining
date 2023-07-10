# multiplex.postprocessing_dapi_seg.py
import os.path
import PIL
from PIL import Image
import cv2
import numpy as np
import multiplex.helpertools as ht
from skimage import exposure
PIL.Image.MAX_IMAGE_PIXELS = 933120000
import multiplex.setup_logger
import logging

# postprocessing_dapi_seg.py creates its own logger, as a sub logger to 'pipelineGUI.main'
logger = logging.getLogger('pipelineGUI.main.postprocessing_dapiSeg')


class PostProcessingDapiSeg:
    def __init__(self, input_dir, output_dir, tiff_ext):
        self.input_folder = input_dir
        self.output_folder = output_dir
        self.tiff_ext = tiff_ext

    def process(self):
        # Load with PIL
        for im in os.listdir(self.input_folder):
            image_file_path = ht.correct_path(self.input_folder, im)
            if im.endswith(self.tiff_ext) and not (os.path.isdir(im)):
                image_file = Image.open(image_file_path)

                # Make into Numpy array and normalise
                na = np.array(image_file, dtype=np.uint8)
                threshold = 0
                na[na > threshold] = 1
                contour, hier = cv2.findContours(na, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contour:
                    cv2.drawContours(na, [cnt], 0, 1, -1)

                se1 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                se2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

                mask = cv2.morphologyEx(na, cv2.MORPH_CLOSE, se1)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, se2)

                out = na * mask
                threshold = 0
                out[out > threshold] = 1
                # Save
                intimg = exposure.rescale_intensity(out, in_range=(0, 1))
                cv2.imwrite(ht.correct_path(self.output_folder, im), intimg)
        logger.info("Postprocessing is finished")
