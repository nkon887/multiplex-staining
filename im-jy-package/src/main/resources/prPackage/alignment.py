import os
import re
import shutil
import sys

from ij import IJ, WindowManager, ImagePlus, VirtualStack
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter
from register_virtual_stack import Register_Virtual_Stack_MT, Transform_Virtual_Stack_MT
from ij.plugin import ImagesToStack

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
import config
import logging

# alignment.py creates its own logger, as a sub logger to 'pipelineGUI.macro.main.alignment'
logger = logging.getLogger('pipelineGUI.macro.main.ALIGNMENT')


class Alignment:
    def __init__(self, alignment_dir, tiff_ext, error_subfolder_name, input_dir, precrop_input_dir):
        self.alignment_dir = alignment_dir
        self.tiff_ext = tiff_ext
        self.error_subfolder_name = error_subfolder_name
        self.input_dir = input_dir
        self.precrop_input_dir = precrop_input_dir

    def get_patient_subfolder_number(self, patients, item):
        # folder path
        count = 0
        # Iterate directory
        for curr_item in patients:
            if curr_item == item:
                count += 1
        return count

    def get_files_number(self, dir_path, ext):
        # folder path
        count = 0
        # Iterate directory
        for path in os.listdir(dir_path):
            # check if current path is a file
            file_path = os.path.join(dir_path, path)
            if os.path.isfile(file_path) and file_path.endswith(ext):
                count += 1
        return count

    def copy_file(self, filename, filename_suffix):
        # Copy filename+ext into a new filename_copy_i+ext i in filename_suffix range
        file_name, ext = filename.split('.')
        for i in filename_suffix:
            file_destination = file_name + "_copy_" + str(i) + "." + ext
            if not os.path.exists(file_destination):
                shutil.copy(filename, file_destination)

    def delete_files_from_process_folders(self, list_of_dirs):
        for dir in list_of_dirs:
            for img_file in os.listdir(dir):
                os.remove(os.path.join(dir, img_file))

    def Composite_Aligner(self, img_paths, max_files_numbers, params_background, folder_to_precrop, force_save):
        """ Aligns composite images, saves to target directory. """
        # Source, output and transformations directories
        alignment_dir = self.alignment_dir
        temp_input_dir = os.path.join(alignment_dir, "temp\\")
        target_dir = os.path.join(alignment_dir, "out\\")
        transf_dir = os.path.join(alignment_dir, "transforms\\")
        # Creates dir if dir does not exist.
        if not os.path.exists(temp_input_dir):
            os.makedirs(temp_input_dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        if not os.path.exists(transf_dir):
            os.makedirs(transf_dir)
        patients_to_crop = []
        for patient in img_paths.keys():
            for dirpath, dirnames, files in os.walk(temp_input_dir):
                if files:
                    self.delete_files_from_process_folders([temp_input_dir])
            for dirpath, dirnames, files in os.walk(target_dir):
                if files:
                    self.delete_files_from_process_folders([target_dir])
            for dirpath, dirnames, files in os.walk(transf_dir):
                if files:
                    self.delete_files_from_process_folders([transf_dir])
            stack_name = patient
            stack_path = os.path.join(alignment_dir, stack_name + self.tiff_ext).replace("\\", "/")
            # Save output
            if (not os.path.exists(stack_path)) or not (patient in x for x in
                                                        os.listdir(folder_to_precrop)) or force_save:
                for subfolder in img_paths[patient].keys():
                    for img_path in img_paths[patient][subfolder]:
                        if "dapi" in os.path.basename(img_path) and not "dapi_copy" in os.path.basename(img_path):
                            shutil.copy(img_path, os.path.join(temp_input_dir, os.path.basename(img_path)))

                p = Register_Virtual_Stack_MT.Param()

                # parameters:
                p.sift.maxOctaveSize = 1024
                p.sift.minOctaveSize = 64
                p.sift.steps = 12
                p.sift.initialSigma = 1.6
                p.sift.fdBins = 8
                p.sift.fdSize = 8
                # 1 = RIGID
                p.featuresModelIndex = 1
                p.registrationModelIndex = 1

                # The "inlier ratio":
                p.minInlierRatio = 0.05

                # Reference image name (must be within source directory)
                reference_name = os.path.basename(iter(os.listdir(temp_input_dir)).next())
                logger.info("Reference file name " + reference_name)
                # Shrinkage option (False = 0)
                use_shrinking_constraint = 0
                # Advanced option (False = 0)
                advanced = 0
                # Interpolation (False = 0)
                interpolate = 1

                # Opens a dialog to set transformation options.
                # IJ.beep()
                # p.showDialog()

                # Executes alignment.
                logger.info("Aligning...")
                try:
                    Register_Virtual_Stack_MT.exec(temp_input_dir, target_dir, transf_dir, reference_name, p,
                                                   use_shrinking_constraint)
                except:
                    logger.exception(sys.exc_info())
                for img_file in os.listdir(temp_input_dir):
                    os.remove(os.path.join(temp_input_dir, img_file))
                # Close alignment window.
                imp = WindowManager.getCurrentImage()
                if imp:
                    imp.close()
                else:
                    logger.warning(patient + " couldn't be processed")
                    patients_to_crop.append(patient)
                    continue
                max_files_number = max_files_numbers[patient] - 1
                for i in range(max_files_number):
                    for subfolder in img_paths[patient].keys():
                        img_path_list = [x for x in img_paths[patient][subfolder] if
                                         "dapi.tif" not in os.path.basename(x)]
                        img_path = img_path_list[i]
                        shutil.copy(img_path, os.path.join(temp_input_dir, os.path.basename(img_path)))
                    check_transform = Transform_Virtual_Stack_MT.exec(temp_input_dir, target_dir, transf_dir,
                                                                      interpolate)
                    if check_transform:
                        logger.info("batch " + str(i) + " of " + patient + " is successfully transformed")
                    for img_file in os.listdir(temp_input_dir):
                        os.remove(os.path.join(temp_input_dir, img_file))
                    # Close alignment window.
                    imp = WindowManager.getCurrentImage()
                    imp.close()
                for img_file in os.listdir(transf_dir):
                    os.remove(os.path.join(transf_dir, img_file))
                vs = None
                width, height = 0, 0
                try:
                    width, height = self.get_max_dims(target_dir)
                except TypeError:
                    logger.exception(sys.exc_info())
                # Initialize the VirtualStack
                if vs is None and self.get_files_number(target_dir, self.tiff_ext) > 1:
                    # vs = CreateVirtualStack(target_dir, params_background)
                    imp = self.create_stack(target_dir)
                    stack = imp.getStack()
                    for i in xrange(0, stack.size()):
                        ip = stack.getProcessor(i + 1)
                        stack.setSliceLabel(os.path.basename(stack.getSliceLabel(i + 1)), i + 1)
                        if "dapi" in stack.getSliceLabel(i + 1):
                            radius = params_background["radius"]
                            create_background = params_background["createBackground"]
                            light_background = params_background["lightBackground"]
                            use_paraboloid = params_background["useParaboloid"]
                            do_presmooth = params_background["doPresmooth"]
                            correct_corners = params_background["correctCorners"]
                            bs = BackgroundSubtracter()
                            bs.rollingBallBackground(ip, radius, create_background, light_background, use_paraboloid,
                                                     do_presmooth,
                                                     correct_corners)

                    imp = ImagePlus(stack_name, stack)
                    stack_path = os.path.join(alignment_dir, stack_name + self.tiff_ext).replace("\\", "/")
                    # Save output
                    if (not os.path.exists(stack_path)) or force_save:
                        logger.info("Saving the stack as " + stack_path)
                        FileSaver(imp).saveAsTiff(stack_path)
                    else:
                        logger.warning("The stack file " + stack_path + " exists. Skipping")
                elif vs is None and self.get_files_number(target_dir, self.tiff_ext) == 1:
                    logger.warning("The number of image files is less than 2. For stack it should be at least 2. "
                                   "Skipping")
                    continue
                for img_file in os.listdir(target_dir):
                    os.remove(os.path.join(target_dir, img_file))
            else:
                logger.warning(stack_path + " exists. Skipping")
        logger.info("Run is finished")
        self.delete_files_from_process_folders([temp_input_dir, target_dir, transf_dir])
        shutil.rmtree(temp_input_dir)
        shutil.rmtree(target_dir)
        shutil.rmtree(transf_dir)
        return patients_to_crop

    def create_stack(self, target_dir):
        images = []
        for filename in os.listdir(target_dir):
            imp = IJ.openImage(os.path.join(target_dir, filename))
            if imp:
                images.append(imp)
        stack = None
        if images:
            stack = ImagesToStack.run(images)
        return stack

    def ask_for_parameters(self):
        gui = GenericDialog("Input parameters")
        gui.addDirectoryField("Directory Path", self.input_dir)
        gui.addMessage("Background Parameters")
        gui.addNumericField("Radius", 50, 0)  # 0 for no decimal part
        gui.addCheckbox("createBackground", False)
        gui.addCheckbox("lightBackground", False)
        gui.addCheckbox("useParaboloid", False)
        gui.addCheckbox("doPresmooth", False)
        gui.addCheckbox("correctCorners", False)
        gui.addMessage("Overwrite option")
        gui.addCheckbox("forceSave", False)
        gui.showDialog()
        if gui.wasCanceled():
            logger.warning("User canceled dialog! Doing nothing. Exit")
            return
        folder_path = gui.getNextString()
        bg_params = {
            "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
            "createBackground": gui.getNextBoolean(),
            "lightBackground": gui.getNextBoolean(),
            "useParaboloid": gui.getNextBoolean(),
            "doPresmooth": gui.getNextBoolean(),
            "correctCorners": gui.getNextBoolean()
        }
        force_save = gui.getNextBoolean()
        return [folder_path, bg_params, force_save]

    def get_max_dims(self, dir):
        files = [filename for filename in os.listdir(dir) if os.path.isfile(os.path.join(dir, filename))]
        width_list = []
        height_list = []
        for filename in files:
            width, height = ht.dimensions_of(os.path.join(dir, filename),
                                             self.alignment_dir, self.error_subfolder_name)
            width_list.append(width)
            height_list.append(height)
        return max(width_list), max(height_list)

    def aligning(self):
        imagejversion = IJ.getVersion()
        logger.info("Current IMAGEJ version: " + imagejversion)
        try:
            # Input Parameters_dir

            update_input_dir, params_background, force_save = self.ask_for_parameters()
        except:
            # user canceled dialog
            return
        if not os.path.exists(update_input_dir):
            logger.warning("The input directory doesn't exist. Doing nothing.Exiting")
            return
        pattern = r'^\d{6}\_[^\_]*'
        folder_to_precrop = self.precrop_input_dir
        subdirs = [x[0] for x in os.walk(update_input_dir) if re.match(pattern, os.path.basename(x[0]))]
        if not subdirs:
            logger.warning(update_input_dir + " is empty. Doing nothing")
            return

        subfolder_patients = []
        for folder in subdirs:
            subfolder_patients.append(os.path.basename(folder).split("_")[1])
        patients = list(set(subfolder_patients))
        counts = []
        for patient in patients:
            counts.append(self.get_patient_subfolder_number(subfolder_patients, patient))
        selected_patients = []
        for count, patient in zip(counts, patients):
            if count > 1:
                selected_patients.append(patient)
        selected_patients = list(set(selected_patients))
        selected_patient_subfolder_img_paths_dict = {}
        subdir_files_number = {}  # Empty dictionary to add values into
        max_files_numbers = {}
        for patient in selected_patients:
            selected_patient_subfolder_img_paths_dict[patient] = {}
            subdir_files_number[patient] = {}
            for subfolder in subdirs:
                if os.path.basename(subfolder).split("_")[1] in patient:
                    selected_patient_subfolder_img_paths_list = []
                    for img in os.listdir(subfolder):
                        selected_patient_subfolder_img_paths_list.append(os.path.join(update_input_dir, subfolder, img))
                    subdir_files_number[patient][subfolder] = self.get_files_number(
                        os.path.join(update_input_dir, subfolder),
                        self.tiff_ext)
                    selected_patient_subfolder_img_paths_dict[patient][
                        subfolder] = selected_patient_subfolder_img_paths_list
            max_files_numbers[patient] = max(subdir_files_number[patient].values())
        selected_patient_subfolder_img_paths_list = []
        # print(selected_patient_subfolder_img_paths_dict)
        # check and add dapi file copies to the subfolders of each patient if needed 
        for patient in selected_patients:
            for subfolder in selected_patient_subfolder_img_paths_dict[patient]:
                dirpath = os.path.join(update_input_dir, subfolder)
                dapifiles = ht.dapi_tiff_image_filenames(dirpath, config.dapi_str, self.tiff_ext)
                if not dapifiles == []:
                    dapipath = os.path.join(dirpath, dapifiles[0])
                    logger.info("Processing the subfolder " + os.path.dirname(dapipath))
                    if subdir_files_number[patient][subfolder] < max_files_numbers[patient]:
                        # add dapi file copies if max_file_number greater than current subfolder file number
                        logger.info(
                            "Copying the dapi file " + os.path.basename(dapipath) + " in the subfolder " + os.path.join(
                                update_input_dir,
                                os.path.dirname(
                                    dapipath)))
                        dapi_filename_suffix = range(1, max_files_numbers[patient] - subdir_files_number[patient][
                            subfolder] + 1)
                        self.copy_file(dapipath, dapi_filename_suffix)
                        # update dictionary according copy dapi file
                        for img in os.listdir(subfolder):
                            selected_patient_subfolder_img_paths_list.append(
                                os.path.join(update_input_dir, subfolder, img))
                        selected_patient_subfolder_img_paths_dict[patient][
                            subfolder] = selected_patient_subfolder_img_paths_list

        patients_to_precrop = self.Composite_Aligner(selected_patient_subfolder_img_paths_dict, max_files_numbers,
                                                     params_background, folder_to_precrop, force_save)
        if not patients_to_precrop == []:
            logger.info("The list of patients to crop " + str(patients_to_precrop))
        for folder in subdirs:
            for patient_to_precrop in patients_to_precrop:
                if patient_to_precrop in os.path.basename(folder):
                    precrop_subfolder = os.path.join(folder_to_precrop, os.path.basename(folder))
                    if not os.path.exists(precrop_subfolder):
                        os.makedirs(precrop_subfolder)
                    for filename in os.listdir(folder):
                        shutil.copy(os.path.join(folder, filename),
                                    os.path.join(precrop_subfolder, os.path.basename(filename)))
