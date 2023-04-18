import os
import sys

from ij import IJ, WindowManager, ImagePlus, VirtualStack
from ij.plugin.frame import RoiManager
from ij.io import FileSaver
sys.path.append(os.path.abspath(os.getcwd()))


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
        imp = IJ.openImage(os.path.join(self.input_dir, filename))
        IJ.run("Create Selection", "")
        roi = imp.getRoi()
        #IJ.run("ROI Manager...")
        RM = RoiManager()
        rm = RM.getRoiManager()
        rm.runCommand("Associate", "true")
        rm.runCommand("Show All with labels")
        rm.addRoi(roi)
        print(filename)
        file_split=filename[0:len(filename)-15]
        print(file_split)
        origin_file = file_split+self.tiff_ext
        IJ.openImage(os.path.join(self.inputOrigin_dir, origin_file))
        IJ.selectWindow(origin_file)
        rm.select(0)
        IJ.selectWindow(origin_file)
        mask = imp.createRoiMask()
        FileSaver(mask).saveAsTiff(os.path.join(self.output_dir,filename))
        rm.runCommand(imp,"Deselect")
        rm.runCommand(imp, "Delete")
        IJ.run("Close")
        while WindowManager.getImageCount() > 0:
            for imp in [WindowManager.getImage(id) for id in WindowManager.getIDList()]:
                IJ.selectImage(imp.getTitle())
                imp.close()