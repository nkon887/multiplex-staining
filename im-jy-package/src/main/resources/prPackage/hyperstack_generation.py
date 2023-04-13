# Walk recursively through an user-selected directory
# and for each subfolder add all found filenames that end with ".tif"
# to a VirtualStack, substract Background, adjust and generate Hyperstack
# It is assumed that all images are of the same type
# and have the same dimensions
# you can choose to overwrite the already generated output
import os
import shutil
import sys
import re

from ij import IJ, ImagePlus, VirtualStack
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin import HyperStackConverter

sys.path.append(os.path.abspath(os.getcwd()))
import config
import helpertools as ht


class HyperstackGeneration:
    def __init__(self, input_dir, stacks_dir, tiff_ext):
        self.input_dir = input_dir
        self.stacks_dir = stacks_dir
        self.tiff_ext = tiff_ext

    def ask_for_parameters(self):
        gui = GenericDialog("Input parameters")
        gui.addDirectoryField("DirectorPath", self.input_dir)
        gui.addMessage("Hyperstack Parameters")
        gui.addNumericField("frames_number", 1)
        gui.addNumericField("slices_number", 1)
        gui.addChoice("order", ["xyzct", "xyczt(default)", "xyctz", "xyztc", "xytcz", "xytzc"],
                      "xyczt(default)")  # xyczt(default) is default here
        gui.addChoice("color", ["Color", "Composite", "Grayscale"], "Grayscale")  # Grayscale is default here
        gui.addMessage("Overwrite option")
        gui.addCheckbox("forceSave", False)
        gui.showDialog()
        if gui.wasCanceled():
            print("User canceled dialog! Doing nothing. Exit")
            return
        folder_path = gui.getNextString()
        hyperstack_params = {
            "number_frames": int(gui.getNextNumber()),
            "number_slices": int(gui.getNextNumber()),
            "order": gui.getNextChoice().split("(")[0],
            "color": gui.getNextChoice()
        }
        force_save = gui.getNextBoolean()
        return [folder_path, hyperstack_params, force_save]

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

    def generate_hyperstack(self):
        imagejversion = IJ.getVersion()
        IJ.log("Current IMAGEJ version: " + imagejversion)
        try:
            # Input Parameters
            update_input_dir, params_hyperstack, force_save = self.ask_for_parameters()
        except:
            # user canceled dialog
            return
        if not os.path.exists(update_input_dir):
            print("The input directory doesn't exist. Doing nothing.Exiting")
            return
        pattern = r'^\d{6}\_[^\_]*'
        subdirs = [x[0] for x in os.walk(update_input_dir) if re.match(pattern, os.path.basename(x[0]))]
        if not subdirs:
            print(update_input_dir + " is empty. Doing nothing")
            return

        for subdir in subdirs:
            hyperstack_name = os.path.basename(subdir)
            stack_name = hyperstack_name
            vs = None
            width, height = 0, 0
            dirpath = os.path.join(update_input_dir, subdir)
            dapifiles = ht.dapi_tiff_image_filenames(dirpath, config.dapi_str, self.tiff_ext)
            if not dapifiles == []:
                dapipath = os.path.join(dirpath, dapifiles[0])
                print("Processing the subfolder " + os.path.dirname(dapipath))
                try:
                    width, height = ht.dimensions_of(dapipath, self.stacks_dir, config.error_subfolder_name)
                except TypeError:
                    print(sys.exc_info())
                # Upon finding the dapi image, initialize the VirtualStack
                if vs is None and self.get_files_number(dirpath, self.tiff_ext) > 1:
                    vs = CreateVirtualStack(width, height, dirpath)
                    hyperstack_folder = hyperstack_name.split("_")[1].split(".")[0]
                    hyperstack_folder_path = ht.setting_directory(self.stacks_dir, hyperstack_folder)
                    hyperstack_path = os.path.join(hyperstack_folder_path, hyperstack_name + self.tiff_ext).replace(
                        "\\",
                        "/")
                    # Save output
                    if (not os.path.exists(hyperstack_path)) or force_save:
                        print("Saving the hyperstack as " + hyperstack_path)
                        stack = ImagePlus(stack_name, vs)
                        number_channels = stack.getNSlices()
                        FileSaver(
                            HyperStackConverter.toHyperStack(stack, number_channels, params_hyperstack["number_frames"],
                                                             params_hyperstack["number_slices"],
                                                             params_hyperstack["order"],
                                                             params_hyperstack["color"])).saveAsTiff(hyperstack_path)
                    else:
                        print("The hyperstack file " + hyperstack_path + " exists. Skipping")
                elif vs is None and self.get_files_number(dirpath, self.tiff_ext) == 1:
                    print("The number of image files is less than 2. For hyperstack it should be at least 2. Skipping")
                    continue
            if os.path.abspath(update_input_dir) == os.path.abspath(self.input_dir):
                for filename in os.listdir(subdir):
                    os.remove(os.path.join(subdir, filename))
                shutil.rmtree(os.path.join(subdir))

        print("Run is finished")
        return


class CreateVirtualStack(VirtualStack):
    def __init__(self, width, height, source_dir):
        # Tell the superclass to initialize itself with the sourceDir
        super(VirtualStack, self).__init__(width, height, None, source_dir)
        # Store the parameters for the NormalizeLocalContrast
        file_list = sorted(os.listdir(source_dir))
        dapi_index_list = []
        for item in file_list:
            if "dapi" in item:
                dapi_index_list.append(file_list.index(item))
        count = 0
        if dapi_index_list:
            for dapi_file_index in dapi_index_list:
                file_list.insert(0 + count, file_list.pop(dapi_file_index))
                count += 1
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
        return ip
