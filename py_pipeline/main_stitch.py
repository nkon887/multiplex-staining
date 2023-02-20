import os
import sys
import time
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import config
from stitching import Stitcher
import pythontools as pt
def processing():

    print("Stitching")
    # start
    start_time = time.time()
    Stitcher("D:/bigImg/workingDir/01_input/220908_E37568-17-1D.czi", config.input_dir, config.tiff_ext).process()
    end_time = time.time()
    print("\nDuration of the program execution:")
    alignment_time = pt.convert(end_time - start_time)
    print(alignment_time)
    # End of stitching


if __name__ in ['__builtin__', '__main__']:
    # Start time
    start_time = time.time()
    processing()
    # End time
    end_time = time.time()
    # Total time
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
