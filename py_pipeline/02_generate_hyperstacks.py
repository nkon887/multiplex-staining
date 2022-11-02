# Walk recursively through an user-selected directory
# and for each subfolder add all found filenames that end with ".tif"
# to a VirtualStack, substract Background, adjust and generate Hyperstack
# It is assumed that all images are of the same type
# and have the same dimensions
# you can choose to overwrite the already generated output
import os
import sys

from ij import IJ, ImagePlus, VirtualStack
from ij.io import DirectoryChooser
from ij.io import FileSaver
from loci.formats import ChannelSeparator
from ij.plugin.filter import BackgroundSubtracter
from ij.plugin import HyperStackConverter
from ij.gui import GenericDialog
import shutil


class CreateVirtualStack(VirtualStack):
    def __init__(self, width, height, sourceDir, params):
        # Tell the superclass to initialize itself with the sourceDir
        super(VirtualStack, self).__init__(width, height, None, sourceDir)
        # Store the parameters for the NormalizeLocalContrast
        self.params = params
        # Set all TIFF files in sourceDir as slices
        for filename in sorted(os.listdir(sourceDir)):
            if filename.endswith(".tif") and not (os.path.basename(filename) in ["Stack.tif", "Hyperstack.tif"]):
                self.addSlice(filename)

    def getProcessor(self, n):
        # Load the image at index n
        filepath = os.path.join(self.getDirectory(), self.getFileName(n))
        imp = IJ.openImage(filepath)
        if imp.isStack() or imp.isHyperStack():
            pass
        # Substract backgrund
        ip = imp.getProcessor()
        radius = self.params["radius"]
        createBackground = self.params["createBackground"]
        lightBackground = self.params["lightBackground"]
        useParaboloid = self.params["useParaboloid"]
        doPresmooth = self.params["doPresmooth"]
        correctCorners = self.params["correctCorners"]
        bs = BackgroundSubtracter()
        bs.rollingBallBackground(ip, radius, createBackground, lightBackground, useParaboloid, doPresmooth,
                                 correctCorners)
        return ip


def dimensionsOf(path):
    fr = None
    try:
        fr = ChannelSeparator()
        fr.setGroupFiles(False)
        fr.setId(path)
        return fr.getSizeX(), fr.getSizeY()
    except:
        # Print the error, if any
        print
        sys.exc_info()
    finally:
        fr.close()


def dapiTiffImageFilenames(directory, dapi_str, ext):
    dapiTiffFiles = []
    files = os.listdir(directory)
    if not files == []:
        for filename in sorted(files):
            if ((dapi_str or dapi_str.upper() or dapi_str.lower()) in filename) and (filename.endswith(ext)):
                dapiTiffFiles.append(filename)
    return dapiTiffFiles


def ask_for_parameters():
    gui = GenericDialog("Input parameters")
    gui.addDirectoryField("DirectorPath", "DefaultFolderPath")
    gui.addMessage("Background Parameters")
    gui.addNumericField("Radius", 50, 0)  # 0 for no decimal part
    gui.addCheckbox("createBackground", False)
    gui.addCheckbox("lightBackground", False)
    gui.addCheckbox("useParaboloid", False)
    gui.addCheckbox("doPresmooth", False)
    gui.addCheckbox("correctCorners", False)
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
        IJ.log("User canceled dialog!")
        return
    folderPath = gui.getNextString()
    bg_params = {
        "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
        "createBackground": gui.getNextBoolean(),
        "lightBackground": gui.getNextBoolean(),
        "useParaboloid": gui.getNextBoolean(),
        "doPresmooth": gui.getNextBoolean(),
        "correctCorners": gui.getNextBoolean()
    }
    hyperstack_params = {
        "number_frames": gui.getNextNumber(),
        "number_slices": gui.getNextNumber(),
        "order": gui.getNextChoice(),
        "color": gui.getNextChoice()
    }
    forceSave = gui.getNextBoolean()
    return [folderPath, bg_params, hyperstack_params, forceSave
            ]


def get_files_number(dir_path, ext, stack_name, hyperstack_name):
    # folder path
    count = 0
    # Iterate directory
    for path in os.listdir(dir_path):
        # check if current path is a file
        file_path = os.path.join(dir_path, path)
        if os.path.isfile(file_path) and file_path.endswith(ext) and not (
                os.path.basename(file_path) in [stack_name + ext, hyperstack_name + ext]):
            count += 1
    return count


def copy_file(filename, filename_suffix):
    # Copy filename+ext into a new filename_copy_i+ext i in filename_suffix range
    file_name, ext = filename.split('.')
    for i in filename_suffix:
        file_destination = file_name + "_copy_" + str(i) + ext
        if not os.path.exists(file_destination):
            shutil.copy(filename, file_destination)


def run():
    dapi_str = "dapi"
    ext = ".tif"

    # Input Parameters
    srcDir, params_background, params_hyperstack, force_save = ask_for_parameters()
    if not srcDir:
        # user canceled dialog
        return
    subdirs = [x[0] for x in os.walk(srcDir)]
    if not subdirs:
        return
    if force_save is None:
        force_save = False
    outputDir = os.path.join(srcDir, "hyperstacks")
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    hyperstack_name = ""
    stack_name = "Stack"
    subdir_files_number = {}  # Empty dictionary to add values into

    for subdir in subdirs:
        hyperstack_name = subdir
        subdir_files_number[subdir] = get_files_number(os.path.join(srcDir, subdir), ext, stack_name,
                                                       hyperstack_name)
    max_files_number = max(subdir_files_number.values())

    for subdir in subdirs:
        vs = None
        width, height = 0, 0
        dirpath = os.path.join(srcDir, subdir)
        dapifiles = dapiTiffImageFilenames(dirpath, dapi_str, ext)
        if not dapifiles == []:
            dapipath = os.path.join(dirpath, dapifiles[0])
            IJ.log("Processing the subfolder " + os.path.dirname(dapipath))
            if subdir_files_number[subdir] < max_files_number:
                IJ.log(
                    "Copying the dapi file " + os.path.basename(dapipath) + " in the subfolder " + os.path.join(srcDir,
                                                                                                                os.path.dirname(
                                                                                                                    dapipath)))
                dapi_filename_suffix = range(1, max_files_number - subdir_files_number[subdir] + 1)
                copy_file(dapipath, dapi_filename_suffix)
            imp = IJ.openImage(dapipath)
            if not (imp.isStack() or imp.isHyperStack()):
                width, height = dimensionsOf(dapipath)
            # Upon finding the dapi image, initialize the VirtualStack
            if vs is None:
                vs = CreateVirtualStack(width, height, dirpath, params_background)
                hyperstack_path = os.path.join(outputDir, hyperstack_name + ext)
                # Save output
                if (not os.path.exists(hyperstack_path)) or force_save:
                    stack = ImagePlus(stack_name, vs)
                    number_channels = stack.getNSlices()
                    FileSaver(
                        HyperStackConverter.toHyperStack(stack, number_channels, params_hyperstack["number_frames"],
                                                         params_hyperstack["number_slices"],
                                                         params_hyperstack["order"],
                                                         params_hyperstack["color"])).saveAsTiff(hyperstack_path)
                IJ.log("Finished sucessfully")
    IJ.log("Run is finished")


run()
