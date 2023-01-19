import os
import sys
import time

from ij import IJ, ImagePlus, VirtualStack, ImageStack
from ij.gui import WaitForUserDialog, Toolbar
from ij.io import FileSaver
from ij.plugin import HyperStackConverter
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/multiplex-staining/py_pipeline"))
import pythontools as pt
import jythontools as jt
import config


class CroppingForAlignment:
    def __init__(self, input_dir, target_dir, error_subfolder_name, tiff_ext):
        self.input_dir = input_dir
        self.target_dir = target_dir
        self.error_subfolder_name = error_subfolder_name
        self.tiff_ext = tiff_ext

    def processing(self):
        subfolders = [x[0].replace("\\", "/") for x in os.walk(self.input_dir)]
        subfolders.pop(0)
        if not subfolders:
            print(self.input_dir + " is empty. Doing nothing")
        force_save = jt.ask_to_overwrite()
        if not force_save:
            # user canceled dialog
            return

        for subfolder in subfolders:
            tiff_files = []
            for tiff_file in os.listdir(subfolder):
                if not (tiff_file.endswith(self.tiff_ext) or (self.error_subfolder_name in tiff_file) or
                   (self.error_subfolder_name in subfolder)) and os.path.isfile(os.path.join(subfolder, tiff_file)):
                    tiff_files.append(tiff_file)
            first_roi = []
            imps = []
            tiff_cropped_paths = []
            for tiff_file in tiff_files:
                print("Processing the tiff file " + tiff_file)
                imp = IJ.openImage(os.path.join(subfolder, tiff_file))
                stack = imp.getStack()
                for i in range(1, stack.size() + 1):
                    tiff_cropped_path = os.path.join(self.target_dir, os.path.basename(tiff_file).split('.')[0],
                                                     stack.getSliceLabel(i)).replace("\\", "/")
                    tiff_cropped_paths.append(tiff_cropped_path)
                # Save output
                if (not all(os.path.exists(tiff_cropped_path) for tiff_cropped_path in tiff_cropped_paths)) or force_save:
                    path = os.path.join(subfolder, tiff_file).replace("\\", "/")
                    try:
                        width, height = jt.dimensions_of(path, self.input_dir, self.error_subfolder_name)
                        if [width, height] and imp not in imps:
                            imps.append(imp)
                            if not (imp.isStack() or imp.isHyperStack()):
                                print("The input " + tiff_file + " is neither the Stack nor Hyperstack. Skipping")
                                continue
                    except:
                        print(sys.exc_info())
                        continue
                else:
                    imp.close()
                    print("The cropped tiff files of " + subfolder + " exists. Skipping")

            if imps:
                for imp in imps:
                    imp.show()
                    # ask the user to define a selection and get the bounds of the selection
                    if not first_roi:
                        IJ.setTool(Toolbar.RECTANGLE)
                        WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
                        roi = imp.getRoi()
                        first_roi.append(roi)
                    else:
                        imp.setRoi(first_roi[0])
                WaitForUserDialog("Adjust the area,then click OK.").show()
                j = 0
                for imp in imps:
                    imp.changes = False
                    roi = imp.getRoi()
                    imp.setRoi(roi)
                    stack = imp.getStack()
                    cropped_stack = CroppedStack(stack, roi)
                    for i in range(1, cropped_stack.size() + 1):
                        print(i)
                        tempSlice = ImagePlus(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
                        if not os.path.exists(os.path.dirname(tiff_cropped_paths[j])):
                            os.mkdir(os.path.dirname(tiff_cropped_paths[j]))
                        file_path = tiff_cropped_paths[j].replace("\\", "/")
                        if not os.path.exists(file_path) or force_save:
                            print(file_path)
                            FileSaver(tempSlice).saveAsTiff(file_path)
                        j += 1
                    imp.close()
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
    cropping = CroppingForAlignment(config.stacks_dir, config.cropped_stacks_dir, config.error_subfolder_name,
                                    config.tiff_ext)


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
