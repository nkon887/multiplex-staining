# Walk recursively through an user-selected directory
# and for each subfolder add all found filenames that end with ".tif"
# to a VirtualStack, substract Background and generate Hyperstack
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


class CreateVirtualStack(VirtualStack):
    def __init__(self, width, height, sourceDir, params):
        # Tell the superclass to initialize itself with the sourceDir
        super(VirtualStack, self).__init__(width, height, None, sourceDir)
        # Store the parameters for the NormalizeLocalContrast
        self.params = params
        # Set all TIFF files in sourceDir as slices
        for filename in sorted(os.listdir(sourceDir)):
            if filename.lower().endswith(".tif") and not ("Stack.tif" or "Hyperstack.tif") in filename:
                self.addSlice(filename)

    def getProcessor(self, n):
        # Load the image at index n
        filepath = os.path.join(self.getDirectory(), self.getFileName(n))
        imp = IJ.openImage(filepath)
        if (imp.isStack() or imp.isHyperStack()):
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


def dapiTiffImageFilenames(directory):
    dapiTiffFiles = []
    files = os.listdir(directory)
    if not files == []:
        for filename in sorted(files):
            if (("dapi" or "DAPI") in filename) and (filename.lower().endswith(".tif")):
                dapiTiffFiles.append(filename)
    return dapiTiffFiles


def ask_to_proceed_with_overwrite():
    gd = GenericDialog("forceSave")
    gd.addCheckbox("forceSave", False)
    gd.showDialog()
    if gd.wasCanceled():
        IJ.log("User canceled dialog!")
        return
    forceSave = gd.getNextBoolean()
    return forceSave


def run():
    # A generator over all file paths in sourceDir
    srcDir = DirectoryChooser("Choose!").getDirectory()
    if not srcDir:
        # user canceled dialog
        return
    subdirs = [x[0] for x in os.walk(srcDir)]

    if not subdirs:
        return
    force_save = ask_to_proceed_with_overwrite()
    if force_save is None:
        force_save = False

    for subdir in subdirs:
        # Parameters for the Background substraction
        params = {
            "radius": 50.0,
            "createBackground": False,
            "lightBackground": False,
            "useParaboloid": False,
            "doPresmooth": False,
            "correctCorners": False
        }
        vs = None
        width, height = 0, 0
        dirpath = os.path.join(srcDir, subdir)
        dapifiles = dapiTiffImageFilenames(dirpath)
        if not dapifiles == []:
            dapipath = os.path.join(dirpath, dapifiles[0])
            IJ.log("Processing the subfolder " + os.path.dirname(dapipath))
            imp = IJ.openImage(dapipath)
            if not (imp.isStack() or imp.isHyperStack()):
                width, height = dimensionsOf(dapipath)
            # Upon finding the dapi image, initialize the VirtualStack
            if vs is None:
                vs = CreateVirtualStack(width, height, dirpath, params)
                stack_name = "Stack.tif"
                hyperstack_name = "Hyperstack.tif"
                stack_path = os.path.join(dirpath, stack_name)
                hyperstack_path = os.path.join(dirpath, hyperstack_name)
                # Save output
                if (not os.path.exists(stack_path)) or force_save:
                    stack = ImagePlus(stack_name, vs)
                    FileSaver(stack).saveAsTiff(stack_path)
                    number_channels = stack.getNSlices()
                    number_frames = 1
                    number_slices = 1
                    order = "xytzc"
                    color = "Grayscale"
                    FileSaver(
                        HyperStackConverter.toHyperStack(stack, number_channels, number_slices, number_frames,
                                                         order, color)).saveAsTiff(hyperstack_path)

    IJ.log("Finished sucessfully")


run()
# To Do: Step before: automate check of number of chan in each subfolder and get the max, add to other subs
#  copy of dapi chan if less then max
