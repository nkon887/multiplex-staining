import os
import sys
from ij import IJ
from ij.gui import GenericDialog
from ij.plugin import HyperStackConverter

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config


def alignment(imp, title, path, alignment_type, channels, force_save):
    if alignment_type == ("Rigid Body" or "Scaled Rotation"):
        alignment_type = "[" + alignment_type + "]"
    channels_list = [key.lower() for key, v in channels.items() if v == True]
    # IJ.log(str(channels_list))
    channel_str = ' '.join(channels_list)
    IJ.run(imp, "HyperStackReg ", "transformation=" + ' '.join([alignment_type, channel_str]))
    IJ.log("Processing the file " + title)
    HyperStackConverter.toStack(imp)
    if (not os.path.exists(path)) or force_save:
        IJ.saveAs(imp, "Tiff", path)
    else:
        IJ.log("The file already exists.Skipping")
    IJ.run("Close All")


def create_gui(channels_number):
    gui = GenericDialog("Alignment: Input parameters")
    gui.addMessage("Choose the type of alignment")
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
    alignmentType = gui.getNextChoice()
    channels = {}
    for i in range(channels_number):
        channels["Channel" + str(i + 1)] = gui.getNextBoolean()
    forceSave = gui.getNextBoolean()
    return [alignmentType, channels, forceSave]


def main():
    hsDir = config.concatenatesDir
    outDir = config.alignmentDir
    for hs in os.listdir(hsDir):
        if "concatenate" in os.path.basename(hs) and hs.endswith(config.tiff_ext):
            stack_to_crop_path = os.path.join(hsDir, hs)
            imp = IJ.openImage(stack_to_crop_path)
            channel_no = imp.getNChannels()
            try:
                alignment_type, channels, force_save = create_gui(channel_no)
            except:
                # pass
                # user canceled dialog
                return
            alignment_path = os.path.join(outDir, hs.split(".")[0] + "_alignment_" + alignment_type +
                                          config.tiff_ext).replace("\\", "/")
            alignment(imp, hs.split(".")[0], alignment_path, alignment_type, channels, force_save)
            # imp.close()
        else:
            IJ.log("No files found in the subfolder \"concatenates\". Skipping")
    IJ.log("Run is finished")


if __name__ in ['__builtin__', '__main__']:
    main()
