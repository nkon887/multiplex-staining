import os
import sys

from ij import IJ, ImagePlus
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin.filter import BackgroundSubtracter

sys.path.append(os.path.abspath(os.getcwd()))
import jythontools as jt


class BackgroundAdjustment:
    def __init__(self, input_dir, output_dir, tiff_ext):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tiff_ext = tiff_ext

    def get_list_of_indices(self, stack):
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
            filenames_list = [filename for filename in filenames if "_" + marker + self.tiff_ext in filename]
            filenames_list = list(set(filenames_list))
            slice_indices = []
            for filename in filenames_list:
                slice_indices = slice_indices + [i + 1 for i, x in enumerate(filenames) if x == filename]
            marker_stack_indices_groups[marker] = slice_indices

        return filenames, marker_stack_indices_groups

    def get_keys_from_value(self, d, val):
        return [k for k, v in d.items() if v == val]

    def ask_for_bg_parameters(self, markers):
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

    def processing(self):
        input_dir = self.input_dir
        output_dir = self.output_dir
        tiff_files = []
        all_files = os.listdir(input_dir)
        if all_files:
            for tiff_file in all_files:
                if not (os.path.isdir(tiff_file)) and "_Cropped" in os.path.basename(tiff_file) and \
                        tiff_file.endswith(self.tiff_ext):
                    tiff_files.append(tiff_file)
            # Subtract background
            bs = BackgroundSubtracter()
            markers = []
            imp = IJ.openImage(os.path.join(input_dir, (next(iter(tiff_files)))))
            imp.show()
            imp.changes = False
            stack = imp.getStack()
            _, markerslice_groups = self.get_list_of_indices(stack)
            imp.close()
            markers = list(set(markerslice_groups.keys()))
            try:
                params_bg = self.ask_for_bg_parameters(markers)
            except:
                print("user canceled dialog. Exit")
                return
            force_save = jt.ask_to_overwrite()
            if force_save is None:
                # user canceled dialog
                return

            for tiff_file in tiff_files:
                print("Processing the file " + str(tiff_file))
                imp = IJ.openImage(os.path.join(input_dir, tiff_file))
                imp.show()
                imp.changes = False
                stack = imp.getStack()
                filenames, markerslice_groups = self.get_list_of_indices(stack)
                for sliceIndex in range(1, stack.getSize() + 1):
                    filename = str(stack.getSliceLabel(sliceIndex)).split(".")[0]
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
                        if sliceIndex in [x for x in markerslice_groups.get(marker)]:
                            print("Saving the slice " + str(sliceIndex) + " " + str(stack.getSliceLabel(sliceIndex)))
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
            print(input_dir + " is empty. Doing nothing")
        print("Run is finished")
