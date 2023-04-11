import os
import sys
import time
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import config
from stitching import stitchingTools
import pythontools as pt
def processing():

    print("Stitching")
    # start
    start_time = time.time()
    stitchingTools(config.stitch_input_dir, config.input_dir, config.czi_ext, config.tiff_ext).process()
    end_time = time.time()
    print("\nDuration of the program execution:")
    stitching_time = pt.convert(end_time - start_time)
    print(stitching_time)
    # End of stitching


if __name__ in ['__builtin__', '__main__']:
    processing()
    System.exit(0)