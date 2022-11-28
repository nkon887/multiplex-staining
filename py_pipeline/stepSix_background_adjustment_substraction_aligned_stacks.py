import os
import sys
import time

from ij import IJ, ImagePlus
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter
from java.lang import System
from mpicbg.ij.plugin import NormalizeLocalContrast

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/multiplex-staining/py_pipeline"))
import config


def execute_filter(ip, params):
    """ Given an ImageProcessor ip and a dictionary of parameters, filter the ip,
      and return the same or a new ImageProcessor of the same dimensions and type. """
    block_radius_x = params["blockRadiusX"]
    block_radius_y = params["blockRadiusY"]
    stds = params["stds"]
    center = params["center"]
    stretch = params["stretch"]
    NormalizeLocalContrast.run(ip, block_radius_x, block_radius_y, stds, center, stretch)
    return ip


def get_list_of_indices(stack):
    filenames = []
    for sliceIndex in range(1, stack.getSize() + 1):
        filenames.append(stack.getSliceLabel(sliceIndex))
    markers = []
    exception = "copy"
    for filename in filenames:
        filename_list = filename.split("_")
        # IJ.log(str(filename))
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
        IJ.log(str(marker))
        IJ.log(str(slice_indices))

    return filenames, marker_stack_indices_groups


def get_keys_from_value(d, val):
    return [k for k, v in d.items() if v == val]


def ask_for_parameters(marker):
    gui = GenericDialog("Parameter settings")

    gui.addMessage("Background Parameters")
    gui.addMessage("Marker: " + marker)
    gui.addNumericField("Radius", 50, 0)  # 0 for no decimal part
    gui.addCheckbox("createBackground", False)
    gui.addCheckbox("lightBackground", False)
    gui.addCheckbox("useParaboloid", False)
    gui.addCheckbox("doPresmooth", False)
    gui.addCheckbox("correctCorners", False)

    gui.addMessage("Contrast Parameters")
    gui.addCheckbox("General Enhance Contrast", False)
    gui.addCheckbox("Adjust Contrast", False)
    gui.addNumericField("Block Radius X", 20)
    gui.addNumericField("Block Radius Y", 20)
    gui.addNumericField("stds", 2, 0)
    gui.addCheckbox("center", False)
    gui.addCheckbox("stretch", False)

    gui.addMessage("Overwrite option")
    gui.addCheckbox("forceSave", False)

    gui.showDialog()

    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    params = {
        "radius": gui.getNextNumber(),  # This always return a double (ie might need to cast to int)
        "createBackground": gui.getNextBoolean(),
        "lightBackground": gui.getNextBoolean(),
        "useParaboloid": gui.getNextBoolean(),
        "doPresmooth": gui.getNextBoolean(),
        "correctCorners": gui.getNextBoolean(),
        "enhanceContrast": gui.getNextBoolean(),
        "adjustContrast": gui.getNextBoolean(),
        "blockRadiusX": int(gui.getNextNumber()),
        "blockRadiusY": int(gui.getNextNumber()),
        "stds": int(gui.getNextNumber()),
        "center": gui.getNextBoolean(),
        "stretch": gui.getNextBoolean(),
        "forceSave": gui.getNextBoolean()
    }
    return params


def main():
    input_dir = config.alignmentDir
    output_dir = config.contrastBgAdjustDir
    tiff_files = []
    subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
    subfolders.pop(0)
    for subfolder in subfolders:
        for tiff_file in os.listdir(subfolder):
            if "_Cropped" in os.path.basename(tiff_file) and tiff_file.endswith(config.tiff_ext):
                tiff_files.append(tiff_file)
        # Subtract background
        bs = BackgroundSubtracter()

        for tiff_file in tiff_files:
            IJ.log(str(tiff_file))
            imp = IJ.openImage(os.path.join(subfolder, tiff_file))
            imp.show()
            imp.changes = False
            stack = imp.getStack()
            filenames, markerslice_groups = get_list_of_indices(stack)
            params = {}
            for marker in markerslice_groups.keys():
                try:
                    params[marker] = ask_for_parameters(marker)
                except:
                    IJ.log("user canceled dialog. Exit")
                    return
            for sliceIndex in range(1, stack.getSize() + 1):
                filename = str(stack.getSliceLabel(sliceIndex)).split(".")[0]
                IJ.log("Processing slice " + str(sliceIndex) + " " + str(stack.getSliceLabel(sliceIndex)))
                # Save output
                ip = stack.getProcessor(sliceIndex)
                slice_file_name_one = ''
                slice_file_name_two = ''
                slice_file_name_three = ''
                slice_file_name_four = ''
                marker_params = {}
                marker = ''
                subfolder_name = os.path.basename(tiff_file).split('.')[0].split("_")[0]
                subfolder_path = os.path.join(output_dir, subfolder_name).replace("\\", "/")
                if not os.path.exists(subfolder_path):
                    os.mkdir(subfolder_path)
                for marker in markerslice_groups.keys():
                    if sliceIndex in markerslice_groups.get(marker):
                        IJ.log("Slice " + str(sliceIndex) + " is in " + str(marker))
                        slice_file_name_one = os.path.join(subfolder_path,
                                                           filename + "_auto_contrast_no_bg_sub"
                                                           + ".tif").replace("\\", "/")
                        slice_file_name_two = os.path.join(subfolder_path,
                                                           filename + "_auto_contrast_bg_sub_"
                                                           + ".tif").replace("\\", "/")
                        slice_file_name_three = os.path.join(subfolder_path,
                                                             filename + "_no_contrast_no_bg_sub_"
                                                             + ".tif").replace("\\", "/")
                        slice_file_name_four = os.path.join(subfolder_path,
                                                            filename + "_no_contrast_bg_sub_"
                                                            + ".tif").replace("\\", "/")
                        marker_params = params[marker]
                # Save output
                if (not os.path.exists(slice_file_name_one)) or marker_params["forceSave"]:
                    if marker_params["adjustContrast"]:
                        IJ.log("Contrast Adjustment")
                        try:
                            ip = execute_filter(ip, params[marker])
                        # Fail-safe execution of the filter, which is a global function name
                        except:
                            print(sys.exc_info())
                        temp = ImagePlus(str(sliceIndex), ip)
                        if marker_params["enhanceContrast"]:
                            IJ.run(temp, "Enhance Contrast...", "saturated=0.35 normalize")
                        IJ.run(temp, "8-bit", "")
                        IJ.run(temp, "Make Binary", "method=Default background=Default calculate black")
                        FileSaver(temp).saveAsTiff(slice_file_name_one)
                        if (not os.path.exists(slice_file_name_two)) or marker_params["forceSave"]:
                            bs.rollingBallBackground(ip, marker_params["radius"], marker_params["createBackground"],
                                                     marker_params["lightBackground"], marker_params["useParaboloid"],
                                                     marker_params["doPresmooth"], marker_params["correctCorners"])
                            temp = ImagePlus(str(sliceIndex), ip)
                            if marker_params["enhanceContrast"]:
                                IJ.run(temp, "Enhance Contrast...", "saturated=0.35 normalize")
                            IJ.run(temp, "8-bit", "")
                            IJ.run(temp, "Make Binary", "method=Default background=Default calculate black")
                            FileSaver(temp).saveAsTiff(slice_file_name_two)
                        else:
                            IJ.log(slice_file_name_two + " exists. Doing nothing. Skipping")
                    else:
                        if (not os.path.exists(slice_file_name_three)) or params[marker]["forceSave"]:
                            temp = ImagePlus(str(sliceIndex), ip)
                            if marker_params["enhanceContrast"]:
                                IJ.run(temp, "Enhance Contrast...", "saturated=0.35 normalize")
                            IJ.run(temp, "8-bit", "")
                            IJ.run(temp, "Make Binary", "method=Default background=Default calculate black")
                            FileSaver(temp).saveAsTiff(slice_file_name_three)
                        else:
                            IJ.log(slice_file_name_three + " exists. Doing nothing. Skipping")
                        if (not os.path.exists(slice_file_name_four)) or params[marker]["forceSave"]:
                            bs.rollingBallBackground(ip, marker_params["radius"], marker_params["createBackground"],
                                                     marker_params["lightBackground"], marker_params["useParaboloid"],
                                                     marker_params["doPresmooth"], marker_params["correctCorners"])
                            temp = ImagePlus(str(sliceIndex), ip)
                            if marker_params["enhanceContrast"]:
                                IJ.run(temp, "Enhance Contrast...", "saturated=0.35 normalize")
                            IJ.run(temp, "8-bit", "")
                            IJ.run(temp, "Make Binary", "method=Default background=Default calculate black")
                            FileSaver(temp).saveAsTiff(slice_file_name_four)
                        else:
                            IJ.log(slice_file_name_four + " exists. Doing nothing. Skipping")
                else:
                    IJ.log(slice_file_name_two + " exists. Doing nothing. Skipping")

            imp.close()
        IJ.log("Run is finished")
        IJ.run("Close All")


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("Duration of the program execution:", )
    print(end_time - start_time)
    System.exit(0)
