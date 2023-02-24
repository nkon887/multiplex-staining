import os
import sys
import cv2
import numpy as np
import time

sys.path.append(os.path.abspath(os.getcwd()))

import config
import pythontools as pt


class PreparationDapiSeg:
    def __init__(self, input_dir, output_dir):
        self.input_folder = input_dir
        self.output_folder = output_dir

    def process(self):
        # get all files of directory
        for filename in os.listdir(self.input_folder):
            if "dapi" in filename and "bg_sub" in filename:
                # adjust contrast of each files (substract 5 from intensity)
                # subtract 5 from all pixels in our image and make it darker
                image = cv2.imread(os.path.join(self.input_folder, filename))
                M = np.ones(image.shape, dtype="uint8") * 5
                subtracted = cv2.subtract(image, M)
                file_folder_name = os.path.splitext(os.path.basename(filename))[0]
                # create folders with files
                filefolder_path = os.path.join(self.output_folder, file_folder_name)
                if not os.path.exists(filefolder_path):
                    os.mkdir(filefolder_path)
                output_path = os.path.join(filefolder_path, filename)
                # create folder input
                cv2.imwrite(output_path, subtracted)
                cv2.waitKey(0)
                f = open(os.path.join(self.output_folder, "channelNames_" + file_folder_name + ".txt"), "w+")
                f.write(filename)
                f.close()


def main():
    PreparationDapiSeg(config.bg_adjust_dir, config.dapi_seg_input_dir).process()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))

# (get size of each image file and put in corresponding folder)
# setup cvconfig py
# start segmentation
# output new folder new file
