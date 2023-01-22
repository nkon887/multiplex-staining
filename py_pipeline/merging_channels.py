import re
import sys
import os
import time
from java.lang import System
from ij.gui import GenericDialog
from ij import IJ, WindowManager
from ij.io import FileSaver

sys.path.append(os.path.abspath(os.getcwd()))
import config
import pythontools as pt


class MergingChannels:
    def __init__(self, input_dir, output_dir, tiff_ext, dapi_str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str

    def get_channels(self, subfolder, exc_channel):
        channels = []
        for subfolder_file in os.listdir(subfolder):
            filename = os.path.basename(subfolder_file)
            if filename.endswith(self.tiff_ext) and not (exc_channel in filename):
                channel = '_'.join(filename.split('.')[0].split('_')[2:])
                channels.append(channel)
        return sorted(list(set(channels)))

    def getting_input_parameters(self, dapi_files, markers):
        gui = GenericDialog("Channels")
        gui.addMessage("Choose dapi image  you want to use for merge")
        for subfolder, i in zip(dapi_files.keys(), range(0, len(dapi_files.keys()))):
            dapis = dapi_files.get(subfolder)
            gui.addChoice("patient " + os.path.basename(subfolder) + ":", dapis, dapis[2])  # dapis[2] is default here
            if i % 2 == 0:
                gui.addToSameRow()
        gui.addMessage("Choose images of channels you want to combine with dapi image")
        for marker, i in zip(markers, range(0, len(markers))):
            gui.addCheckbox(marker, False)
            if i % 2 == 0:
                gui.addToSameRow()
        gui.addMessage("Overwrite option")
        gui.addCheckbox("forceSave", False)
        gui.showDialog()

        if gui.wasCanceled():
            print("User canceled dialog! Doing nothing. Exit")
            return
        params = {}
        for subfolder in dapi_files.keys():
            params[self.dapi_str + subfolder] = gui.getNextChoice()
        for marker in markers:
            params[marker] = gui.getNextBoolean()
        force_save = gui.getNextBoolean()
        return params, force_save

    def get_channel_files(self, subfolder, marker):
        channel_files = []
        for subfolder_file in os.listdir(subfolder):
            pattern = r'^\d{6}[^{\.}]*'
            if marker in os.path.basename(subfolder_file) and re.match(pattern + self.tiff_ext,
                                                                       os.path.basename(subfolder_file)):
                channel_files.append(subfolder_file)
        return channel_files

    def merging(self, dapi_file, selected_channel_files, output_dir, force_save):
        for channel_file in selected_channel_files:
            print(str(channel_file))
            merged_filename = (os.path.basename(channel_file)).split(".")[0] + "_merged_dapi" + self.tiff_ext
            imp1 = IJ.openImage(dapi_file)
            imp1.show()
            imp2 = IJ.openImage(channel_file)
            imp2.show()
            IJ.run(imp1, "Merge Channels...",
                   "c1=" + os.path.basename(channel_file) + " c3=" + os.path.basename(dapi_file) + " keep")
            imp1.close()
            imp2.close()
            subfolder_folder_path = os.path.join(output_dir, os.path.basename(channel_file).split("_")[1])
            if not os.path.exists(subfolder_folder_path):
                os.mkdir(subfolder_folder_path)
            merged_file_path = os.path.join(subfolder_folder_path, merged_filename)
            print("Saving the " + str(merged_file_path))
            if (not os.path.exists(merged_file_path)) or force_save:
                res = WindowManager.getCurrentImage()
                FileSaver(res).saveAsTiff(merged_file_path)
                res.close()
        IJ.run("Close All")

    def processing(self):
        input_dir = self.input_dir
        output_dir = self.output_dir
        subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
        subfolders.pop(0)
        if not subfolders:
            print(input_dir + " is empty. Doing nothing")
            return
        markers = []
        dapi_files_dict = {}

        for subfolder in subfolders:
            dapi_files = pt.dapi_tiff_image_filenames(subfolder, self.dapi_str, self.tiff_ext)
            dapi_files_dict[subfolder] = dapi_files
            markers = markers + self.get_channels(subfolder, self.dapi_str)
            if not dapi_files:
                print("Image file of dapi channel isn't found. Please check the filename and change  it if needed")
            if not markers:
                print("Channels could not be identified. Please check the filenames")
                return
        markers = list(set(markers))
        try:
            selected_markers, force_save = self.getting_input_parameters(dapi_files_dict, markers)
        except:
            print("Could get not the input parameters. Exiting")
            return

        for subfolder in subfolders:
            selected_channel_files = []
            for marker in markers:
                if selected_markers.get(marker) and marker != self.dapi_str + subfolder:
                    selected_channel_files = selected_channel_files + self.get_channel_files(subfolder,
                                                                                                         marker)
            selected_dapi_image = selected_markers[self.dapi_str + subfolder]
            selected_dapi_image_path = os.path.join(subfolder, selected_dapi_image).replace("\\", "/")
            selected_channel_files_paths = []
            for selected_channel_file in selected_channel_files:
                selected_channel_files_paths.append(
                    os.path.join(subfolder, selected_channel_file).replace("\\", "/"))
            self.merging(selected_dapi_image_path, selected_channel_files_paths, output_dir, force_save)


def main():
    MergingChannels(config.bg_adjust_dir, config.merge_channels_dir, config.tiff_ext, config.dapi_str).processing()


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
