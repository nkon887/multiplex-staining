import getopt
import os
import sys

from ij import IJ, ImagePlus, VirtualStack
from ij.gui import GenericDialog
from ij.gui import WaitForUserDialog, Toolbar
from ij.io import FileSaver
from ij.plugin import HyperStackConverter
from ij.plugin.frame import RoiManager

# sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config


def ask_for_parameters():
    gui = GenericDialog("Overwrite files?")
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    force_save = gui.getNextBoolean()
    return force_save


class CroppedStack(VirtualStack):
    def __init__(self, stack, roi):
        # Constructor: tell the superclass VirtualStack about the dimensions
        super(VirtualStack, self).__init__(stack.getWidth(), stack.getHeight(), stack.size())
        self.stack = stack
        self.region = roi

    def getProcessor(self, n):
        # Modify the same slice at index n every time it is requested
        ip = self.stack.getProcessor(n)
        ip.setRoi(self.region)
        return ip.crop()


def main(argv):
    tiff_ext = ".tif"
    inputfolder = ''
    try:
        opts, args = getopt.getopt(argv, "hi:", ["ifolder="])
    except getopt.GetoptError:
        print
        'stepThree_cropping_tiff_images.py -i <inputfolder>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print
            'stepThree_cropping_tiff_images.py -i <inputfolder>'
            sys.exit()
        elif opt in ("-i", "--ifolder"):
            inputfolder = arg
    if inputfolder == "hyperstack":
        input_dir = config.hyperstacksDir
    elif inputfolder == "aligned stack":
        input_dir = config.alignmentDir
    tiff_files = []
    for tiff_file in os.listdir(input_dir):
        if not ("_Cropped" in os.path.basename(tiff_file) and tiff_file.endwith(tiff_ext)):
            tiff_files.append(tiff_file)
    # IJ.log(input_dir)
    tiff_to_crop_path = os.path.join(input_dir, tiff_files[0])
    imp = IJ.openImage(tiff_to_crop_path)
    imp.show()
    # imp = IJ.getImage()
    stack = imp.getStack()
    try:
        force_save = ask_for_parameters()
    except:
        # user canceled dialog
        return
    # remove all the previous ROIS
    rm = RoiManager.getInstance()
    if not rm:
        rm = RoiManager()
        rm.runCommand("reset")
    # ask the user to define a selection and get the bounds of the selection
    IJ.setTool(Toolbar.RECTANGLE)
    WaitForUserDialog("Select the area,then click OK.").show()
    roi = imp.getRoi()
    imp.setRoi(roi)
    rm.addRoi(roi)
    rois = rm.getRoisAsArray()  # this is a list of rois (only 1 as it got cleared
    for tiff_file in tiff_files:
        tiff_cropped_path = os.path.join(input_dir,
                                         os.path.basename(tiff_file).split('.')[0] + "_Cropped" + tiff_ext).replace(
            "\\", "/")
        # Save output
        if (not os.path.exists(tiff_cropped_path)) or force_save:
            if not tiff_file == tiff_files[0]:
                imp = IJ.openImage(os.path.join(config.hyperstacksDir, tiff_file))
                IJ.log(str(imp.isStack()))
                if not (imp.isStack() or imp.isHyperStack()):
                    IJ.log("The input" + tiff_file + "is not a Stack. Skipping")
                    continue
                imp.show()
                stack = imp.getStack()
                # ask the user to define a selection and get the bounds of the selection
                imp.setRoi(rois[0])
                WaitForUserDialog("Adjust the area,then click OK.").show()
                roi = imp.getRoi()
                imp.setRoi(roi)
                rm.addRoi(roi)
            cropped = ImagePlus("cropped", CroppedStack(stack, roi))
            # cropped.show()
            imp.close()
            if inputfolder == "hyperstack":
                FileSaver(HyperStackConverter.toHyperStack(cropped, cropped.getNSlices(), 1, 1, "xyczt(default)",
                                                           "Grayscale")).saveAsTiff(tiff_cropped_path)
            elif inputfolder == "aligned stack":
                FileSaver(cropped).saveAsTiff(tiff_cropped_path)
        else:
            IJ.log("The cropped tiff file " + tiff_cropped_path + " exists. Skipping")
    rm.close()


if __name__ in ['__builtin__', '__main__']:
    main(sys.argv[1:])
