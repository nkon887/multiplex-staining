import os.path
import time
import sys
import PIL
from PIL import Image
import cv2
import numpy as np
from skimage import exposure

sys.path.append(os.path.abspath(os.getcwd()))

import pythontools as pt

PIL.Image.MAX_IMAGE_PIXELS = 933120000


class PostProcessingDapiSeg:
    def __init__(self, input_dir, output_dir):
        self.input_folder = input_dir
        self.output_folder = output_dir

    def process(self):
        # Load with PIL
        for im in os.listdir(self.input_folder):
            image_file_path = os.path.join(self.input_folder, im)
            # print(image_file_path)
            if im.endswith(".tif") and not (os.path.isdir(im)):
                # print(image_file_path)
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
                # print(str(out))
                threshold = 0
                out[out > threshold] = 1
                # Save
                intimg = exposure.rescale_intensity(out, in_range=(0, 1))
                cv2.imwrite(os.path.join(self.output_folder, im), intimg)
                print("done")


def main():
    PostProcessingDapiSeg("S:/C13/Microscopy-core/zkobus/230220_Copies_DAPI_for_new_masks/output/visual_output",
                          "S:/C13/Microscopy-core/zkobus/230220_Copies_DAPI_for_new_masks/output/binary").process()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
