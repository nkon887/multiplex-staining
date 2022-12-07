import os
import sys
import time

from ij import IJ
from ij.io import FileSaver
from ij.plugin import Concatenator
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/multiplex-staining/py_pipeline"))
import config
import jythontools as jt
import pythontools as pt


def main():
    input_dir = config.hyperstacksDir
    out_dir = config.concatenatesDir
    subfolders = [x[0] for x in os.walk(input_dir)]
    subfolders.pop(0)
    if not subfolders:
        print(input_dir + " is empty. Doing nothing")
    force_save = jt.ask_to_overwrite()
    for subfolder in subfolders:
        hs_files = []
        concatenate_path = os.path.join(out_dir, os.path.basename(subfolder) + config.tiff_ext).replace("\\", "/")
        if (not os.path.exists(concatenate_path)) or force_save:
            for hs in os.listdir(subfolder):
                if config.cropped_suffix in os.path.basename(hs):
                    print("Found cropped hyperstack " + str(hs))
                    stack_to_crop_path = os.path.join(subfolder, hs)
                    imp = IJ.openImage(stack_to_crop_path)
                    hs_files.append(imp)
                else:
                    continue
            if hs_files:
                print(
                    "Saving the concatenate of the hyperstacks from the subfolder " + str(os.path.basename(subfolder)))
                FileSaver(Concatenator.run(hs_files)).saveAsTiff(concatenate_path)
        else:
            print("The concatenated tiff file " + concatenate_path + " exists. Skipping")
    print("stepFour concatenation is finished")


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
