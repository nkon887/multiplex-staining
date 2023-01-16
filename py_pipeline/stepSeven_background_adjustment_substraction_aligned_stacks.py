import os
import sys
import time

from ij import IJ, ImagePlus
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
import config
import pythontools as pt
import jythontools as jt


def get_list_of_indices(stack):
    filenames = []
    for sliceIndex in range(1, stack.getSize() + 1):
        filenames.append(stack.getSliceLabel(sliceIndex))
    markers = []
    exception = "copy"
    for filename in filenames:
        filename_list = filename.split("_")
        if exception not in filename:
            markers.append(filename_list.pop().split(".")[0])
        else:
            temp = filename_list.index(exception)
            markers.append(filename_list[temp - 1])
    markers = list(set(markers))
    marker_stack_indices_groups = {}
    for marker in markers:
        filenames_list = [filename for filename in filenames if marker in filename]
        filenames_list = list(set(filenames_list))
        slice_indices = []
        for filename in filenames_list:
            slice_indices = slice_indices + [i + 1 for i, x in enumerate(filenames) if x == filename]
        marker_stack_indices_groups[marker] = slice_indices

    return filenames, marker_stack_indices_groups


def get_keys_from_value(d, val):
    return [k for k, v in d.items() if v == val]


def ask_for_bg_parameters(markers):
    gui = GenericDialog("Background Parameter Settings")
    for marker in markers:
        gui.addMessage("Marker: " + marker)
        gui.addNumericField("Radius", 50, 0)  # 0 for no decimal part
        gui.addToSameRow()
        gui.addCheckbox("createBackground", False)
        gui.addToSameRow()
        gui.addCheckbox("lightBackground", False)
        gui.addToSameRow()
        gui.addCheckbox("useParaboloid", False)
        gui.addToSameRow()
        gui.addCheckbox("doPresmooth", False)
        gui.addToSameRow()
        gui.addCheckbox("correctCorners", False)
    gui.showDialog()

    if gui.wasCanceled():
        print("User canceled dialog! Doing nothing. Exit")
        return
    params = {}
    for marker in markers:
        params[marker] = {
            "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
            "createBackground": gui.getNextBoolean(),
            "lightBackground": gui.getNextBoolean(),
            "useParaboloid": gui.getNextBoolean(),
            "doPresmooth": gui.getNextBoolean(),
            "correctCorners": gui.getNextBoolean(),
        }
    return params


def main():
    input_dir = config.alignmentDir
    output_dir = config.contrastBgAdjustDir
    tiff_files = []
    subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
    subfolders.pop(0)
    for subfolder in subfolders:
        all_files = os.listdir(subfolder)
        if all_files:
            for tiff_file in os.listdir(subfolder):
                if "_Cropped" in os.path.basename(tiff_file) and tiff_file.endswith(config.tiff_ext):
                    tiff_files.append(tiff_file)
            # Subtract background
            bs = BackgroundSubtracter()
            markers = []
            imp = IJ.openImage(os.path.join(subfolder, (next(iter(tiff_files)))))
            imp.show()
            imp.changes = False
            stack = imp.getStack()
            _, markerslice_groups = get_list_of_indices(stack)
            imp.close()
            markers = list(set(markerslice_groups.keys()))
            try:
                params_bg = ask_for_bg_parameters(markers)
                force_save = jt.ask_to_overwrite()
            except:
                print("user canceled dialog. Exit")
                return

            for tiff_file in tiff_files:
                print("Processing the file " + str(tiff_file))
                imp = IJ.openImage(os.path.join(subfolder, tiff_file))
                imp.show()
                imp.changes = False
                stack = imp.getStack()
                filenames, markerslice_groups = get_list_of_indices(stack)
                for sliceIndex in range(1, stack.getSize() + 1):
                    filename = str(stack.getSliceLabel(sliceIndex)).split(".")[0]
                    print("Saving the slice " + str(sliceIndex) + " " + str(stack.getSliceLabel(sliceIndex)))
                    # Save output
                    ip = stack.getProcessor(sliceIndex)
                    slice_file_name_three = ''
                    slice_file_name_four = ''
                    marker = ''
                    subfolder_name = os.path.basename(tiff_file).split('.')[0].split("_")[0]
                    subfolder_path = os.path.join(output_dir, subfolder_name).replace("\\", "/")
                    if not os.path.exists(subfolder_path):
                        os.mkdir(subfolder_path)
                    for marker in markerslice_groups.keys():
                        if sliceIndex in ["_" + x + config.tiff_ext for x in markerslice_groups.get(marker)]:
                            print("Slice " + str(sliceIndex) + " is in " + str(marker))
                            slice_file_name_three = os.path.join(subfolder_path,
                                                                 filename + "_no_background_sub"
                                                                 + ".tif").replace("\\", "/")
                            slice_file_name_four = os.path.join(subfolder_path,
                                                                filename + "_background_sub"
                                                                + ".tif").replace("\\", "/")
                            # Save output
                            if (not os.path.exists(slice_file_name_three)) or force_save:
                                temp = ImagePlus(str(sliceIndex), ip)
                                IJ.run(temp, "8-bit", "")
                                FileSaver(temp).saveAsTiff(slice_file_name_three)
                            else:
                                print(slice_file_name_three + " exists. Doing nothing. Skipping")
                            if (not os.path.exists(slice_file_name_four)) or force_save:
                                bs.rollingBallBackground(ip, params_bg[marker]["radius"],
                                                         params_bg[marker]["createBackground"],
                                                         params_bg[marker]["lightBackground"],
                                                         params_bg[marker]["useParaboloid"],
                                                         params_bg[marker]["doPresmooth"],
                                                         params_bg[marker]["correctCorners"])
                                temp = ImagePlus(str(sliceIndex), ip)
                                IJ.run(temp, "8-bit", "")
                                FileSaver(temp).saveAsTiff(slice_file_name_four)
                            else:
                                print(slice_file_name_four + " exists. Doing nothing. Skipping")
                imp.close()
            IJ.run("Close All")
        else:
            print(subfolder + " is empty. Doing nothing")
        print("Run is finished")


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("Duration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
