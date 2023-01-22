import os
import sys
import time

from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import pythontools as pt
import config
from cropping import Cropping


def main():
    Cropping(config.stacks_dir, config.cropped_stacks_dir, config.error_subfolder_name,
             config.tiff_ext, config.cropped_suffix).processing_before_alignment()


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
