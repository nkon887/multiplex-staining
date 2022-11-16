import os
import sys
from ij.io import FileSaver
from ij import IJ
from ij.plugin import Concatenator

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config

ext = ".tif"
hsDir = config.hyperstacksDir
outDir = config.concatenatesDir
hsFiles = []
concatenate_path = os.path.join(outDir, "concatenate" + ext).replace("\\", "/")
for hs in os.listdir(hsDir):
    if "_Cropped" in os.path.basename(hs):
        stackToCropPath = os.path.join(hsDir, hs)
        imp = IJ.openImage(stackToCropPath)
        hsFiles.append(imp)
FileSaver(Concatenator.run(hsFiles)).saveAsTiff(concatenate_path)