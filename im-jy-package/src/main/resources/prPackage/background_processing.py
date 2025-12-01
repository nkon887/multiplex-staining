# -*- coding: utf-8 -*-
import os
import re
import sys
import logging

from ij import IJ, ImagePlus
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
import config

# im-jy-package.background_processing.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.BACKGROUNDADJUSTMENT')


class BackgroundAdjustment:
    def __init__(self, txt_dir, infos_txt, working_dir, metadata_csv_file, input_dir, output_dir, tiff_ext, csv_ext,
                 forceSave):
        self.txt_dir = txt_dir
        self.infos_txt = infos_txt
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tiff_ext = tiff_ext
        self.metadata_csv_file = metadata_csv_file
        self.working_dir = working_dir
        self.tempfile_bg = os.path.join(self.working_dir, "temp_bg.csv")
        self.csv_ext = csv_ext
        self.force_save = int(forceSave[0])

    def get_patientIDs_from_csv_file(self):
        try:
            # Get list of files in working_dir
            file_list = os.listdir(self.working_dir)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(self.working_dir, f)) and f.lower().endswith(
                self.csv_ext) and f.lower() == self.metadata_csv_file
        ]
        # logger.info(ht.correct_path(self.working_dir, fnames[0]))
        dates_patients_channels_markers_dict = {}
        # channels_markers_out = []
        patientIDs = []
        if len(fnames) == 1:
            data = ht.read_data_from_csv(ht.correct_path(self.working_dir, self.metadata_csv_file))
            for dic in data:
                patientIDs.append(dic["expID"])
        patientIDs = dict.fromkeys(patientIDs)

        return patientIDs

    def get_list_of_indices(self, input_dir, tiff_files):
        tiff_files_together = []
        # all_markers_together_from_txt = self.read_markers_from_txt_file()
        all_markers_together_from_csv = self.read_markers_from_csv_file()
        # logger.info(all_markers_together_from_csv)
        all_markers_together_from_stacks = []
        if tiff_files:
            for tiff_file in tiff_files:
                logger.info("The following image file will be processed " + tiff_file)
                tiff_file_dict = {}
                tiff_file_dict['tiff_file'] = tiff_file
                imp = IJ.openImage(ht.correct_path(input_dir, tiff_file))
                imp.show()
                imp.changes = False
                stack = imp.getStack()
                filenames = []
                markers = []
                for sliceIndex in range(1, stack.getSize() + 1):
                    filenames.append(stack.getSliceLabel(sliceIndex))
                imp.close()
                tiff_file_dict['filenames'] = filenames
                exception = "copy"
                if filenames:
                    for filename in filenames:
                        if filename is not None:
                            #logger.info("filename: " + filename)
                            filename_list = filename.split("_")
                            if exception not in filename:
                                markers.append(filename_list.pop().split(".")[0])
                            else:
                                temp = filename_list.index(exception)
                                markers.append(filename_list[temp - 1])
                    markers = list(set(markers))
                    if not markers:
                        logger.warning("The image file " +tiff_file+ " has slices without names containing [date]_[patientID]_[marker]. Please redo the previous steps (stitching,datacheck,alignment and cropping using the pipeline according to the workinstructions. The further processing may cause errorprone output")
                    tiff_file_dict['markers'] = markers
                    all_markers_together_from_stacks.append(markers)
                    marker_stack_indices_groups = {}
                    for marker in markers:
                        filenames_list = [filename for filename in filenames if "_" + marker + self.tiff_ext in filename]
                        filenames_list = list(set(filenames_list))
                        slice_indices = []
                        for filename in filenames_list:
                            slice_indices = slice_indices + [i + 1 for i, x in enumerate(filenames) if x == filename]
                        marker_stack_indices_groups[marker] = slice_indices
                    tiff_file_dict['marker_indices'] = marker_stack_indices_groups
                    tiff_files_together.append(tiff_file_dict)
        # all_markers_together_from_stacks = list(
        #    set([num for sublist in all_markers_together_from_stacks for num in sublist]))
        # if all_markers_together_from_txt:
        #    all_markers_together = all_markers_together_from_txt
        # else:
        #    all_markers_together = all_markers_together_from_stacks
        # return tiff_files_together, all_markers_together
        return tiff_files_together

    def read_markers_from_txt_file(self):
        channel_markers = []
        folder = self.txt_dir
        logger.info(folder)
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(self.infos_txt)
        ]
        logger.info(ht.correct_path(folder, fnames[0]))
        if len(fnames) == 1:
            with open(ht.correct_path(folder, fnames[0])) as f:
                # read all lines in a list
                lines = f.readlines()
                for i, line in enumerate(lines):
                    # check if string present on a current line
                    if not re.match(r'^\d{6}$', line):
                        channel_marker_str = lines[i].strip()
                        channel_marker_list = channel_marker_str.split(" ")
                        check_length = len(channel_marker_list)
                        if check_length == 2:
                            channel_markers.append(channel_marker_list[1])
        channel_markers = list(set(channel_markers))
        return channel_markers

    def read_markers_from_csv_file(self):
        folder = self.working_dir
        # logger.info(folder)
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(
                self.csv_ext) and f.lower() == self.metadata_csv_file
        ]
        # logger.info(ht.correct_path(folder, fnames[0]))
        channels_markers_out = []
        if len(fnames) == 1:
            data = ht.read_data_from_csv(ht.correct_path(folder, self.metadata_csv_file))
            for dic in data:
                channels_markers = {}
                channel_list = [key for key in dic.keys() if
                                "channel" in key and "marker" not in key and dic[
                                    key] != ""]
                channel_list_markers = [key for key in channel_list]
                for ch in channel_list_markers:
                    channels_markers[ch] = dic[ch]
                for ch in channels_markers:
                    channels_markers_out = channels_markers_out + [dic["marker for " + ch]]
        channels_markers_out = list(set(channels_markers_out))
        return channels_markers_out

    def get_keys_from_value(self, d, val):
        return [k for k, v in d.items() if v == val]

    def ask_for_bg_parameters(self, markers):
        gui = GenericDialog("Background Parameter Settings")
        gui.addMessage("Radius values for the markers:")
        for i, marker in enumerate(markers):
            gui.addNumericField(marker, 50, 0)  # 0 for no decimal part
            if i % 6 != 5 and i < len(markers) - 1:
                gui.addToSameRow()

        gui.addMessage("Overwrite option")
        # gui.addCheckbox("forceSave", False)
        gui.showDialog()

        if gui.wasCanceled():
            logger.warning("User canceled dialog! Doing nothing. Exit")
            return
        params = {}
        for marker in markers:
            params[marker] = {
                "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
                "createBackground": False,
                "lightBackground": False,
                "useParaboloid": False,
                "doPresmooth": False,
                "correctCorners": False,
            }
        # force_save = gui.getNextBoolean()

        # return params, force_save
        return params

    def get_parameters(self):
        params_bg = {}
        # force_save_data = []
        # force_save = True
        if os.path.exists(self.tempfile_bg):
            data = ht.read_data_from_csv(self.tempfile_bg)
            for paramset in data:
                params_bg[paramset["bg_marker"]] = {"radius": int(paramset["bg_selected_bg_value"]),
                                                    "createBackground": False,
                                                    "lightBackground": False,
                                                    "useParaboloid": False,
                                                    "doPresmooth": False,
                                                    "correctCorners": False, }
                # force_save_data.append(paramset['bg_forceSave'])
            # if list(set(force_save_data))[0] == "Not Selected":
            #    force_save = False
            # return params_bg, force_save
        return params_bg

    def processing(self):
        logger.info("Current IMAGEJ version: " + IJ.getVersion())
        input_dir = self.input_dir
        output_dir = self.output_dir
        patientIDs_metadata = self.get_patientIDs_from_csv_file()
        tiff_files = []
        all_files = os.listdir(input_dir)
        if all_files:
            for tiff_file in all_files:
                if not (os.path.isdir(tiff_file)) and config.cropped_suffix in os.path.basename(tiff_file) and \
                        tiff_file.endswith(self.tiff_ext):
                    for patient_ID_metadata in patientIDs_metadata:
                        if patient_ID_metadata == (os.path.basename(tiff_file).split(".")[0]).split("_")[0]:
                            tiff_files.append(tiff_file)
            if tiff_files:
                # tiff_files_together, all_markers_together = self.get_list_of_indices(input_dir, tiff_files)
                tiff_files_together = self.get_list_of_indices(input_dir, tiff_files)
                all_markers_together = self.read_markers_from_csv_file()
                # Subtract background
                bs = BackgroundSubtracter()
                # try:
                #    params_bg, force_save = self.ask_for_bg_parameters(all_markers_together)
                # except:
                #    logger.warning("user canceled dialog. Exit")
                #    return
                # params_bg, force_save = self.get_parameters()
                params_bg = self.get_parameters()
                if params_bg != {}:
                    for tiff_file in tiff_files:
                        logger.info("Processing the file " + str(tiff_file))
                        imp = IJ.openImage(ht.correct_path(input_dir, tiff_file))
                        imp.show()
                        imp.changes = False
                        stack = imp.getStack()
                        markers = []
                        markerslice_groups = {}
                        for tiff_file_together in tiff_files_together:
                            if tiff_file_together['tiff_file'] == tiff_file:
                                markers = tiff_file_together['markers']
                                markerslice_groups = tiff_file_together['marker_indices']
                        for sliceIndex in range(1, stack.getSize() + 1):
                            filename = str(stack.getSliceLabel(sliceIndex)).split(".")[0]
                            # Save output
                            ip = stack.getProcessor(sliceIndex)
                            slice_file_name_three = ''
                            slice_file_name_four = ''
                            marker = ''
                            subfolder_name = os.path.basename(tiff_file).split('.')[0].split("_")[0]
                            subfolder_path = ht.setting_directory(output_dir, subfolder_name)
                            for marker in markers:
                                if marker in all_markers_together:
                                    if sliceIndex in [x for x in markerslice_groups.get(marker)]:
                                        logger.info(
                                            "Saving the slice " + str(sliceIndex) + " " + str(
                                                stack.getSliceLabel(sliceIndex)))
                                        logger.info("Slice " + str(sliceIndex) + " is in " + str(marker))
                                        slice_file_name_three = ht.correct_path(subfolder_path,
                                                                                filename + "_noBackgroundSub"
                                                                                + config.tiff_ext)
                                        slice_file_name_four = ht.correct_path(subfolder_path,
                                                                               filename + "_backgroundSub" +
                                                                               config.tiff_ext)
                                        # Save output
                                        if (not os.path.exists(slice_file_name_three)) or self.force_save == 1:
                                            temp = ImagePlus(str(sliceIndex), ip)
                                            IJ.run(temp, "8-bit", "")
                                            FileSaver(temp).saveAsTiff(slice_file_name_three)
                                        else:
                                            logger.warning(slice_file_name_three + " exists. Doing nothing. Skipping")
                                        if (not os.path.exists(slice_file_name_four)) or self.force_save == 1:
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
                else:
                    logger.warning("No csv file was found. Something went wrong when setting the parameters in the the "
                                   "dialog for setting the parameters for background processing. The user may have cancelled it or "
                                   "deleted it. Repeat the step if you want to process the background "
                                   "and set the parameters. Doing nothing.")
                IJ.run("Close All")
            else:
                logger.warning("No tif file found")
        else:
            logger.warning(input_dir + " is empty. Doing nothing")
        logger.info("Run is finished")
