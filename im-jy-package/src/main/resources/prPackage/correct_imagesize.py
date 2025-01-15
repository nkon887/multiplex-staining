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
    def __init__(self, step, tiff_ext, input_dir, input_origin_dir, output_dir, forceSave):
        self.input_dir = input_dir
        self.inputOrigin_dir = input_origin_dir
        self.tiff_ext = tiff_ext
        self.output_dir = output_dir
        # self.force_save = ht.ask_to_overwrite(step)
        self.force_save = int(forceSave[0])

    def find_all(self, name, path):
        result = []
        for root, dirs, files in os.walk(path):
            if name in files:
                result.append(os.path.join(root, name))
        return result

    def action(self, filename):
        invert_var = 0
        filepath = ht.correct_path(self.input_dir, filename)
        imp = IJ.openImage(filepath)
        IJ.run(imp, "Create Selection", "")
        roi = imp.getRoi()
        RM = RoiManager()
        rm = RM.getRoiManager()
        rm.runCommand("Associate", "true")
        rm.runCommand("Show All with labels")
        logger.info("Processed file in " + self.input_dir + " is " + filename)
        if roi:
            rm.addRoi(roi)
            file_split = filename[0:len(filename) - 15]
            logger.info("File used in " + self.inputOrigin_dir + " is " + file_split)
            # subfolder_name = filename.split("_")[1]
            origin_file = file_split + self.tiff_ext
            orig_imp_paths = self.find_all(origin_file, self.inputOrigin_dir)
            if orig_imp_paths:
                orig_imp = IJ.openImage(orig_imp_paths[0])
                orig_imp.show()
                IJ.selectWindow(orig_imp.getTitle())
                roi_mask = RoiManager.getInstance().getRoisAsArray()[0]
                IJ.selectWindow(orig_imp.getTitle())
                imp_ori = IJ.getImage()
                imp_ori.setRoi(roi_mask)
                mask = imp_ori.createRoiMask()
                FileSaver(ImagePlus("Mask", mask)).saveAsTiff(ht.correct_path(self.output_dir, filename))
                rm.runCommand(imp_ori, "Deselect")
                rm.runCommand(imp_ori, "Delete")
                IJ.run("Close")
            else:
                logger.warning("No segmented file " + origin_file + " can be found in " + self.inputOrigin_dir)
            while WindowManager.getImageCount() > 0:
                for imp in [WindowManager.getImage(id) for id in WindowManager.getIDList()]:
                    IJ.selectWindow(imp.getTitle())
                    imp.close()
        else:
            FileSaver(imp).saveAsTiff(ht.correct_path(self.output_dir, filename))
            IJ.run("Close")

    def processing(self):
        logger.info("Current IMAGEJ version: " + IJ.getVersion())
        filelist = [item for item in os.listdir(self.input_dir)]
        output_paths = []
        for i in range(len(filelist)):
            output_paths.append(ht.correct_path(self.output_dir, filelist[i]))
        if (not all(os.path.exists(output_path) for output_path in
                    output_paths)) or self.force_save == 1:
            for i in range(len(filelist)):
                logger.info("Processing the file " + str(filelist[i]))
                self.action(filelist[i])
        else:
            # logger.warning("The files of " + self.output_dir + " exists. Force save is not enabled. Skipping")
            logger.warning("The files of " + self.output_dir + " exists or there is no input data to process. "
                                                               "Force save is not enabled. Skipping")
        logger.info("Run is finished")
