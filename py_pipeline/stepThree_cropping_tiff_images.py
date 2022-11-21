# @String param

import os
import sys

from ij import IJ, ImagePlus, VirtualStack, ImageStack
from ij.gui import GenericDialog
from ij.gui import WaitForUserDialog, Toolbar
from ij.io import FileSaver
from ij.plugin import HyperStackConverter

# sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config


def ask_for_parameters():
    gui = GenericDialog("Overwrite files?")
    gui.addMessage("Should the existing files be overwritten?")
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
        self.cur_stack = stack
        self.cur_region = roi

    def getProcessor(self, n):
        # Modify the same slice at index n every time it is requested
        ip = self.cur_stack.getProcessor(n)
        ip.setRoi(self.cur_region)
        return ip.crop()


def main():
    input_dir = ''
    if param == 'hyperstack':
        input_dir = config.hyperstacksDir
    elif param == 'alignedStack':
        input_dir = config.alignmentDir
    tiff_files = []
    for tiff_file in os.listdir(input_dir):
        if not ("_Cropped" in os.path.basename(tiff_file) and tiff_file.endswith(config.tiff_ext)):
            tiff_files.append(tiff_file)
    tiff_to_crop_path = os.path.join(input_dir, tiff_files[0])
    imp = IJ.openImage(tiff_to_crop_path)
    imp.show()
    try:
        force_save = ask_for_parameters()
    except:
        # user canceled dialog
        return
    # ask the user to define a selection and get the bounds of the selection
    IJ.setTool(Toolbar.RECTANGLE)
    WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
    roi = imp.getRoi()
    for tiff_file in tiff_files:
        IJ.log("Processing the tiff file " + tiff_file)
        tiff_cropped_path = os.path.join(input_dir,
                                         os.path.basename(tiff_file).split('.')[0] + "_Cropped" +
                                         config.tiff_ext).replace("\\", "/")
        # Save output
        if (not os.path.exists(tiff_cropped_path)) or force_save:
            if not tiff_file == tiff_files[0]:
                imp = IJ.openImage(os.path.join(input_dir, tiff_file))
                if not (imp.isStack() or imp.isHyperStack()):
                    IJ.log("The input" + tiff_file + "is not a Stack. Skipping")
                    continue
                imp.show()
                # ask the user to define a selection and get the bounds of the selection
                imp.setRoi(roi)
                WaitForUserDialog("Adjust the area,then click OK.").show()
                roi = imp.getRoi()
            imp.setRoi(roi)
            roi_width = int(roi.getFloatWidth())
            roi_height = int(roi.getFloatHeight())
            stack = imp.getStack()
            cropped_stack = CroppedStack(stack, roi)
            res_stack = ImageStack(roi_width, roi_height)
            for i in range(1, cropped_stack.size()+1):
                res_stack.addSlice(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
            cropped = ImagePlus("cropped", res_stack)
            # alternative:
            # cropped = imp.resize(int(roi.getFloatWidth()), int(roi.getFloatHeight()), 1, "bilinear")
            IJ.log("Saving the cropped hyperstack as " + tiff_cropped_path)
            if param == "hyperstack":
                FileSaver(HyperStackConverter.toHyperStack(cropped, cropped.getNSlices(), 1, 1, "xyczt(default)",
                                                           "Grayscale")).saveAsTiff(tiff_cropped_path)
            elif param == "alignedStack":
                FileSaver(cropped).saveAsTiff(tiff_cropped_path)
            imp.close()
        else:
            IJ.log("The cropped tiff file " + tiff_cropped_path + " exists. Skipping")
    IJ.log("Run is finished")


if __name__ in ['__builtin__', '__main__']:
    main()
