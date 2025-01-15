import collections
import re
import sys
import os
from ij.gui import GenericDialog
from ij import IJ, WindowManager
from ij.io import FileSaver
import csv
import logging

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht

# im-jy-package.merging_channels.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.MERGING_CHANNELS')


class MergingChannels:
    def __init__(self, input_dir, output_dir, tiff_ext, dapi_str, work_dir, forceSave):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str
        self.work_dir = work_dir
        self.tempfile = os.path.join(self.work_dir, "temp_merge.csv")
        self.force_save = int(forceSave[0])

    def getting_input_parameters(self, dapi_files, markers):
        gui = GenericDialog("Channels")
        gui.addMessage("Choose dapi image  you want to use for merge")
        dapi_filenames = dapi_files.keys()
        length_dapi_filenames = len(dapi_filenames)
        for subfolder, i in zip(dapi_filenames, range(0, length_dapi_filenames)):
            dapis = dapi_files.get(subfolder)
            gui.addChoice("patient " + os.path.basename(subfolder) + ":", dapis, dapis[2])  # dapis[2] is default here
            if i % 2 == 0 and subfolder != dapi_filenames[len(dapi_filenames) - 1]:
                gui.addToSameRow()
        gui.addMessage("Choose images of channels you want to combine with dapi image")
        for marker, i in zip(markers, range(0, len(markers))):
            gui.addCheckbox(marker, False)
            if i % 2 == 0 and marker != markers[len(markers) - 1]:
                gui.addToSameRow()
        gui.addCheckbox("Select all markers", False)
        gui.addMessage("Overwrite option")
        # gui.addCheckbox("forceSave", False)
        gui.showDialog()

        if gui.wasCanceled():
            logger.warning("User canceled dialog! Doing nothing. Exit")
            return
        params = {}
        for subfolder in dapi_files.keys():
            params[self.dapi_str + subfolder] = gui.getNextChoice()
        for marker in markers:
            params[marker] = gui.getNextBoolean()
        all_Selected = gui.getNextBoolean()
        # force_save = gui.getNextBoolean()
        if all_Selected:
            for marker in markers:
                params[marker] = True
        # return params, force_save
        return params

    def get_channel_files(self, subfolder, marker):
        channel_files = []
        for subfolder_file in os.listdir(subfolder):
            pattern = r'^\d{6}[^{\.}]*'
            if marker in os.path.basename(subfolder_file) and re.match(pattern + self.tiff_ext,
                                                                       os.path.basename(subfolder_file)):
                channel_files.append(subfolder_file)
        return channel_files

    def merging(self, dapi_file, selected_channel_files, output_dir):
        for channel_file in selected_channel_files:
            subfolder_folder_path = ht.setting_directory(output_dir, os.path.basename(channel_file).split("_")[1])
            merged_filename = (os.path.basename(channel_file)).split(".")[0] + "_merged_dapi" + self.tiff_ext
            merged_file_path = ht.correct_path(subfolder_folder_path, merged_filename)
            if (not os.path.exists(merged_file_path)) or self.force_save == 1:
                logger.info("Channel file " + str(channel_file) + " to be merged with dapi file " + str(dapi_file))
                imp1 = IJ.openImage(dapi_file)
                imp1.show()
                imp2 = IJ.openImage(channel_file)
                imp2.show()
                IJ.run(imp1, "Merge Channels...",
                       "c1=" + os.path.basename(channel_file) + " c3=" + os.path.basename(dapi_file) + " keep")
                imp1.close()
                imp2.close()
                res = WindowManager.getCurrentImage()
                IJ.run(res, "Enhance Contrast", "saturated=0.35")
                logger.info("Saving the " + str(os.path.basename(merged_file_path)))
                FileSaver(res).saveAsTiff(merged_file_path)
                res.close()
            else:
                logger.warning("Skipping as " + str(os.path.basename(merged_file_path)) + " exists")

        IJ.run("Close All")

    def processing(self):
        logger.info("Current IMAGEJ version: " + IJ.getVersion())
        input_dir = self.input_dir
        output_dir = self.output_dir
        subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
        subfolders.pop(0)
        if not subfolders:
            logger.warning(input_dir + " is empty. Doing nothing")
            return
        if not os.path.exists(self.tempfile):
            logger.warning("No csv file was found. Something went wrong when setting the parameters in the the "
                           "dialog for setting the parameters for channel merging. The user may have cancelled it or "
                           "deleted it. Repeat the step if you want to merge the channel image "
                           "with the DAPI image and set the parameters. Doing nothing.")
            return
        try:
            data = ht.read_data_from_csv(self.tempfile)
        except:
            logger.exception("Could not get the input parameters. Exiting")
            return
        #force_save = True
        for subfolder in subfolders:
            selected_markers = [case['merge_selected_channels'].split(";") for case in data if
                                case['merge_patientID'] == os.path.basename(subfolder)]
            selected_markers = [item for sublist in selected_markers for item in sublist]
            selected_channel_files = []
            for marker in selected_markers:
                selected_channel_files = selected_channel_files + self.get_channel_files(subfolder,
                                                                                         marker)
            selected_dapi_image = [case['merge_selected_dapi_file'] for case in data if
                                   case['merge_patientID'] == os.path.basename(subfolder)]
            a = [case['merge_patientID'] for case in data]
            # logger.info("data " + str(a) + "subfolder " + os.path.basename(subfolder) + "selected dapi image " + str(selected_dapi_image) + "subfolder " + str(subfolder))
            if not selected_dapi_image:
                continue
            else:
                selected_dapi_image_path = ht.correct_path(subfolder, selected_dapi_image[0])
                # selected_force_save = [case['merge_forceSave'] for case in data if
                #                       case['merge_patientID'] == os.path.basename(subfolder)]
                selected_channel_files_paths = []
                for selected_channel_file in selected_channel_files:
                    selected_channel_files_paths.append(
                        ht.correct_path(subfolder, selected_channel_file))
                # if selected_force_save[0] == "Not Selected":
                #     force_save = False
                self.merging(selected_dapi_image_path, selected_channel_files_paths, output_dir)
