
import os
import shutil
import re
import sys
import time
from java.lang import System
from ij.gui import GenericDialog
from ij import IJ, WindowManager, ImagePlus, VirtualStack
from register_virtual_stack import Register_Virtual_Stack_MT, Transform_Virtual_Stack_MT
from ij.plugin.filter import BackgroundSubtracter
from ij.io import FileSaver

sys.path.append(os.path.abspath(os.getcwd()))
import config
import pythontools as pt
import jythontools as jt
import config


class CreateVirtualStack(VirtualStack):
    def __init__(self, width, height, source_dir, params):
        # Tell the superclass to initialize itself with the sourceDir
        super(VirtualStack, self).__init__(width, height, None, source_dir)
        # Store the parameters for the NormalizeLocalContrast
        self.params = params
        file_list = sorted(os.listdir(source_dir))
        # Set all TIFF files in sourceDir as slices
        for filename in file_list:
            if filename.endswith(".tif"):
                self.addSlice(filename)

    def getProcessor(self, n):
        # Load the image at index n
        filepath = os.path.join(self.getDirectory(), self.getFileName(n))
        imp = IJ.openImage(filepath)
        if imp.isStack() or imp.isHyperStack():
            pass
        # Subtract background
        ip = imp.getProcessor()
        if "dapi" in self.getFileName(n):
            radius = self.params["radius"]
            create_background = self.params["createBackground"]
            light_background = self.params["lightBackground"]
            use_paraboloid = self.params["useParaboloid"]
            do_presmooth = self.params["doPresmooth"]
            correct_corners = self.params["correctCorners"]
            bs = BackgroundSubtracter()
            bs.rollingBallBackground(ip, radius, create_background, light_background, use_paraboloid, do_presmooth,
                                     correct_corners)
        return ip


def get_patient_subfolder_number(patients, item):
    # folder path
    count = 0
    # Iterate directory
    for curr_item in patients:
        if curr_item == item:
            count += 1
    return count


def get_files_number(dir_path, ext):
    # folder path
    count = 0
    # Iterate directory
    for path in os.listdir(dir_path):
        # check if current path is a file
        file_path = os.path.join(dir_path, path)
        if os.path.isfile(file_path) and file_path.endswith(ext):
            count += 1
    return count


def copy_file(filename, filename_suffix):
    # Copy filename+ext into a new filename_copy_i+ext i in filename_suffix range
    file_name, ext = filename.split('.')
    for i in filename_suffix:
        file_destination = file_name + "_copy_" + str(i) + "." + ext
        if not os.path.exists(file_destination):
            shutil.copy(filename, file_destination)


def delete_files_from_process_folders(list_of_dirs):
    for dir in list_of_dirs:
        for img_file in os.listdir(dir):
            os.remove(os.path.join(dir, img_file))


def Composite_Aligner(img_paths, max_files_numbers, params_background, folder_to_precrop, force_save):
    """ Aligns composite images, saves to target directory. """

    # Source, output and transformations directories
    alignmentDirSV = config.alignmentDirSV
    temp_input_dir = os.path.join(alignmentDirSV, "temp\\")
    target_dir = os.path.join(alignmentDirSV, "out\\")
    transf_dir = os.path.join(alignmentDirSV, "transforms\\")
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
                delete_files_from_process_folders([temp_input_dir])
        for dirpath, dirnames, files in os.walk(target_dir):
            if files:
                delete_files_from_process_folders([target_dir])                
        for dirpath, dirnames, files in os.walk(transf_dir):   
            if files:
                delete_files_from_process_folders([transf_dir])                
        stack_name = patient
        stack_path = os.path.join(alignmentDirSV, stack_name + config.tiff_ext).replace("\\", "/")
        # Save output
        if (not os.path.exists(stack_path)) or not(patient in x for x in os.listdir(folder_to_precrop)) or force_save:
            for subfolder in img_paths[patient].keys():
                for img_path in img_paths[patient][subfolder]:
                    print(img_path)
                    if "dapi" in os.path.basename(img_path) and not "dapi_copy" in os.path.basename(img_path):
                        shutil.copy(img_path, os.path.join(temp_input_dir, os.path.basename(img_path)))

            # Shrinkage option (False = 0)
            use_shrinking_constraint = 1

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
            print(reference_name)
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
            print("Aligning...")
            try:
                Register_Virtual_Stack_MT.exec(temp_input_dir, target_dir, transf_dir, reference_name, p,
                                               use_shrinking_constraint)
            except:
                print(sys.exc_info())
            for img_file in os.listdir(temp_input_dir):
                os.remove(os.path.join(temp_input_dir, img_file))
            # Close alignment window.
            imp = WindowManager.getCurrentImage()
            if imp:
                imp.close()
            else:
                print(patient + " couldn't be processed")
                patients_to_crop.append(patient)
                continue
            max_files_number = max_files_numbers[patient] - 1
            for i in range(max_files_number):
                for subfolder in img_paths[patient].keys():
                    img_path_list = [x for x in img_paths[patient][subfolder] if "dapi.tif" not in os.path.basename(x)]
                    img_path = img_path_list[i]
                    shutil.copy(img_path, os.path.join(temp_input_dir, os.path.basename(img_path)))
                check_transform = Transform_Virtual_Stack_MT.exec(temp_input_dir, target_dir, transf_dir, interpolate)
                if check_transform:
                    print("batch " + str(i) + " of " + patient + " is successfully transformed")
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
                width, height = jt.dimensions_of(os.path.join(target_dir, iter(os.listdir(target_dir)).next()),
                                                 alignmentDirSV, config.error_subfolder_name)
            except TypeError:
                print(sys.exc_info())
            # Initialize the VirtualStack
            if vs is None and get_files_number(target_dir, config.tiff_ext) > 1:
                vs = CreateVirtualStack(width, height, target_dir, params_background)
                stack_path = os.path.join(alignmentDirSV, stack_name + config.tiff_ext).replace("\\", "/")
                # Save output
                if (not os.path.exists(stack_path)) or force_save:
                    print("Saving the stack as " + stack_path)
                    stack = ImagePlus(stack_name, vs)
                    FileSaver(stack).saveAsTiff(stack_path)
                else:
                    print("The stack file " + stack_path + " exists. Skipping")
            elif vs is None and get_files_number(target_dir, config.tiff_ext) == 1:
                print("The number of image files is less than 2. For stack it should be at least 2. Skipping")
                continue
            for img_file in os.listdir(target_dir):
                os.remove(os.path.join(target_dir, img_file))
        else:
            print(stack_path + " exists. Skipping")
    print("Run is finished")
    delete_files_from_process_folders([temp_input_dir, target_dir, transf_dir])
    shutil.rmtree(temp_input_dir)
    shutil.rmtree(target_dir)
    shutil.rmtree(transf_dir)
    return patients_to_crop


def ask_for_parameters():
    gui = GenericDialog("Input parameters")
    gui.addDirectoryField("Directory Path", config.inputDir)
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
        print("User canceled dialog! Doing nothing. Exit")
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


def main():
    try:
        # Input Parameters
        input_dir, params_background, force_save = ask_for_parameters()
    except:
        # user canceled dialog
        return
    if not os.path.exists(input_dir):
        print("The input directory doesn't exist. Doing nothing.Exiting")
        return
    pattern = r'^\d{6}\_[^\_]*'
    folder_to_precrop = config.precrop_input_dir
    subdirs = [x[0] for x in os.walk(input_dir) if re.match(pattern, os.path.basename(x[0]))]
    if not subdirs:
        print(input_dir + " is empty. Doing nothing")
        return

    subfolder_patients = []
    for folder in subdirs:
        print(os.path.basename(folder).split("_")[1])
        subfolder_patients.append(os.path.basename(folder).split("_")[1])
    patients = list(set(subfolder_patients))
    print(patients)
    counts = []
    for patient in patients:
        counts.append(get_patient_subfolder_number(subfolder_patients, patient))
    print(counts)
    selected_patients = []
    for count, patient in zip(counts, patients):
        if count > 1:
            selected_patients.append(patient)
    print(selected_patients)
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
                    selected_patient_subfolder_img_paths_list.append(os.path.join(input_dir, subfolder, img))
                subdir_files_number[patient][subfolder] = get_files_number(os.path.join(input_dir, subfolder),
                                                                           config.tiff_ext)
                selected_patient_subfolder_img_paths_dict[patient][
                    subfolder] = selected_patient_subfolder_img_paths_list
        max_files_numbers[patient] = max(subdir_files_number[patient].values())
    print(subdir_files_number)
    print(max_files_numbers)
    selected_patient_subfolder_img_paths_list = []
    print(selected_patient_subfolder_img_paths_dict)
    # check and add dapi file copies to the subfolders of each patient if needed 
    for patient in selected_patients:
        for subfolder in selected_patient_subfolder_img_paths_dict[patient]:
            dirpath = os.path.join(input_dir, subfolder)
            dapifiles = pt.dapi_tiff_image_filenames(dirpath, config.dapi_str, config.tiff_ext)
            if not dapifiles == []:
                dapipath = os.path.join(dirpath, dapifiles[0])
                print("Processing the subfolder " + os.path.dirname(dapipath))
                if subdir_files_number[patient][subfolder] < max_files_numbers[patient]:
                    # add dapi file copies if max_file_number greater then current subfolder file number
                    print(
                        "Copying the dapi file " + os.path.basename(dapipath) + " in the subfolder " + os.path.join(
                            input_dir,
                            os.path.dirname(
                                dapipath)))
                    dapi_filename_suffix = range(1, max_files_numbers[patient] - subdir_files_number[patient][
                        subfolder] + 1)
                    copy_file(dapipath, dapi_filename_suffix)
                    # update dictionary according copy dapi file
                    for img in os.listdir(subfolder):
                        selected_patient_subfolder_img_paths_list.append(os.path.join(input_dir, subfolder, img))
                    selected_patient_subfolder_img_paths_dict[patient][
                        subfolder] = selected_patient_subfolder_img_paths_list
    
    patients_to_precrop = Composite_Aligner(selected_patient_subfolder_img_paths_dict, max_files_numbers,
                                            params_background, folder_to_precrop, force_save)
    if not patients_to_precrop == []:
        print("The list of patients to crop " + str(patients_to_precrop))
    for folder in subdirs:
        for patient_to_precrop in patients_to_precrop:
            if patient_to_precrop in os.path.basename(folder):
                precrop_subfolder = os.path.join(folder_to_precrop, os.path.basename(folder))
                if not os.path.exists(precrop_subfolder):
                    os.makedirs(precrop_subfolder)
                for filename in os.listdir(folder):
                    shutil.copy(os.path.join(folder, filename), os.path.join(precrop_subfolder, os.path.basename(filename)))


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
