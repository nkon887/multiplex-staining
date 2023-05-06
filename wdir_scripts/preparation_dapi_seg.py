import os
import sys
import cv2
import numpy as np
import time

sys.path.append(os.path.abspath(os.getcwd()))

import config
import pythontools as pt
from PIL import Image


class PreparationDapiSeg:
    def __init__(self, input_dir, output_dir):
        self.input_folder = input_dir
        self.output_folder = output_dir

    def process(self):
        # get all files of directory
        for subdir in [x[0] for x in os.walk(self.input_folder)]:
            for filename in os.listdir(subdir):
                if "0dapi" in str(filename):
                    # adjust contrast of each files (substract 5 from intensity)
                    # subtract 5 from all pixels in our image and make it darker
                    image = cv2.imread(os.path.join(self.input_folder, subdir, filename))
                    M = np.ones(image.shape, dtype="uint8") * 5
                    subtracted = cv2.subtract(image, M)
                    file_folder_name = os.path.splitext(os.path.basename(filename))[0]
                    # create folders with files
                    filefolder_path = os.path.join(self.output_folder, file_folder_name)
                    if not os.path.exists(filefolder_path):
                        os.mkdir(filefolder_path)
                    output_path = os.path.join(filefolder_path, filename)
                    # create folder input
                    gray = cv2.cvtColor(subtracted, cv2.COLOR_BGR2GRAY)
                    sub = Image.fromarray(gray.astype(np.uint8))
                    sub.save(output_path)
                    f = open(os.path.join(self.output_folder, "channelNames_" + file_folder_name + ".txt"), "w+")
                    f.write(filename)
                    f.close()
        print('Preparation of input for dapi segmentation is finished')


def main():
    PreparationDapiSeg(config.bg_adjust_dir, config.dapi_seg_input_dir).process()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
