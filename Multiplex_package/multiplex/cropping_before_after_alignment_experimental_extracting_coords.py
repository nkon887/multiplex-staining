import csv
import re
from PIL import Image as im

im.MAX_IMAGE_PIXELS = 933120000
import numpy as np
import libtiff
import os
import logging
import tkinter
from tkinter import *

# --- logger & helpertools -------------------------------------------------
try:
    from multiplex.setup_logger import logger  # configured logger
    # multiplex/cropping_before_after_alignment_experimental_extracting_coords.py creates its own logger, as a sub logger to 'multiplex.main'
    logger = logging.getLogger('multiplex.main.cropping_After_Alignment_Experimental_Extracting_Coords')

except Exception:  # minimal fallback logger
    import logging
    logger = logging.getLogger("multiplex")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

try:
    import multiplex.helpertools as ht  # helpertools
except Exception:
    class _HTFallback:
        @staticmethod
        def correct_path(*parts):
            return os.path.normpath(os.path.join(*parts))
        @staticmethod
        def setting_directory(base, sub):
            p = os.path.join(base, sub)
            os.makedirs(p, exist_ok=True)
            return p
        @staticmethod
        def read_data_from_csv(path):
            import csv
            with open(path, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
    ht = _HTFallback()  # type: ignore

class Cropping_Before_After_Alignment_Experimental_Extracting_Coords:
    def __init__(self, pre_input_dir, input_dir, target_dir, error_subfolder_name, tiff_ext, cropped_suffix, forceSave):
        self.pre_input_dir = pre_input_dir
        self.input_dir = input_dir
        self.target_dir = target_dir
        self.error_subfolder_name = error_subfolder_name
        self.tiff_ext = tiff_ext
        self.cropped_suffix = cropped_suffix
        self.tempfile = os.path.join(self.input_dir, "temp.csv")
        self.force_save = int(forceSave[0])

    # def getting_forceSave_parameter(self):
    #    force_Save = ""
    #    window = tkinter.Tk()
    #    window.title("Cropping after Alignment Form")
    #    frame = tkinter.Frame(window)
    #    frame.pack()
    #    # Force Save
    #    force_save_frame = tkinter.LabelFrame(frame, text="Force Save Option")
    #    force_save_frame.grid(row=3, column=0, sticky="news", padx=20, pady=10)

    #    accept_var = tkinter.StringVar(value=self.no_selection)
    #    terms_check = tkinter.Checkbutton(force_save_frame, text="forceSave",
    #                                      variable=accept_var, onvalue=self.selection, offvalue=self.no_selection)
    #    terms_check.grid(row=0, column=0)

    # Buttons
    #   buttons_frame = tkinter.Frame(frame)
    #   buttons_frame.grid(row=4, column=0, sticky="", padx=20, pady=10)

    #    def Stop():
    #        # declare variable as nonlocal variable
    #        nonlocal force_Save

    # get the value of the entry box before destroying window
    #       force_Save = accept_var.get()
    #       window.destroy()

    #    OKbutton = tkinter.Button(buttons_frame, text="OK",
    #                              command=Stop
    #                              )
    #    OKbutton.grid(row=0, column=0)
    #   Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window.destroy)
    #   Cbutton.grid(row=0, column=1)
    #   for widget in buttons_frame.winfo_children():
    #       widget.grid_configure(ipadx=15, padx=10, pady=5)
    #   buttons_frame.grid_rowconfigure(0, weight=1)
    #   buttons_frame.grid_columnconfigure(0, weight=1)
    #   window.mainloop()
    #   return force_Save

    def processing_before_alignment(self):
        """
        BEFORE alignment:
        - Scan all subfolders under input_dir (02_01_input_to_precrop)
        - Find all TIFFs belonging to each patient
        - Identify DAPI images
        - Read ALL DAPI slices
        - Compute bounding box of the smallest shared region
        - Write coordinates to CSV
        """

        forceSave = self.force_save

        # ---------------------------------------------------------
        # Collect all subfolders under input_dir
        # ---------------------------------------------------------
        subfolders = [ht.correct_path(p[0]) for p in os.walk(self.input_dir)]
        if subfolders:
            subfolders.pop(0)  # remove the root folder itself

        if not subfolders:
            logger.warning(self.input_dir + " is empty. Doing nothing.")
            return

        # Will store patientID → list of original TIFF paths
        tiff_paths_per_patient = {}
        # Will store patientID → list of target cropped tiff paths
        cropped_paths_per_patient = {}

        # ---------------------------------------------------------
        # Build mapping patientID → list of TIFF paths
        # ---------------------------------------------------------
        for subfolder in subfolders:

            # Example folder name: 250701_patientID
            filename = "_".join(os.path.basename(subfolder).split("_")[:2])

            original_tiffs = []
            cropped_tiffs = []

            for tname in os.listdir(subfolder):
                input_path = ht.correct_path(subfolder, tname)

                # Skip error folders or incorrect types
                if (self.error_subfolder_name in tname) or (self.error_subfolder_name in subfolder):
                    continue
                if not os.path.isfile(input_path):
                    continue
                if not tname.lower().endswith(self.tiff_ext.lower()):
                    continue

                original_tiffs.append(input_path)

                # Target output path:
                #    target_dir / patientID / same_filename
                cropped_path = ht.correct_path(self.target_dir,
                                               os.path.basename(subfolder),
                                               tname)
                cropped_tiffs.append(cropped_path)

            tiff_paths_per_patient[filename] = original_tiffs
            cropped_paths_per_patient[filename] = cropped_tiffs

        # --- PROCESS EACH PATIENT -------------------------------------------------
        for patientID, tiff_file_paths in tiff_paths_per_patient.items():

            # Skip if all cropped TIFFs already exist and forceSave=0
            all_exist = all(os.path.exists(p) for p in cropped_paths_per_patient[patientID])
            if all_exist and not forceSave:
                logger.info(f"Cropped TIFFs already exist for {patientID}. Skipping.")
                continue

            logger.info("Processing TIFFs for " + patientID)

            data_together = []
            dapi_coords_all_slices = []

            # --- Read all DAPI images (all slices) -------------------------------------------------
            for tiff_path in tiff_file_paths:
                name = os.path.basename(tiff_path).lower()

                # Select only DAPI TIFFs (excluding dapi_copy)
                if "dapi" not in name or "dapi_copy" in name:
                    continue

                try:
                    img_stack = self.read_tiff(tiff_path)
                except:
                    logger.exception("Could not read TIFF: " + tiff_path)
                    continue

                # Extract bounding box from ALL slices, not only slice[0]
                for slice_arr in img_stack:
                    coords = self.crop_image_only_outside_coordinates(slice_arr, tol=36)
                    dapi_coords_all_slices.append(coords)

            # --- If no DAPI data found → skip -------------------------------------------------

            if not dapi_coords_all_slices:
                logger.warning("No DAPI slices found for patient " + patientID)
                continue

            # --- Compute smallest shared bounding region across slices -------------------------------------------------
            row_start = max(c[0] for c in dapi_coords_all_slices)
            row_end = min(c[1] for c in dapi_coords_all_slices)
            col_start = max(c[2] for c in dapi_coords_all_slices)
            col_end = min(c[3] for c in dapi_coords_all_slices)

            # Fiji format: x, y, width, height
            fiji_x = col_start
            fiji_y = row_start
            fiji_w = col_end - col_start
            fiji_h = row_end - row_start

            data_together.append({
                "date_patientID": patientID,
                "fiji_coordinates": f"{fiji_x};{fiji_y};{fiji_w};{fiji_h}"
            })

            # --- Write CSV -------------------------------------------------
            fields = ["date_patientID", "fiji_coordinates"]
            try:
                with open(self.tempfile, "w") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(data_together)
            except:
                logger.exception("Failed writing coordinate CSV.")

        logger.info("Run is finished.")

    def processing_after_alignment(self):
        """
        For each TIFF:
        - Read all slices
        - Detect DAPI slices among per-patient images
        - Compute bounding box per slice
        - Compute smallest shared crop region across ALL slices of DAPI
        - Save to CSV
        """

        # Reset tempfile
        tempfile = self.tempfile
        if os.path.exists(tempfile):
            os.remove(tempfile)

        forceSave = self.force_save

        # --- 1) Collect TIFFs from input dir -------------------------------------------------
        folder_files = os.listdir(self.input_dir)
        logger.info("Input dir: " + self.input_dir)

        tiff_files = []
        for f in folder_files:
            if f.endswith(self.tiff_ext) and not os.path.isdir(f):
                if (self.cropped_suffix not in f) and (self.error_subfolder_name not in f):
                    tiff_files.append(f)

        if not tiff_files:
            logger.warning("No TIFF files found.")
            return

        # --- 2) Build mapping: patient → list of TIFF names in pre_input_dir -------------------------------------------------
        update_pre_input_dir = self.pre_input_dir
        if not os.path.exists(update_pre_input_dir):
            logger.warning("Pre-input dir missing. Exiting.")
            return

        pattern = r'^\d{6}_[^\_]*'
        subdirs = [x[0] for x in os.walk(update_pre_input_dir)
                   if re.match(pattern, os.path.basename(x[0]))]

        if not subdirs:
            logger.warning("No subdir match found in pre-input dir.")
            return

        selected_patient_subfolder_img_paths_dict = {}

        for tiff_file in tiff_files:
            patient = os.path.splitext(os.path.basename(tiff_file))[0]
            selected_images = []

            for folder in subdirs:
                if os.path.basename(folder).split("_")[1] == patient:
                    for img in os.listdir(folder):
                        if "dapi_copy" not in img:
                            selected_images.append(img)

            selected_patient_subfolder_img_paths_dict[patient] = selected_images

        # --- 3) Process each TIFF -------------------------------------------------
        data_together = []

        for tiff_file in tiff_files:
            patient = os.path.splitext(os.path.basename(tiff_file))[0]
            logger.info("Processing TIFF: " + tiff_file)

            tiff_path = ht.correct_path(self.input_dir, tiff_file)
            tiff_cropped_path = ht.correct_path(
                self.input_dir,
                patient + self.cropped_suffix + self.tiff_ext
            )

            # Skip overwrite protection
            if os.path.exists(tiff_cropped_path) and not forceSave:
                logger.warning("Cropped exists, skipping: " + tiff_cropped_path)
                continue

            channel_filenames = selected_patient_subfolder_img_paths_dict.get(patient, [])
            if not channel_filenames:
                logger.info("No images for patient " + patient + ". Skipping.")
                continue

            # Read TIFF slices
            images = self.read_tiff(tiff_path)

            # --- Extract bounding boxes from ALL DAPI slices -------------------------------------------------
            all_coords = []

            for slice_index, channel_name in zip(range(len(images)), channel_filenames):
                if "dapi" in channel_name.lower():
                    coords = self.crop_image_only_outside_coordinates(images[slice_index], tol=23)
                    all_coords.append(coords)

            if not all_coords:
                logger.warning("No DAPI slices found for patient " + patient)
                continue

            # --- Compute smallest shared frame across all DAPI slices -------------------------------------------------
            shared_row_start = max(c[0] for c in all_coords)
            shared_row_end = min(c[1] for c in all_coords)
            shared_col_start = max(c[2] for c in all_coords)
            shared_col_end = min(c[3] for c in all_coords)

            # Fiji format: (x, y, w, h)
            fiji_x = shared_col_start
            fiji_y = shared_row_start
            fiji_w = shared_col_end - shared_col_start
            fiji_h = shared_row_end - shared_row_start

            # Save output
            entry = {
                "patientID": patient,
                "fiji_coordinates": "%d;%d;%d;%d" % (fiji_x, fiji_y, fiji_w, fiji_h)
            }
            data_together.append(entry)

            # Write CSV each time for safety
            fields = ["patientID", "fiji_coordinates"]
            with open(tempfile, "w") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                w.writerows(data_together)

        logger.info("Run is finished.")

    # --- Supporting functions -------------------------------------------------

    def crop_image_only_outside_coordinates(self, im, tol=0):
        mask = im > tol
        if im.ndim == 3:
            mask = mask.all(2)

        m, n = mask.shape
        mask0, mask1 = mask.any(0), mask.any(1)

        col_start = mask0.argmax()
        col_end = n - mask0[::-1].argmax()
        row_start = mask1.argmax()
        row_end = m - mask1[::-1].argmax()

        return row_start, row_end, col_start, col_end

    def crop_image_only_outside__(self, im, coords):
        return im[coords[0]:coords[1], coords[2]:coords[3]]

    def read_tiff(self, path):
        tif = libtiff.TIFF.open(path, 'r')
        images = []
        for tif_slice in tif.iter_images():
            images.append(np.asarray(tif_slice))
        return images

