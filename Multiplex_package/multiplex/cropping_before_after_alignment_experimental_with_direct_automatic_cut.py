import re
from PIL import Image as im

im.MAX_IMAGE_PIXELS = 933120000
import numpy as np
import tifffile as tiff
import os
import logging
import tkinter
from tkinter import *

# --- logger & helpertools -------------------------------------------------
try:
    from multiplex.setup_logger import logger  # configured logger
    # multiplex/cropping_before_after_alignment_experimental_with_direct_automatic_cut.py creates its own logger, as a sub logger to 'multiplex.main'
    logger = logging.getLogger('multiplex.main.cropping_before_after_alignment_experimental_with_direct_automatic_cut')

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

class Cropping_Before_After_Alignment_Experimental_With_Direct_Automatic_Cut:
    def __init__(self, pre_input_dir, input_dir, target_dir, error_subfolder_name, tiff_ext, cropped_suffix, forceSave):
        self.pre_input_dir_only_after_alignment = pre_input_dir
        self.input_dir = input_dir
        self.target_dir = target_dir
        self.error_subfolder_name = error_subfolder_name
        self.tiff_ext = tiff_ext
        self.cropped_suffix = cropped_suffix
        self.force_save = int(forceSave[0])

    def processing_before_alignment(self):
        """
        BEFORE alignment:
        - Read subfolders under input_dir (02_01_input_to_precrop)
        - For each patient:
             • read all TIFFs
             • detect ALL DAPI images
             • compute bounding box across ALL DAPI slices
             • crop FIRST slice of all channel TIFFs
             • save cropped TIFFs into target_dir/patientID/
        """

        forceSave = self.force_save

        # ---------------------------------------------------------
        # 1) Collect subfolders under input_dir
        # ---------------------------------------------------------
        subfolders = [ht.correct_path(p[0]) for p in os.walk(self.input_dir)]
        if subfolders:
            subfolders.pop(0)  # remove root entry

        if not subfolders:
            logger.warning(self.input_dir + " is empty. Doing nothing.")
            return

        # patientID → list of original TIFF paths
        tiff_paths_dict = {}
        # patientID → list of future cropped output paths
        cropped_paths_dict = {}

        # ---------------------------------------------------------
        # 2) Build mapping: patientID → list of original TIFFs
        # ---------------------------------------------------------
        for subfolder in subfolders:
            patientID = "_".join(os.path.basename(subfolder).split("_")[:2])

            original_paths = []
            cropped_paths = []

            for fname in os.listdir(subfolder):
                path = ht.correct_path(subfolder, fname)

                if self.error_subfolder_name in fname:
                    continue
                if not fname.lower().endswith(self.tiff_ext.lower()):
                    continue
                if not os.path.isfile(path):
                    continue

                original_paths.append(path)

                out_path = ht.correct_path(self.target_dir, patientID, fname)
                cropped_paths.append(out_path)

            tiff_paths_dict[patientID] = original_paths
            cropped_paths_dict[patientID] = cropped_paths

        # ---------------------------------------------------------
        # 3) Process each patient
        # ---------------------------------------------------------
        for patientID, file_paths in tiff_paths_dict.items():

            # Skip if already cropped (unless forceSave)
            all_exist = all(os.path.exists(p) for p in cropped_paths_dict[patientID])
            if all_exist and not forceSave:
                logger.info(f"Cropped TIFFs already exist for {patientID}. Skipping.")
                continue

            if not file_paths:
                logger.warning(f"No TIFFs found for {patientID}. Skipping.")
                continue

            logger.info(f"Processing patient {patientID}")

            dapi_coords = []  # collect bounding boxes from ALL DAPI slices
            images_by_file = {}  # fname → stack

            # ---------------------------------------------------------
            # 4) Read input TIFF stacks and extract DAPI bounding boxes
            # ---------------------------------------------------------
            for path in file_paths:
                fname = os.path.basename(path)
                is_dapi = ("dapi" in fname.lower()) and ("dapi_copy" not in fname.lower())

                try:
                    stack = self.read_tiff(path)
                except:
                    logger.exception("Could not read TIFF: " + path)
                    continue

                images_by_file[fname] = stack

                if is_dapi:
                    # take ALL slices of DAPI
                    for slice_arr in stack:
                        coords = self.crop_image_only_outside_coordinates(slice_arr, tol=36)
                        dapi_coords.append(coords)

            # ---------------------------------------------------------
            # 5) If no DAPI found → skip patient
            # ---------------------------------------------------------
            if not dapi_coords:
                logger.warning(f"No DAPI slices found for {patientID}. Skipping.")
                continue

            # Compute smallest shared bounding region
            r0 = max(c[0] for c in dapi_coords)
            r1 = min(c[1] for c in dapi_coords)
            c0 = max(c[2] for c in dapi_coords)
            c1 = min(c[3] for c in dapi_coords)
            crop_coords = (r0, r1, c0, c1)

            logger.info(f"Crop coords for {patientID}: {crop_coords}")

            # ---------------------------------------------------------
            # 6) Crop all FIRST slices and save
            # ---------------------------------------------------------
            out_dir = ht.correct_path(self.target_dir, patientID)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            for path in file_paths:
                fname = os.path.basename(path)
                stack = images_by_file[fname]

                # Use FIRST slice only before alignment
                arr = stack[0]
                cropped = self.crop_image_only_outside__(arr, crop_coords)

                pil_img = im.fromarray(cropped)
                save_path = ht.correct_path(out_dir, fname)

                if os.path.exists(save_path) and not forceSave:
                    logger.info(f"Skipping existing cropped file: {save_path}")
                    continue

                try:
                    logger.info("Saving cropped TIFF: " + save_path)
                    pil_img.save(save_path)
                except:
                    logger.exception("Could not save: " + save_path)

        logger.info("Run is finished.")

    def processing_after_alignment(self):
        """
        AFTER alignment:
        - Find all TIFF files in input_dir
        - Match each TIFF to its corresponding patient subfolder in pre_input_dir_only_after_alignment
        - For each patient:
            • Read TIFF stack (aligned)
            • Read list of corresponding channel filenames
            • Identify DAPI channels
            • Compute bounding box from ALL DAPI slices
            • Crop ALL slices using smallest shared region
            • Save cropped slices as TIFFs into input_dir/patient/
        """

        forceSave = self.force_save
        logger.info("Input directory: " + self.input_dir)

        # ---------------------------------------------------------------------
        # 1) Collect TIFF filenames from input_dir
        # ---------------------------------------------------------------------
        folder_files = os.listdir(self.input_dir)
        if not folder_files:
            logger.warning(self.input_dir + " is empty. Doing nothing.")
            return

        tiff_files = []
        for f in folder_files:
            if not f.lower().endswith(self.tiff_ext.lower()):
                continue
            if self.cropped_suffix in f:
                continue
            if self.error_subfolder_name in f:
                continue

            path = ht.correct_path(self.input_dir, f)
            if os.path.isfile(path):
                tiff_files.append(f)

        if not tiff_files:
            logger.warning("No TIFF files found. Doing nothing.")
            return

        # ---------------------------------------------------------------------
        # 2) Build mapping: patientID → list of filenames in pre_input_dir
        # ---------------------------------------------------------------------
        pre_dir = self.pre_input_dir_only_after_alignment
        if not os.path.exists(pre_dir):
            logger.warning("The pre-input directory does not exist. Exiting.")
            return

        pattern = r'^\d{6}\_[^\_]*'
        subdirs = [x[0] for x in os.walk(pre_dir) if re.match(pattern, os.path.basename(x[0]))]
        if not subdirs:
            logger.warning("No matching patient folders found in pre_input_dir. Doing nothing.")
            return

        patient_channels_dict = {}

        for f in tiff_files:
            patient = os.path.splitext(f)[0]
            matched_imgs = []

            for folder in subdirs:
                if os.path.basename(folder).split("_")[1] == patient:
                    for img in os.listdir(folder):
                        # skip dapi_copy
                        if "dapi_copy" in img.lower():
                            continue
                        matched_imgs.append(img)

            patient_channels_dict[patient] = matched_imgs

        # ---------------------------------------------------------------------
        # 3) PROCESS EACH PATIENT
        # ---------------------------------------------------------------------
        for tif in tiff_files:
            patient = os.path.splitext(tif)[0]
            aligned_path = ht.correct_path(self.input_dir, tif)

            cropped_output_path = ht.correct_path(self.input_dir,
                                                  patient + self.cropped_suffix + self.tiff_ext)

            # Skip if cropped exists already
            if os.path.exists(cropped_output_path) and not forceSave:
                logger.warning(f"Cropped TIFF for {patient} already exists. Skipping.")
                continue

            channel_filenames = patient_channels_dict.get(patient, [])
            if not channel_filenames:
                logger.info(f"No channel metadata found for patient {patient}. Skipping.")
                continue

            logger.info("Cropping aligned TIFF for patient " + patient)

            # Read TIFF (aligned stack)
            try:
                images = self.read_tiff(aligned_path)
            except:
                logger.exception("Failed to read: " + aligned_path)
                continue

            # -----------------------------------------------------------------
            # 4) Find all DAPI slices and compute combined bounding box
            # -----------------------------------------------------------------
            dapi_coords = []

            # Ensure no mismatch: channel list length must match number of slices
            if len(channel_filenames) != len(images):
                logger.warning(f"Channel list length mismatch for {patient}. "
                               f"{len(channel_filenames)} filenames vs {len(images)} slices.")
                continue

            for slice_index, ch_name in enumerate(channel_filenames):
                if "dapi" in ch_name.lower() and "dapi_copy" not in ch_name.lower():
                    coords = self.crop_image_only_outside_coordinates(images[slice_index], tol=50)
                    dapi_coords.append(coords)

            if not dapi_coords:
                logger.warning(f"No DAPI slices found for patient {patient}. Skipping.")
                continue

            # small shared region across all DAPI slices
            r0 = max(c[0] for c in dapi_coords)
            r1 = min(c[1] for c in dapi_coords)
            c0 = max(c[2] for c in dapi_coords)
            c1 = min(c[3] for c in dapi_coords)

            coords_crop = (r0, r1, c0, c1)
            logger.info(f"Crop region for {patient}: (r0={r0}, r1={r1}, c0={c0}, c1={c1})")

            # -----------------------------------------------------------------
            # 5) Crop all slices and save into input_dir/patient/
            # -----------------------------------------------------------------
            targetDir = ht.correct_path(self.input_dir, patient)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)

            for idx, arr in enumerate(images):
                cropped = self.crop_image_only_outside__(arr, coords_crop)
                pil_img = im.fromarray(cropped)

                outname = channel_filenames[idx] + self.tiff_ext
                outfile = ht.correct_path(targetDir, outname)

                logger.info(f"Saving cropped slice: {outfile}")
                try:
                    pil_img.save(outfile)
                except:
                    logger.exception("Failed to save: " + outfile)

        logger.info("Run is finished.")

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
        with tiff.TiffFile(path) as tif:
            arr = tif.asarray()
        return arr
