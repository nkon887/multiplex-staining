import os
import sys
import time

from ij import IJ
from ij.gui import GenericDialog
from ij.plugin import HyperStackConverter
from java.lang import System

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/multiplex-staining/py_pipeline"))
import config


def alignment(imp, title, path, alignment_type, channels, force_save):
    IJ.log("Processing the file " + title)
    if alignment_type == ("Rigid Body" or "Scaled Rotation"):
        alignment_type = "[" + alignment_type + "]"
    channels_list = [key.lower() for key, v in channels.items() if v is True]
    channel_str = ' '.join(channels_list)
    IJ.run(imp, "HyperStackReg ", "transformation=" + ' '.join([alignment_type, channel_str]))
    HyperStackConverter.toStack(imp)
    IJ.saveAs(imp, "Tiff", path)


def create_gui(experiment_id, channels_number):
    gui = GenericDialog("Alignment: Input parameters")
    gui.addMessage("Choose the type of alignment for the experiment " + experiment_id)
    gui.addChoice("Alignment type", ["Affine", "Rigid Body", "Translation", "Scaled Rotation"],
                  "Rigid Body")  # rigidBody is default here
    gui.addMessage("Choose the channels")
    for i in range(channels_number):
        gui.addCheckbox("Channel" + str(i + 1), False)
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    alignment_type = gui.getNextChoice()
    channels = {}
    for i in range(channels_number):
        channels["Channel" + str(i + 1)] = gui.getNextBoolean()
    force_save = gui.getNextBoolean()
    return [alignment_type, channels, force_save]


def getting_parameters():
    hs_dir = config.concatenatesDir
    params = {}
    for hs in os.listdir(hs_dir):
        if hs.endswith(config.tiff_ext):
            hs_to_align_path = os.path.join(hs_dir, hs)
            imp = IJ.openImage(hs_to_align_path)
            channel_no = imp.getNChannels()
            try:
                alignment_type, channels, force_save = create_gui(hs.split(".")[0], channel_no)
                params[hs] = [alignment_type, channels, force_save]
            except:
                # pass
                # user canceled dialog
                return
    return params


def main():
    hs_dir = config.concatenatesDir
    out_dir = config.alignmentDir
    params = getting_parameters()
    for hs in os.listdir(hs_dir):
        if hs.endswith(config.tiff_ext):
            hs_to_align_path = os.path.join(hs_dir, hs)
            imp = IJ.openImage(hs_to_align_path)
            alignment_subfolder_path = os.path.join(out_dir, params.get(hs)[0].replace(" ", "_"))
            if not os.path.exists(alignment_subfolder_path):
                os.mkdir(alignment_subfolder_path)
            alignment_path = os.path.join(alignment_subfolder_path, hs.split(".")[0] +
                                          config.tiff_ext).replace("\\", "/")
            if (not os.path.exists(alignment_path)) or params.get(hs)[2]:
                alignment(imp, hs.split(".")[0], alignment_path, params.get(hs)[0], params.get(hs)[1],
                          params.get(hs)[2])
            else:
                IJ.log("The file already exists.Skipping")
            IJ.run("Close All")
        else:
            IJ.log("No files found in the subfolder \"concatenates\". Skipping")
    IJ.log("Run is finished")


if __name__ in ['__builtin__', '__main__']:
    start_time = time.time()
    main()
    end_time = time.time()
    print("Duration of the program execution:", )
    print(end_time - start_time)
    System.exit(0)
