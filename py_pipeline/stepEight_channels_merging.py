import re
import sys
import os
import time
from java.lang import System
from ij.gui import GenericDialog
from ij import IJ, WindowManager
from ij.io import FileSaver

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/multiplex-staining/py_pipeline"))
import config
import pythontools as pt


def get_channels(subfolder, exc_channel):
    channels = []
    for subfolder_file in os.listdir(subfolder):
        filename = os.path.basename(subfolder_file)
        if filename.endswith(config.tiff_ext) and not (exc_channel in filename):
            channel = '_'.join(filename.split('.')[0].split('_')[2:])
            channels.append(channel)
    return sorted(list(set(channels)))


def getting_input_parameters(dapi_files, markers):
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
        params[config.dapi_str + subfolder] = gui.getNextChoice()
    for marker in markers:
        params[marker] = gui.getNextBoolean()
    force_save = gui.getNextBoolean()
    return params, force_save


def get_channel_files(subfolder, marker):
    channel_files = []
    for subfolder_file in os.listdir(subfolder):
        pattern = r'^\d{6}[^{\.}]*'
        if marker in os.path.basename(subfolder_file) and re.match(pattern + r'.tif', os.path.basename(subfolder_file)):
            channel_files.append(subfolder_file)
    return channel_files


def process(dapi_file, selected_channel_files, output_dir, force_save):
    for channel_file in selected_channel_files:
        print(str(channel_file))
        merged_filename = (os.path.basename(channel_file)).split(".")[0] + "_merged_dapi" + config.tiff_ext
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
            FileSaver(WindowManager.getCurrentImage()).saveAsTiff(merged_file_path)
    IJ.run("Close All")


def main():
    input_dir = config.contrastBgAdjustDir
    output_dir = config.mergeChannelsDir
    subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
    subfolders.pop(0)
    if not subfolders:
        print(input_dir + " is empty. Doing nothing")
        return
    selected_markers_dict, force_save_dict = {}, {}
    markers = []
    dapi_files_dict = {}

    for subfolder in subfolders:
        dapi_files = pt.dapi_tiff_image_filenames(subfolder, config.dapi_str, config.tiff_ext)
        dapi_files_dict[subfolder] = dapi_files
        markers = markers + get_channels(subfolder, config.dapi_str)
        if not dapi_files:
            print("Image file of dapi channel isn't found. Please check the filename and change  it if needed")
        if not markers:
            print("Channels could not be identified. Please check the filenames")
            return
    markers = list(set(markers))
    try:
        selected_markers, force_save = getting_input_parameters(dapi_files_dict, markers)
    except:
        print("Could get not the input parameters. Exiting")
        return

    for subfolder in subfolders:
        selected_channel_files = []
        for marker in markers:
            if selected_markers.get(marker) and marker != config.dapi_str + subfolder:
                selected_channel_files = selected_channel_files + get_channel_files(subfolder, marker)
        selected_dapi_image = selected_markers[config.dapi_str + subfolder]
        selected_dapi_image_path = os.path.join(subfolder, selected_dapi_image).replace("\\", "/")
        selected_channel_files_paths = []
        for selected_channel_file in selected_channel_files:
            selected_channel_files_paths.append(os.path.join(subfolder, selected_channel_file).replace("\\", "/"))
        process(selected_dapi_image_path, selected_channel_files_paths, output_dir, force_save)


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
    System.exit(0)
