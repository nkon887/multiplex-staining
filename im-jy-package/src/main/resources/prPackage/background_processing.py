import os
import sys
import logging

from ij import IJ, ImagePlus
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
import config

# background_processing.py creates its own logger, as a sub logger to 'pipelineGUI.macro.main.BACKGROUNDADJUSTMENT'
logger = logging.getLogger('pipelineGUI.macro.main.BACKGROUNDADJUSTMENT')


class BackgroundAdjustment:
    def __init__(self, input_dir, output_dir, tiff_ext):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tiff_ext = tiff_ext

    def get_list_of_indices(self, stack):
        filenames = []
        for sliceIndex in range(1, stack.getSize() + 1):
            filenames.append(stack.getSliceLabel(sliceIndex))
        markers = []
        exception = "copy"
        for filename in filenames:
            filename_list = filename.split("_")
            if exception not in filename:
                markers.append(filename_list.pop().split(".")[0])
            else:
                temp = filename_list.index(exception)
                markers.append(filename_list[temp - 1])
        markers = list(set(markers))
        marker_stack_indices_groups = {}
        for marker in markers:
            filenames_list = [filename for filename in filenames if "_" + marker + self.tiff_ext in filename]
            filenames_list = list(set(filenames_list))
            slice_indices = []
            for filename in filenames_list:
                slice_indices = slice_indices + [i + 1 for i, x in enumerate(filenames) if x == filename]
            marker_stack_indices_groups[marker] = slice_indices

        return filenames, marker_stack_indices_groups

    def get_keys_from_value(self, d, val):
        return [k for k, v in d.items() if v == val]

    def ask_for_bg_parameters(self, markers):
        gui = GenericDialog("Background Parameter Settings")
        gui.addMessage("Radius values for the markers:")
        for i, marker in enumerate(markers):
            gui.addNumericField(marker, 50, 0)  # 0 for no decimal part
            if i < 5 and i < len(markers) - 1:
                gui.addToSameRow()
        #            gui.addCheckbox("createBackground", False)
        #            gui.addToSameRow()
        #            gui.addCheckbox("lightBackground", False)
        #            gui.addToSameRow()
        #            gui.addCheckbox("useParaboloid", False)
        #            gui.addToSameRow()
        #            gui.addCheckbox("doPresmooth", False)
        #            gui.addToSameRow()
        #            gui.addCheckbox("correctCorners", False)
        gui.addMessage("Overwrite option")
        gui.addCheckbox("forceSave", False)
        gui.showDialog()

        if gui.wasCanceled():
            logger.warning("User canceled dialog! Doing nothing. Exit")
            return
        params = {}
        for marker in markers:
            params[marker] = {
                "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
                # "createBackground": gui.getNextBoolean(),
                # "lightBackground": gui.getNextBoolean(),
                # "useParaboloid": gui.getNextBoolean(),
                # "doPresmooth": gui.getNextBoolean(),
                # "correctCorners": gui.getNextBoolean(),
                "createBackground": False,
                "lightBackground": False,
                "useParaboloid": False,
                "doPresmooth": False,
                "correctCorners": False,
            }
        force_save = gui.getNextBoolean()

        return params, force_save

    def processing(self):
        imagejversion = IJ.getVersion()
        logger.info("Current IMAGEJ version: " + imagejversion)
        input_dir = self.input_dir
        output_dir = self.output_dir
        tiff_files = []
        all_files = os.listdir(input_dir)
        if all_files:
            for tiff_file in all_files:
                if not (os.path.isdir(tiff_file)) and config.cropped_suffix in os.path.basename(tiff_file) and \
                        tiff_file.endswith(self.tiff_ext):
                    tiff_files.append(tiff_file)
            if tiff_files:
                # Subtract background
                bs = BackgroundSubtracter()
                markers = []
                imp = IJ.openImage(ht.correct_path(input_dir, (next(iter(tiff_files)))))
                imp.show()
                imp.changes = False
                stack = imp.getStack()
                _, markerslice_groups = self.get_list_of_indices(stack)
                imp.close()
                markers = list(set(markerslice_groups.keys()))
                try:
                    params_bg, force_save = self.ask_for_bg_parameters(markers)
                except:
                    logger.warning("user canceled dialog. Exit")
                    return

                for tiff_file in tiff_files:
                    logger.info("Processing the file " + str(tiff_file))
                    imp = IJ.openImage(ht.correct_path(input_dir, tiff_file))
                    imp.show()
                    imp.changes = False
                    stack = imp.getStack()
                    filenames, markerslice_groups = self.get_list_of_indices(stack)
                    for sliceIndex in range(1, stack.getSize() + 1):
                        filename = str(stack.getSliceLabel(sliceIndex)).split(".")[0]
                        # Save output
                        ip = stack.getProcessor(sliceIndex)
                        slice_file_name_three = ''
                        slice_file_name_four = ''
                        marker = ''
                        subfolder_name = os.path.basename(tiff_file).split('.')[0].split("_")[0]
                        subfolder_path = ht.setting_directory(output_dir, subfolder_name)
                        for marker in markerslice_groups.keys():
                            if sliceIndex in [x for x in markerslice_groups.get(marker)]:
                                logger.info(
                                    "Saving the slice " + str(sliceIndex) + " " + str(stack.getSliceLabel(sliceIndex)))
                                logger.info("Slice " + str(sliceIndex) + " is in " + str(marker))
                                slice_file_name_three = ht.correct_path(subfolder_path,
                                                                        filename + "_noBackgroundSub"
                                                                        + config.tiff_ext)
                                slice_file_name_four = ht.correct_path(subfolder_path, filename + "_backgroundSub" +
                                                                       config.tiff_ext)
                                # Save output
                                if (not os.path.exists(slice_file_name_three)) or force_save:
                                    temp = ImagePlus(str(sliceIndex), ip)
                                    IJ.run(temp, "8-bit", "")
                                    FileSaver(temp).saveAsTiff(slice_file_name_three)
                                else:
                                    logger.warning(slice_file_name_three + " exists. Doing nothing. Skipping")
                                if (not os.path.exists(slice_file_name_four)) or force_save:
                                    bs.rollingBallBackground(ip, params_bg[marker]["radius"],
                                                             params_bg[marker]["createBackground"],
                                                             params_bg[marker]["lightBackground"],
                                                             params_bg[marker]["useParaboloid"],
                                                             params_bg[marker]["doPresmooth"],
                                                             params_bg[marker]["correctCorners"])
                                    temp = ImagePlus(str(sliceIndex), ip)
                                    IJ.run(temp, "8-bit", "")
                                    FileSaver(temp).saveAsTiff(slice_file_name_four)
                                else:
                                    logger.warning(slice_file_name_four + " exists. Doing nothing. Skipping")
                    imp.close()
                IJ.run("Close All")
            else:
                logger.warning("No tif file found")
        else:
            logger.warning(input_dir + " is empty. Doing nothing")
        logger.info("Run is finished")
