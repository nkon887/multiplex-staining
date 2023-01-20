import os
import sys
import time

from ij import IJ, ImagePlus, VirtualStack, ImageStack
from ij.gui import WaitForUserDialog, Toolbar
from ij.io import FileSaver
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import jythontools as jt
import pythontools as pt
import config


class CroppingAlignedStacks:
    def __init__(self, alignment_dir, cropped_suffix, tiff_ext, error_subfolder_name):
        self.input_dir = alignment_dir
        self.cropped_suffix = cropped_suffix
        self.tiff_ext = tiff_ext
        self.error_subfolder_name = error_subfolder_name

    def processing(self):
        subfolders = [x[0].replace("\\", "/") for x in os.walk(self.input_dir)]
        subfolders.pop(0)
        force_save = jt.ask_to_overwrite()
        if not force_save:
            # user canceled dialog
            return
        for subfolder in subfolders:
            tiff_files = []
            subfolder_files = os.listdir(subfolder)
            if subfolder_files:
                for tiff_file in os.listdir(subfolder):
                    if not (self.cropped_suffix in os.path.basename(tiff_file) and tiff_file.endswith(
                            self.tiff_ext) or (self.error_subfolder_name in tiff_file) or (
                                    self.error_subfolder_name in
                                    subfolder)):
                        tiff_files.append(tiff_file)
                for tiff_file in tiff_files:
                    print("Processing the tiff file " + tiff_file)
                    tiff_cropped_path = os.path.join(subfolder,
                                                     os.path.basename(tiff_file).split('.')[0] + self.cropped_suffix +
                                                     self.tiff_ext).replace("\\", "/")
                    # Save output
                    if (not os.path.exists(tiff_cropped_path)) or force_save:
                        path = os.path.join(subfolder, tiff_file).replace("\\", "/")
                        try:
                            width, height = jt.dimensions_of(path, self.input_dir, self.error_subfolder_name)
                            if [width, height]:
                                imp = IJ.openImage(path)
                                if not (imp.isStack() or imp.isHyperStack()):
                                    print("The input " + tiff_file + " is neither the Stack nor Hyperstack. Skipping")
                                    continue
                        except:
                            print(sys.exc_info())
                            continue
                        imp.show()
                        # ask the user to define a selection and get the bounds of the selection
                        IJ.setTool(Toolbar.RECTANGLE)
                        WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
                        roi = imp.getRoi()
                        imp.setRoi(roi)
                        roi_width = int(roi.getFloatWidth())
                        roi_height = int(roi.getFloatHeight())
                        stack = imp.getStack()
                        cropped_stack = CroppedStack(stack, roi)
                        res_stack = ImageStack(roi_width, roi_height)
                        for i in range(1, cropped_stack.size() + 1):
                            res_stack.addSlice(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
                        cropped = ImagePlus("cropped", res_stack)
                        # alternative:
                        # cropped = imp.resize(int(roi_width), int(roi_height), 1, "bilinear")
                        print("Saving the cropped hyperstack as " + tiff_cropped_path)
                        FileSaver(cropped).saveAsTiff(tiff_cropped_path)
                        imp.close()

                    else:
                        print("The cropped tiff file " + tiff_cropped_path + " exists. Skipping")
            else:
                print(subfolder + " is empty. Doing nothing")
            print("Run is finished")


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
    CroppingAlignedStacks(config.alignment_dir, config.cropped_suffix, config.tiff_ext,
                          config.error_subfolder_name).processing()


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
