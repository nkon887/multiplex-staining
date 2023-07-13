import os
import sys
import logging

from ij import IJ, WindowManager, ImagePlus, VirtualStack
from ij.plugin.frame import RoiManager
from ij.io import FileSaver

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht

# im-jy-package.correct_imagesize.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.DAPISEG_RESIZER')


class DapiSeg_Resizer:
    def __init__(self, tiff_ext, input_dir, input_origin_dir, output_dir):
        self.input_dir = input_dir
        self.inputOrigin_dir = input_origin_dir
        self.tiff_ext = tiff_ext
        self.output_dir = output_dir

    def action(self, filename):
        filepath = ht.correct_path(self.input_dir, filename)
        imp = IJ.openImage(filepath)
        IJ.run(imp, "Create Selection", "")
        roi = imp.getRoi()
        RM = RoiManager()
        rm = RM.getRoiManager()
        rm.runCommand("Associate", "true")
        rm.runCommand("Show All with labels")
        rm.addRoi(roi)
        print(filename)
        file_split = filename[0:len(filename) - 15]
        print(file_split)
        subfolder_name = filename.split("_")[1]
        origin_file = file_split + self.tiff_ext
        orig_imp = IJ.openImage(ht.correct_path(self.inputOrigin_dir, subfolder_name, origin_file))
        orig_imp.show()
        IJ.selectWindow(orig_imp.getTitle())
        roi = RoiManager.getInstance().getRoisAsArray()[0]
        IJ.selectWindow(orig_imp.getTitle())
        imp = IJ.getImage()
        imp.setRoi(roi)
        mask = imp.createRoiMask()
        FileSaver(ImagePlus("Mask", mask)).saveAsTiff(ht.correct_path(self.output_dir, filename))
        rm.runCommand(imp, "Deselect")
        rm.runCommand(imp, "Delete")
        IJ.run("Close")
        while WindowManager.getImageCount() > 0:
            for imp in [WindowManager.getImage(id) for id in WindowManager.getIDList()]:
                IJ.selectWindow(imp.getTitle())
                imp.close()

    def processing(self):
        imagejversion = IJ.getVersion()
        logger.info("Current IMAGEJ version: " + imagejversion)
        filelist = [item for item in os.listdir(self.input_dir)]
        for i in range(len(filelist)):
            output_file = ht.correct_path(self.output_dir, filelist[i])
            logger.info("Processing the file " + str(filelist[i]))
            self.action(filelist[i])
        logger.info("Run is finished")

