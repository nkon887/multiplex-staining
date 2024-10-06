import os
import sys
import logging

from ij import IJ, ImagePlus, ImageStack
from ij.gui import WaitForUserDialog, Toolbar
from ij.io import FileSaver

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
from cropped_stack import CroppedStack

# im-jy-package.cropping.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.CROPPING')


class Cropping:
    def __init__(self, step, input_dir, target_dir, error_subfolder_name, tiff_ext, cropped_suffix):
        self.input_dir = input_dir
        self.target_dir = target_dir
        self.error_subfolder_name = error_subfolder_name
        self.tiff_ext = tiff_ext
        self.force_save = ht.ask_to_overwrite(step)
        self.cropped_suffix = cropped_suffix
        self.tempfile = os.path.join(self.input_dir, "temp.csv")

    def infos_func(self):
        imagejversion = IJ.getVersion()
        logger.info("Current IMAGEJ version: " + imagejversion)
        if self.force_save is None:
            # user canceled dialog
            return

    def processing_before_alignment(self):
        subfolders = [x[0].replace("\\", "/") for x in os.walk(self.input_dir)]
        subfolders.pop(0)
        if not subfolders:
            logger.warning(self.input_dir + " is empty. Doing nothing")

        self.infos_func()
        for subfolder in subfolders:
            tiff_files = []
            for tiff_file in os.listdir(subfolder):
                path = ht.correct_path(subfolder, tiff_file)
                if not ((self.error_subfolder_name in tiff_file) or (self.error_subfolder_name in subfolder)) and \
                        os.path.isfile(path) and (tiff_file.endswith(self.tiff_ext)):
                    tiff_files.append(tiff_file)
            first_roi = []
            imps = []
            tiff_cropped_paths = []
            for tiff_file in tiff_files:
                logger.info("Processing the tiff file " + tiff_file)
                path = ht.correct_path(subfolder, tiff_file)
                imp = IJ.openImage(path)
                stack = imp.getStack()
                for i in range(1, stack.size() + 1):
                    tiff_cropped_path = ht.correct_path(self.target_dir, os.path.basename(tiff_file).split('.')[0],
                                                        stack.getSliceLabel(i))
                    tiff_cropped_paths.append(tiff_cropped_path)
                # Save output
                if (not all(os.path.exists(tiff_cropped_path) for tiff_cropped_path in
                            tiff_cropped_paths)) or self.force_save:
                    path = ht.correct_path(subfolder, tiff_file)
                    try:
                        width, height = ht.dimensions_of(path, self.input_dir, self.error_subfolder_name)
                        if [width, height] and imp not in imps:
                            imps.append(imp)
                            if not (imp.isStack() or imp.isHyperStack()):
                                logger.warning("The input " + tiff_file + "is neither the Stack nor Hyperstack. "
                                                                          "Skipping")
                                continue
                    except:
                        logger.exception(sys.exc_info())
                        continue
                else:
                    imp.close()
                    logger.warning("The cropped tiff files of " + subfolder + " exists. Skipping")

            if imps:
                for imp in imps:
                    imp.show()
                    # ask the user to define a selection and get the bounds of the selection
                    if not first_roi:
                        IJ.setTool(Toolbar.RECTANGLE)
                        WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
                        roi = imp.getRoi()
                        first_roi.append(roi)
                    else:
                        imp.setRoi(first_roi[0])
                WaitForUserDialog("Adjust the area,then click OK.").show()
                j = 0
                logger.info("Cropping...")
                for imp in imps:
                    imp.changes = False
                    roi = imp.getRoi()
                    imp.setRoi(roi)
                    # duplicate and crop image
                    stack = imp.getStack()
                    cropped_stack = CroppedStack(stack, roi)
                    for i in range(1, cropped_stack.size() + 1):
                        tempSlice = ImagePlus(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
                        tiff_cropped_path = os.path.dirname(tiff_cropped_paths[j])
                        if not os.path.exists(tiff_cropped_path):
                            os.mkdir(tiff_cropped_path)
                        file_path = tiff_cropped_paths[j].replace("\\", "/")
                        if not os.path.exists(file_path) or self.force_save:
                            FileSaver(tempSlice).saveAsTiff(file_path)
                        j += 1
                    imp.close()
        logger.info("Run is finished")

    def processing_after_alignment(self):
        self.infos_func()
        tiff_files = []
        coordinates = []
        folder_files = os.listdir(self.input_dir)
        logger.info("The input directory: " + self.input_dir)
        if folder_files:
            for tiff_file in folder_files:
                if tiff_file.endswith(self.tiff_ext):
                    if not os.path.isdir(tiff_file) and not (self.cropped_suffix in os.path.basename(tiff_file) and
                                                             tiff_file.endswith(self.tiff_ext) or (
                                                                     self.error_subfolder_name in tiff_file) or (
                                                                     self.error_subfolder_name in self.input_dir)):
                        tiff_files.append(tiff_file)
        else:
            logger.warning(self.input_dir + " is empty. Doing nothing")
        if not os.path.exists(self.tempfile):
            logger.warning("No csv file with coordinates was found. The coordinates have to be set manually.")
        else:
            try:
                coordinates = ht.read_data_from_csv(self.tempfile)
            except:
                logger.exception("Could not get the input parameters. Exiting")
                return
        for tiff_file in tiff_files:
            logger.info("Processing the tiff file " + tiff_file)
            tiff_cropped_path = ht.correct_path(self.input_dir, os.path.basename(tiff_file).split('.')[0] +
                                                self.cropped_suffix + self.tiff_ext)
            # Save output
            if (not os.path.exists(tiff_cropped_path)) or self.force_save:
                path = ht.correct_path(self.input_dir, tiff_file)
                try:
                    width, height = ht.dimensions_of(path, self.input_dir, self.error_subfolder_name)
                    if [width, height]:
                        imp = IJ.openImage(path)
                        if not (imp.isStack() or imp.isHyperStack()):
                            logger.warning("The input " + tiff_file + " is neither the Stack nor Hyperstack. Skipping")
                            continue
                except:
                    logger.exception(sys.exc_info())
                    continue
                imp.show()
                coord = []
                if coordinates:
                    if 'patientID' in coordinates[0].keys() and 'fiji_coordinates' in coordinates[0].keys():
                        coord = [int(x) for case in coordinates if case['patientID'] == os.path.basename(tiff_file).split('.')[0] for x in case['fiji_coordinates'].split(";") if case['fiji_coordinates']]
                    #logger.info(coord)
                if coord:
                    imp.setRoi(coord[0], coord[1], coord[2], coord[3])
                # ask the user to define a selection and get the bounds of the selection
                IJ.setTool(Toolbar.RECTANGLE)
                WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
                roi = imp.getRoi()
                imp.setRoi(roi)
                roi_width = int(roi.getFloatWidth())
                roi_height = int(roi.getFloatHeight())
                stack = imp.getStack()
                logger.info("Cropping...")
                cropped_stack = CroppedStack(stack, roi)
                res_stack = ImageStack(roi_width, roi_height)
                for i in range(1, cropped_stack.size() + 1):
                    res_stack.addSlice(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
                cropped = ImagePlus("cropped", res_stack)
                # keep the same image calibration
                cropped.setCalibration(imp.getCalibration().copy())
                # save
                logger.info("Saving the cropped hyperstack as " + tiff_cropped_path)
                FileSaver(cropped).saveAsTiff(tiff_cropped_path)
                imp.close()

            else:
                logger.warning("The cropped tiff file " + tiff_cropped_path + " exists. Skipping")
        logger.info("Run is finished")
