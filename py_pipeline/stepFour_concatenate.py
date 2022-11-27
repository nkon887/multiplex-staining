import os
import sys
import time

from ij import IJ
from ij.io import FileSaver
from ij.plugin import Concatenator
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config
import jythontools as jt


def main():
    input_dir = config.hyperstacksDir
    out_dir = config.concatenatesDir
    subfolders = [x[0] for x in os.walk(input_dir)]
    subfolders.pop(0)
    force_save = jt.ask_to_overwrite()
    for subfolder in subfolders:
        hs_files = []
        concatenate_path = os.path.join(out_dir, os.path.basename(subfolder) + config.tiff_ext).replace("\\", "/")
        if (not os.path.exists(concatenate_path)) or force_save:
            for hs in os.listdir(subfolder):
                if "_Cropped" in os.path.basename(hs):
                    IJ.log("Found cropped hyperstack " + str(hs))
                    stack_to_crop_path = os.path.join(subfolder, hs)
                    imp = IJ.openImage(stack_to_crop_path)
                    hs_files.append(imp)
                else:
                    continue
            if hs_files:
                IJ.log(
                    "Saving the concatenate of the hyperstacks from the subfolder " + str(os.path.basename(subfolder)))
                FileSaver(Concatenator.run(hs_files)).saveAsTiff(concatenate_path)
    IJ.log("stepFour concatenation is finished")


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("Duration of the program execution:", )
    print(end_time - start_time)
    System.exit(0)
