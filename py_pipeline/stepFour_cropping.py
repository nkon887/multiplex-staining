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
    input_dir = config.stacksDir
    subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
    subfolders.pop(0)
    if not subfolders:
        print(input_dir + " is empty. Doing nothing")
    try:
        force_save = jt.ask_to_overwrite()
    except:
        # user canceled dialog
        return

    for subfolder in subfolders:
        tiff_files = []
        for tiff_file in os.listdir(subfolder):
            if not (config.cropped_suffix in os.path.basename(tiff_file) and tiff_file.endswith(
                    config.tiff_ext) or (config.error_subfolder_name in tiff_file) or (config.error_subfolder_name in
                                                                                       subfolder)) and os.path.isfile(
                                                                                    os.path.join(subfolder, tiff_file)):
                tiff_files.append(tiff_file)
        first_roi = []
        imps = []
        tiff_cropped_paths = []
        for tiff_file in tiff_files:
            print("Processing the tiff file " + tiff_file)
            tiff_cropped_path = os.path.join(subfolder,
                                             os.path.basename(tiff_file).split('.')[0] + config.cropped_suffix +
                                             config.tiff_ext).replace("\\", "/")
            tiff_cropped_paths.append(tiff_cropped_path)
            # Save output
            if (not os.path.exists(tiff_cropped_path)) or force_save:
                path = os.path.join(subfolder, tiff_file).replace("\\", "/")
                try:
                    width, height = jt.dimensions_of(path, input_dir, config.error_subfolder_name)
                    if [width, height]:
                        imp = IJ.openImage(path)
                        imps.append(imp)
                        if not (imp.isStack() or imp.isHyperStack()):
                            print("The input " + tiff_file + " is neither the Stack nor Hyperstack. Skipping")
                            continue
                except:
                    print(sys.exc_info())
                    continue
            else:
                print("The cropped tiff file " + tiff_cropped_path + " exists. Skipping")
        if imps:
            for imp in imps:
                imp.show()
                IJ.run(imp, "Enhance Contrast", "saturated=0.35")
                # ask the user to define a selection and get the bounds of the selection
                if not first_roi:
                    IJ.setTool(Toolbar.RECTANGLE)
                    WaitForUserDialog("Select the area using \"Rectangle\" as a form,then click OK.").show()
                    roi = imp.getRoi()
                    first_roi.append(roi)
                else:
                    imp.setRoi(first_roi[0])
            WaitForUserDialog("Adjust the area,then click OK.").show()
            for imp, tiff_cropped_path in zip(imps, tiff_cropped_paths):
                IJ.resetMinAndMax(imp)
                imp.changes = False
                roi = imp.getRoi()
                imp.setRoi(roi)
                stack = imp.getStack()
                cropped_stack = CroppedStack(stack, roi)
                for i in range(1, cropped_stack.size() + 1):
                    print(i)
                    # res_stack.addSlice(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
                    tempSlice = ImagePlus(stack.getSliceLabel(i), cropped_stack.getProcessor(i))
                    file_name_list = stack.getSliceLabel(i).split("_")
                    subfolder_path = os.path.join(subfolder, file_name_list[0] + "_" + file_name_list[1])
                    if not os.path.exists(subfolder_path):
                        os.mkdir(subfolder_path)
                    file_path = os.path.join(subfolder_path, stack.getSliceLabel(i)).replace("\\", "/")
                    if not os.path.exists(file_path) or force_save:
                        print(file_path)
                        FileSaver(tempSlice).saveAsTiff(file_path)
                imp.close()
    print("Run is finished")


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
