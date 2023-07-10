# multiplex.preparation_dapi_seg.py
import os
import cv2
import numpy as np
from PIL import Image
import multiplex.setup_logger
import logging
import multiplex.helpertools as ht
# multiplex.preparation_dapi_seg.py creates its own logger, as a sub logger to 'pipelineGUI.main'
logger = logging.getLogger('pipelineGUI.main.preparation_dapiSeg')


class PreparationDapiSeg:
    def __init__(self, input_dir, output_dir, dapi_str):
        self.input_folder = input_dir
        self.output_folder = output_dir
        self.dapi_str = dapi_str

    def process(self):
        # get all files of directory
        for subdir in [x[0] for x in os.walk(self.input_folder)]:
            for filename in os.listdir(subdir):
                if f"0{self.dapi_str}" in str(filename):
                    # adjust contrast of each files (substract 5 from intensity)
                    # subtract 5 from all pixels in our image and make it darker
                    image = cv2.imread(ht.correct_path(self.input_folder, subdir, filename))
                    m = np.ones(image.shape, dtype="uint8") * 5
                    subtracted = cv2.subtract(image, m)
                    file_folder_name = os.path.splitext(os.path.basename(filename))[0]
                    # create folders with files
                    filefolder_path = ht.correct_path(self.output_folder, file_folder_name)
                    if not os.path.exists(filefolder_path):
                        os.mkdir(filefolder_path)
                    output_path = ht.correct_path(filefolder_path, filename)
                    # create folder input
                    gray = cv2.cvtColor(subtracted, cv2.COLOR_BGR2GRAY)
                    sub = Image.fromarray(gray.astype(np.uint8))
                    sub.save(output_path)
                    f = open(ht.correct_path(self.output_folder, "channelNames_" + file_folder_name + ".txt"), "w+")
                    f.write(filename)
                    f.close()
        logger.info('Preparation of input for dapi segmentation is finished')
