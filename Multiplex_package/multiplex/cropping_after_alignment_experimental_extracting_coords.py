import csv
import re
from PIL import Image as im

im.MAX_IMAGE_PIXELS = 933120000
import numpy as np
import libtiff
import os
import logging
import helpertools as ht
import tkinter
from tkinter import *

# multiplex.cropping_after_alignment_experimental_extracting_coords.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.main.cropping_After_Alignment_Experimental_Extracting_Coords')

class Cropping_After_Alignment_Experimental_Extracting_Coords:
    def __init__(self, pre_input_dir, input_dir, target_dir, error_subfolder_name, tiff_ext, cropped_suffix):
        self.pre_input_dir = pre_input_dir
        self.input_dir = input_dir
        self.target_dir = target_dir
        self.error_subfolder_name = error_subfolder_name
        self.tiff_ext = tiff_ext
        self.cropped_suffix = cropped_suffix
        self.no_selection = "Not Selected"
        self.selection = "Selected"
        self.tempfile = os.path.join(self.input_dir, "temp.csv")

    def getting_forceSave_parameter(self):
        force_Save = ""
        window = tkinter.Tk()
        window.title("Cropping after Alignment Form")
        frame = tkinter.Frame(window)
        frame.pack()
        # Force Save
        force_save_frame = tkinter.LabelFrame(frame, text="Force Save Option")
        force_save_frame.grid(row=3, column=0, sticky="news", padx=20, pady=10)

        accept_var = tkinter.StringVar(value=self.no_selection)
        terms_check = tkinter.Checkbutton(force_save_frame, text="forceSave",
                                          variable=accept_var, onvalue=self.selection, offvalue=self.no_selection)
        terms_check.grid(row=0, column=0)

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=4, column=0, sticky="", padx=20, pady=10)

        def Stop():
            # declare variable as nonlocal variable
            nonlocal force_Save

            # get the value of the entry box before destroying window
            force_Save = accept_var.get()
            window.destroy()

        OKbutton = tkinter.Button(buttons_frame, text="OK",
                                  command=Stop
                                  )
        OKbutton.grid(row=0, column=0)
        Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window.destroy)
        Cbutton.grid(row=0, column=1)
        for widget in buttons_frame.winfo_children():
            widget.grid_configure(ipadx=15, padx=10, pady=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        window.mainloop()
        return force_Save

    def processing_after_alignment(self):
        forceSave = self.getting_forceSave_parameter()
        tiff_files = []
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
        selected_patient_subfolder_img_paths_dict = {}
        for tiff_file in tiff_files:
            # tiff_file is aligned stack of channel files of one patient that is not cropped
            logger.info("Processing the tiff file " + tiff_file)
            # the pre_input_dir is the folder that contains subfolders with channels files for each patient
            update_pre_input_dir = self.pre_input_dir
            if not os.path.exists(update_pre_input_dir):
                logger.warning("The pre input directory doesn't exist. Doing nothing.Exiting")
                return
            pattern = r'^\d{6}\_[^\_]*'
            subdirs = [x[0] for x in os.walk(update_pre_input_dir) if re.match(pattern, os.path.basename(x[0]))]
            if not subdirs:
                logger.warning(update_pre_input_dir + " is empty. Doing nothing")
                return

            subfolder_patients = []
            for folder in subdirs:
                subfolder_patients.append(os.path.basename(folder).split("_")[1])
            patient = os.path.splitext(os.path.basename(tiff_file))[0]
            selected_patient_subfolder_img_paths_list = []
            for subfolder in subdirs:
                if os.path.basename(subfolder).split("_")[1] == patient:
                    for img in os.listdir(subfolder):
                        if not "dapi_copy" in img:
                            selected_patient_subfolder_img_paths_list.append(img)
            selected_patient_subfolder_img_paths_dict[patient] = selected_patient_subfolder_img_paths_list
        data_together = []
        for tiff_file in tiff_files:
            # Save output
            patient = os.path.splitext(os.path.basename(tiff_file))[0]
            # path of the aligned stack file to process
            path = ht.correct_path(self.input_dir, tiff_file)
            # path of the cropped aligned stack file
            tiff_cropped_path = ht.correct_path(self.input_dir, os.path.basename(tiff_file).split('.')[0] +
                                                self.cropped_suffix + self.tiff_ext)
            # Save output
            if (not os.path.exists(tiff_cropped_path)) or forceSave == self.selection:
                # if cropped aligned stack file doesn't exist or forceSave is selected
                logger.info("Cropping...")
                channel_filenames = selected_patient_subfolder_img_paths_dict[patient]
                images = self.read_tiff(path)
                save_coordinates = []
                if channel_filenames:
                    for i, channelname in zip(range(len(images)), channel_filenames):
                        if "dapi" in channelname:
                            # logger.info(channelname)
                            save_coordinates.append(
                                [l for l in self.crop_image_only_outside_coordinates(images[i], 23)])
                    coordinates_for_crop = []
                    coordinates_for_fiji_crop = []
                    if save_coordinates:
                        coordinates_for_crop = [max(l[0] for l in save_coordinates),
                                                min(l[1] for l in save_coordinates),
                                                max(l[2] for l in save_coordinates),
                                                min(l[3] for l in save_coordinates)]
                        coordinates_for_fiji_crop = [coordinates_for_crop[2],
                                                     coordinates_for_crop[0],
                                                     coordinates_for_crop[3] - coordinates_for_crop[2],
                                                     coordinates_for_crop[1] - coordinates_for_crop[0]]

                    # for i, ar in enumerate(images):
                    # ima = self.crop_image_only_outside__(ar, coordinates_for_crop)
                    # logger.info(str(coordinates_for_crop))
                    # data = im.fromarray(ima)
                    # save
                    # logger.info("Saving the cropped image as " + channel_filenames[i])
                    # targetDir = ht.correct_path(self.input_dir, patient)
                    # if not os.path.exists(targetDir):
                    #    os.makedirs(targetDir)
                    # data.save(ht.correct_path(targetDir, channel_filenames[i] + self.tiff_ext))
                    # logger.info(str(coordinates_for_crop))
                    # logger.info(str(coordinates_for_fiji_crop))

                    data = {}

                    data['patientID'] = patient
                    data['fiji_coordinates'] = ';'.join([str(elem) for elem in coordinates_for_fiji_crop])
                    # Channels info
                    data_together.append(data)
                    #print(data_together)
                    # Create Table
                    fields = []
                    if data_together:
                        fields = list(data_together[0].keys())
                    with open(self.tempfile, "w") as f:
                        w = csv.DictWriter(f, fieldnames=fields)
                        w.writeheader()
                        w.writerows(data_together)
                    f.close()
                else:
                    logger.info(
                        "Image files are not found in the input folder with the patientID " + patient + ". Skipping the patient ID")
            else:
                logger.warning("The cropped tiff file " + tiff_cropped_path + "exists and should not be "
                                                                              "overwritten. Skipping")
        logger.info("Run is finished")

    def crop_image_only_outside_coordinates(self, im, tol=0):
        # img is 2D or 3D image data
        # tol  is tolerance
        mask = im > tol
        if im.ndim == 3:
            mask = mask.all(2)
        m, n = mask.shape
        mask0, mask1 = mask.any(0), mask.any(1)
        col_start, col_end = mask0.argmax(), n - mask0[::-1].argmax()
        row_start, row_end = mask1.argmax(), m - mask1[::-1].argmax()
        return row_start, row_end, col_start, col_end

    def crop_image_only_outside__(self, im, coords):
        return im[coords[0]:coords[1], coords[2]:coords[3]]

    def read_tiff(self, path):
        """
        path - Path to the multipage-tiff file
        n_images - Number of pages in the tiff file
        """
        tif = libtiff.TIFF.open(path, 'r')
        images = []
        for ii, tif_slice in enumerate(tif.iter_images()):
            arr = np.asarray(tif_slice, dtype=np.uint8)
            images.append(arr)
        return images
