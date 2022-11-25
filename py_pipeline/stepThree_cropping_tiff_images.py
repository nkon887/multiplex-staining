# @String param

import os
import sys
import time

from ij import IJ, ImagePlus, VirtualStack, ImageStack
from ij.gui import WaitForUserDialog, Toolbar
from ij.io import FileSaver
from ij.plugin import HyperStackConverter

from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import pythontools as pt
import config


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

    subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
    subfolders.pop(0)
    try:
        force_save = pt.ask_to_overwrite()
    except:
        # user canceled dialog
        return

    for subfolder in subfolders:
        tiff_files = []
        for tiff_file in os.listdir(subfolder):
            if not ("_Cropped" in os.path.basename(tiff_file) and tiff_file.endswith(config.tiff_ext)):
                tiff_files.append(tiff_file)
        tiff_to_crop_path = os.path.join(subfolder, tiff_files[0]).replace("\\", "/")
        IJ.log(tiff_to_crop_path)
        imp = IJ.openImage(tiff_to_crop_path)
        imp.show()

        # ask the user to define a selection and get the bounds of the selection
        IJ.setTool(Toolbar.RECTANGLE)
        WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
        roi = imp.getRoi()
        for tiff_file in tiff_files:
            IJ.log("Processing the tiff file " + tiff_file)
            tiff_cropped_path = os.path.join(subfolder,
                                             os.path.basename(tiff_file).split('.')[0] + "_Cropped" +
                                             config.tiff_ext).replace("\\", "/")
            # Save output
            if (not os.path.exists(tiff_cropped_path)) or force_save:
                if not tiff_file == tiff_files[0]:
                    imp = IJ.openImage(os.path.join(subfolder, tiff_file))
                    if not (imp.isStack() or imp.isHyperStack()):
                        IJ.log("The input" + tiff_file + "is not a Stack. Skipping")
                        continue
                    imp.show()
                    IJ.run(imp, "Enhance Contrast", "saturated=0.35")
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
                IJ.resetMinAndMax(imp)
                for i in range(1, cropped_stack.size() + 1):
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
    start_time = time.time()
    main()
    end_time = time.time()
    print("Duration of the program execution:")
    print(end_time - start_time)
    System.exit(0)
