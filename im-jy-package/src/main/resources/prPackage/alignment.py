import os
import re
import shutil
import sys
import logging

from ij import IJ, WindowManager, ImagePlus, VirtualStack
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter
from register_virtual_stack import Register_Virtual_Stack_MT, Transform_Virtual_Stack_MT
from ij.plugin import ImagesToStack

sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
import config

# im-jy-package.alignment.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.ALIGNMENT')


class Alignment:
    def __init__(self, alignment_dir, working_dir, tiff_ext, error_subfolder_name, input_dir, precrop_input_dir, forceSave):
        self.alignment_dir = alignment_dir
        self.working_dir = working_dir
        self.tiff_ext = tiff_ext
        self.error_subfolder_name = error_subfolder_name
        self.input_dir = input_dir
        self.precrop_input_dir = precrop_input_dir
        self.force_save = int(forceSave[0])
        self.tempfile = os.path.join(self.working_dir, "temp_align.csv")



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
            file_path = ht.correct_path(dir_path, path)
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
                os.remove(ht.correct_path(dir, img_file))

    def Composite_Aligner(self, img_paths, max_files_numbers, alignment_feature_extraction_model,
                          alignment_registration_model, params_background, folder_to_precrop, dapi_selected, autoContrastSelection):
        """ Aligns composite images, saves to target directory. """
        # Source, output and transformations directories
        alignment_dir = self.alignment_dir
        temp_input_dir = ht.correct_path(alignment_dir, "temp\\")
        target_dir = ht.correct_path(alignment_dir, "out\\")
        transf_dir = ht.correct_path(alignment_dir, "transforms\\")
        # Creates dir if dir does not exist.
        if not os.path.exists(temp_input_dir):
            os.makedirs(temp_input_dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        if not os.path.exists(transf_dir):
            os.makedirs(transf_dir)
        patient_IDs_aligned = []
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
            stack_path = ht.correct_path(alignment_dir, stack_name + self.tiff_ext)
            # Save output
            if (not os.path.exists(stack_path)) or not (patient in x for x in
                                                        os.listdir(folder_to_precrop)) or self.force_save == 1:
                for subfolder in img_paths[patient].keys():
                    for img_path in img_paths[patient][subfolder]:
                        filename_=os.path.basename(img_path)
                        if "dapi" in filename_ and not "dapi_copy" in filename_:
                            shutil.copy(img_path, ht.correct_path(temp_input_dir, filename_))

                if autoContrastSelection == "Selected":
                    self.applyAutoContrast(temp_input_dir)

                p = Register_Virtual_Stack_MT.Param()

                # parameters:
                p.sift.maxOctaveSize = 1024
                p.sift.minOctaveSize = 64
                p.sift.steps = 12
                p.sift.initialSigma = 1.6
                p.sift.fdBins = 8
                p.sift.fdSize = 8
                # 1 = RIGID
                alignment_feature_extraction_models = ["Translation", "Rigid", "Similarity", "Affine"]
                alignment_feature_extraction_model_index = alignment_feature_extraction_models.index(
                    alignment_feature_extraction_model
                )

                p.featuresModelIndex = alignment_feature_extraction_model_index
                alignment_registration_models = ["Translate --no deformation", "Rigid --translate + rotate",
                                                 "Similarity --translate + rotate + isotropic scale",
                                                 "Affine --free affine transform", "Elastic --bUnwarpJ splines",
                                                 "Moving least squares -- maximal warping"]
                alignment_registration_model_index = alignment_registration_models.index(alignment_registration_model)
                p.registrationModelIndex = alignment_registration_model_index

                # The "inlier ratio":
                p.minInlierRatio = 0.05

                # Reference image name (must be within source directory)
                reference_name = os.path.basename(iter(os.listdir(temp_input_dir)).next())
                for dapi_ref_selected_patient in dapi_selected:
                    if patient in dapi_ref_selected_patient:
                        dapi_selected_ref = dapi_selected[dapi_ref_selected_patient]
                        if dapi_selected_ref in os.listdir(temp_input_dir):
                            reference_name = dapi_selected_ref
                            logger.info("selected dapi_ref from csv used")
                            logger.info(dapi_selected_ref)
#                            break
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
                    os.remove(ht.correct_path(temp_input_dir, img_file))
                # Close alignment window.
                imp = WindowManager.getCurrentImage()
                if imp:
                    patient_IDs_aligned.append(patient)
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
                        shutil.copy(img_path, ht.correct_path(temp_input_dir, os.path.basename(img_path)))
                    check_transform = Transform_Virtual_Stack_MT.exec(temp_input_dir, target_dir, transf_dir,
                                                                      interpolate)
                    if check_transform:
                        logger.info("batch " + str(i) + " of " + patient + " is successfully transformed")
                    for img_file in os.listdir(temp_input_dir):
                        os.remove(ht.correct_path(temp_input_dir, img_file))
                    # Close alignment window.
                    imp = WindowManager.getCurrentImage()
                    imp.close()
                for img_file in os.listdir(transf_dir):
                    os.remove(ht.correct_path(transf_dir, img_file))
                vs = None
                width, height = 0, 0
                try:
                    width, height = self.get_max_dims(target_dir)
                except TypeError:
                    logger.exception(sys.exc_info())
                # Initialize the VirtualStack
                if vs is None and self.get_files_number(target_dir, self.tiff_ext) > 1:
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
                    stack_path = ht.correct_path(alignment_dir, stack_name + self.tiff_ext)
                    # Save output
                    if (not os.path.exists(stack_path)) or self.force_save == 1:
                        logger.info("Saving the stack as " + stack_path)
                        FileSaver(imp).saveAsTiff(stack_path)
                    else:
                        logger.warning("The stack file " + stack_path + " exists. Skipping")
                elif vs is None and self.get_files_number(target_dir, self.tiff_ext) == 1:
                    logger.warning("The number of image files is less than 2. For stack it should be at least 2. "
                                   "Skipping")
                    continue
                for img_file in os.listdir(target_dir):
                    os.remove(ht.correct_path(target_dir, img_file))
            else:
                logger.warning(stack_path + " exists. Skipping")
                patient_IDs_aligned.append(patient)
        logger.info("Run is finished")
        self.delete_files_from_process_folders([temp_input_dir, target_dir, transf_dir])
        shutil.rmtree(temp_input_dir)
        shutil.rmtree(target_dir)
        shutil.rmtree(transf_dir)
        return patient_IDs_aligned, patients_to_crop

    def applyAutoContrast(self, temp_input_dir):
        for im in os.listdir(temp_input_dir):
            im_path = ht.correct_path(temp_input_dir, im)
            imp1 = IJ.openImage(im_path)
            imp1.show()
            IJ.run(imp1, "Enhance Contrast", "saturated=0.35")
            logger.info("Saving the " + str(im))
            FileSaver(imp1).saveAsTiff(im_path)
            imp1.close()
    def create_stack(self, target_dir):
        images = []
        for filename in os.listdir(target_dir):
            if not "_copy_" in filename:
                imp = IJ.openImage(ht.correct_path(target_dir, filename))
                if imp:
                    images.append(imp)
        stack = None
        if images:
            stack = ImagesToStack.run(images)
        return stack

    def stack_creation_single_batch(self, img_paths, params_background):
        alignment_dir = self.alignment_dir
        patient_IDs_single_batch_stack_created = []
        for patient in img_paths.keys():
            for subfolder in img_paths[patient].keys():
                for img_path in img_paths[patient][subfolder]:
                    target_dir = os.path.dirname(img_path)
                    stack_name = patient
                    vs = None
                    width, height = 0, 0
                    try:
                        width, height = self.get_max_dims(target_dir)
                    except TypeError:
                        logger.exception(sys.exc_info())
                    # Initialize the VirtualStack
                    if vs is None and self.get_files_number(target_dir, self.tiff_ext) > 1:
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
                        stack_path = ht.correct_path(alignment_dir, stack_name + self.tiff_ext)
                        # Save output
                        if (not os.path.exists(stack_path)) or self.force_save == 1:
                            logger.info("Saving the stack as " + stack_path)
                            FileSaver(imp).saveAsTiff(stack_path)
                        else:
                            logger.warning("The stack file " + stack_path + " exists. Skipping")
                        patient_IDs_single_batch_stack_created.append(patient)
                    elif vs is None and self.get_files_number(target_dir, self.tiff_ext) == 1:
                        logger.warning("The number of image files is less than 2. For stack it should be at least 2. "
                                       "Skipping")
                        continue
        return patient_IDs_single_batch_stack_created

    #def ask_for_parameters(self):
    #    gui = GenericDialog("Alignment: Input parameters")
    #    gui.addMessage("Choose the type of feature extraction model")
    #    gui.addChoice("Feature Extraction Model", ["Translation", "Rigid", "Similarity", "Affine"],
    #                  "Rigid")  # rigidBody is default here
    #    gui.addMessage("Choose the type of registration model")
    #    gui.addChoice("Registration model", ["Translate --no deformation", "Rigid --translate + rotate",
    #                                         "Similarity --translate + rotate + isotropic scale",
    #                                         "Affine --free affine transform", "Elastic --bUnwarpJ splines",
    #                                         "Moving least squares -- maximal warping"], "Rigid --translate + rotate")
    #    gui.addMessage("")
    #    gui.addMessage("Background Parameters for DAPI channel images")
    #    gui.addNumericField("Radius", 50, 0)  # 0 for no decimal part
    #    # gui.addMessage("Overwrite option")
    #    # gui.addCheckbox("forceSave", False)
    #    gui.showDialog()
    #    if gui.wasCanceled():
    #        logger.warning("User canceled dialog! Doing nothing. Exit")
    #        return
    #    bg_params = {
    #        "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
    #        "createBackground": False,
    #        "lightBackground": False,
    #        "useParaboloid": False,
    #        "doPresmooth": False,
    #        "correctCorners": False
    #    }
    #    alignment_feature_extraction_model = gui.getNextChoice()
    #    alignment_registration_model = gui.getNextChoice()
    #    # force_save = gui.getNextBoolean()

    #    # return [alignment_feature_extraction_model, alignment_registration_model, bg_params, force_save]
    #    return [alignment_feature_extraction_model, alignment_registration_model, bg_params]

    def get_max_dims(self, dir):
        files = [filename for filename in os.listdir(dir) if os.path.isfile(ht.correct_path(dir, filename))]
        width_list = []
        height_list = []
        for filename in files:
            width, height = ht.dimensions_of(ht.correct_path(dir, filename),
                                             self.alignment_dir, self.error_subfolder_name)
            width_list.append(width)
            height_list.append(height)
        return max(width_list), max(height_list)

    def aligning(self):
        logger.info("Current IMAGEJ version: " + IJ.getVersion())
        # try:
            # Input Parameters_dir

            # update_input_dir, params_background, force_save = self.ask_for_parameters()
            # alignment_feature_extraction_model, alignment_registration_model, params_background, force_save = self.ask_for_parameters()
        #    alignment_feature_extraction_model, alignment_registration_model, params_background = self.ask_for_parameters()
        # except:
            # user canceled dialog
        #    return
        if not os.path.exists(self.tempfile):
            logger.warning("No csv file was found. Something went wrong when setting the parameters in the the "
                           "dialog for setting the parameters for alignment. The user may have cancelled it or "
                           "deleted it. Repeat the step if you want to align the channel images "
                           "with the DAPI image as reference and set the parameters. Doing nothing.")
            return
        try:
            data = ht.read_data_from_csv(self.tempfile)
        except:
            logger.exception("Could not get the input parameters. Exiting")
            return
        patientIDs_csv = []
        dapi_selected = {}
        featureextractionmodeltypechoosen = []
        registrationmodeltypechoosen = []
        dapi_selected_bg = []
        autoContrast_selected = []
        for case in data:
            patientIDs_csv.append(case['patientID'])
            dapi_selected[case['patientID']] = case['selected_dapi_file']
            featureextractionmodeltypechoosen.append(case['selected_featureextractionmodeltype'])
            registrationmodeltypechoosen.append(case['selected_registrationmodeltype'])
            dapi_selected_bg.append(case['dapi_selected_bg'])
            autoContrast_selected.append(case['selected_autoContrast'])
        #logger.info(dapi_selected)
        alignment_feature_extraction_model = list(set(featureextractionmodeltypechoosen))[0]
        alignment_registration_model = list(set(registrationmodeltypechoosen))[0]
        params_background = list(set(dapi_selected_bg))[0]
        params_bg = {"radius": int(params_background),
                                            "createBackground": False,
                                            "lightBackground": False,
                                            "useParaboloid": False,
                                            "doPresmooth": False,
                                            "correctCorners": False, }
        autoContrastSelection = list(set(autoContrast_selected))[0]
        update_input_dir = self.input_dir
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
        selected_patients = []
        patients = list(set(subfolder_patients))
        if patients == patientIDs_csv:
            selected_patients = patients
        else:
            logger.warning("There are data in the input folder, which don't belong to the current workflow. Only the data of the current workflow will be processed")
            selected_patients = patientIDs_csv
        counts = []
        for patient in selected_patients:
            counts.append(self.get_patient_subfolder_number(subfolder_patients, patient))
        selected_patients_for_alignment = []
        selected_patients_with_single_batch = []
        for count, patient in zip(counts, selected_patients):
            if count > 1:
                selected_patients_for_alignment.append(patient)
            elif count == 1:
                selected_patients_with_single_batch.append(patient)
        selected_patients_for_alignment = list(set(selected_patients_for_alignment))
        selected_patients_with_single_batch = list(set(selected_patients_with_single_batch))
        if not selected_patients_for_alignment:
            logger.warning("There is no  patient id with more than one batch of the images to align. Doing nothing")
        if not selected_patients_with_single_batch:
            logger.warning(
                "There is no  patient id with one batch of the images to create a stack with a single batch. Doing nothing")
        selected_patient_subfolder_img_paths_dict = {}
        subdir_files_number = {}  # Empty dictionary to add values into
        max_files_numbers = {}
        for patient in selected_patients_for_alignment:
            selected_patient_subfolder_img_paths_dict[patient] = {}
            subdir_files_number[patient] = {}
            for subfolder in subdirs:
                if os.path.basename(subfolder).split("_")[1] == patient:
                    selected_patient_subfolder_img_paths_list = []
                    for img in os.listdir(subfolder):
                        selected_patient_subfolder_img_paths_list.append(
                            ht.correct_path(update_input_dir, subfolder, img))
                    subdir_files_number[patient][subfolder] = self.get_files_number(
                        ht.correct_path(update_input_dir, subfolder),
                        self.tiff_ext)
                    selected_patient_subfolder_img_paths_dict[patient][
                        subfolder] = selected_patient_subfolder_img_paths_list
            max_files_numbers[patient] = max(subdir_files_number[patient].values())
        # check and add dapi file copies to the subfolders of each patient if needed 
        for patient in selected_patients_for_alignment:
            for subfolder in selected_patient_subfolder_img_paths_dict[patient]:
                dirpath = ht.correct_path(update_input_dir, subfolder)
                dapifiles = ht.dapi_tiff_image_filenames(dirpath, config.dapi_str, self.tiff_ext)
                if not dapifiles == []:
                    dapipath = ht.correct_path(dirpath, dapifiles[0])
                    logger.info("Processing the subfolder " + os.path.dirname(dapipath))
                    if subdir_files_number[patient][subfolder] < max_files_numbers[patient]:
                        # add dapi file copies if max_file_number greater than current subfolder file number
                        logger.info(
                            "Copying the dapi file " + os.path.basename(dapipath) + " in the subfolder " +
                            ht.correct_path(update_input_dir, os.path.dirname(dapipath)))
                        dapi_filename_suffix = range(1, max_files_numbers[patient] - subdir_files_number[patient][
                            subfolder] + 1)
                        self.copy_file(dapipath, dapi_filename_suffix)
        # update dictionary according copy dapi file
        for patient in selected_patients_for_alignment:
            selected_patient_subfolder_img_paths_dict[patient] = {}
            for subfolder in subdirs:
                if os.path.basename(subfolder).split("_")[1] == patient:
                    selected_patient_subfolder_img_paths_list = []
                    for img in os.listdir(subfolder):
                        selected_patient_subfolder_img_paths_list.append(
                            ht.correct_path(update_input_dir, subfolder, img))
                    selected_patient_subfolder_img_paths_dict[patient][
                        subfolder] = selected_patient_subfolder_img_paths_list
        selected_patient_with_single_batch_subfolder_img_paths_dict = {}
        for patient in selected_patients_with_single_batch:
            selected_patient_with_single_batch_subfolder_img_paths_dict[patient] = {}
            for subfolder in subdirs:
                if os.path.basename(subfolder).split("_")[1] == patient:
                    selected_patient_with_single_batch_subfolder_img_paths_list = []
                    for img in os.listdir(subfolder):
                        selected_patient_with_single_batch_subfolder_img_paths_list.append(
                            ht.correct_path(update_input_dir, subfolder, img))
                    selected_patient_with_single_batch_subfolder_img_paths_dict[patient][
                        subfolder] = selected_patient_with_single_batch_subfolder_img_paths_list

        patient_IDs_aligned, patients_to_precrop = self.Composite_Aligner(selected_patient_subfolder_img_paths_dict,
                                                                          max_files_numbers,
                                                                          alignment_feature_extraction_model,
                                                                          alignment_registration_model,
                                                                          params_bg,
                                                                          folder_to_precrop, dapi_selected, autoContrastSelection)
        patient_IDs_single_batch_stack_created = self.stack_creation_single_batch(selected_patient_with_single_batch_subfolder_img_paths_dict, params_bg)
        logger.info("The list of patient IDs successfully aligned " + str(
            patient_IDs_aligned) + "\nThe list of patients IDs to crop and realign " + str(patients_to_precrop) + "\nThe list of patient IDs with stacked single batch" + str(patient_IDs_single_batch_stack_created))
        for folder in subdirs:
            for patient_to_precrop in patients_to_precrop:
                if patient_to_precrop in os.path.basename(folder):
                    precrop_subfolder = ht.correct_path(folder_to_precrop, os.path.basename(folder))
                    if not os.path.exists(precrop_subfolder):
                        os.makedirs(precrop_subfolder)
                    for filename in os.listdir(folder):
                        shutil.copy(ht.correct_path(folder, filename),
                                    ht.correct_path(precrop_subfolder, os.path.basename(filename)))
