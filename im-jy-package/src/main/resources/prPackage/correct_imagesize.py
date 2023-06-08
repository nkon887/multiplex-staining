import os
import sys

from ij import IJ, WindowManager, ImagePlus, VirtualStack
from ij.plugin.frame import RoiManager
from ij.io import FileSaver

sys.path.append(os.path.abspath(os.getcwd()))
import logging

# correct_imagesize.py creates its own logger, as a sub logger to 'pipelineGUI.macro.main.DAPISEG_RESIZER'
logger = logging.getLogger('pipelineGUI.macro.main.DAPISEG_RESIZER')

class DapiSeg_Resizer:
    def __init__(self, tiff_ext, input_dir, input_origin_dir, output_dir):
        self.input_dir = input_dir
        self.inputOrigin_dir = input_origin_dir
        self.tiff_ext = tiff_ext
        self.output_dir = output_dir

        filelist = [item for item in os.listdir(self.input_dir)]
        for i in range(len(filelist)):
            output_file = os.path.join(self.output_dir, filelist[i])
            self.action(filelist[i])

    def action(self, filename):
        filepath = os.path.join(self.input_dir, filename)
        imp = IJ.openImage(filepath)
#        imp.show()
        IJ.run(imp, "Create Selection", "")
        roi = imp.getRoi()
        # IJ.run("ROI Manager...")
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
        orig_imp = IJ.openImage(os.path.join(self.inputOrigin_dir, subfolder_name, origin_file))
        orig_imp.show()
        IJ.selectWindow(orig_imp.getTitle())
        roi = RoiManager.getInstance().getRoisAsArray()[0]
        IJ.selectWindow(orig_imp.getTitle())
        imp = IJ.getImage()
        imp.setRoi(roi)
        mask = imp.createRoiMask()
        FileSaver(ImagePlus("Mask", mask)).saveAsTiff(os.path.join(self.output_dir, filename))
        rm.runCommand(imp, "Deselect")
        rm.runCommand(imp, "Delete")
        IJ.run("Close")
        while WindowManager.getImageCount() > 0:
            for imp in [WindowManager.getImage(id) for id in WindowManager.getIDList()]:
                IJ.selectWindow(imp.getTitle())
                imp.close()
