import os
import sys
from ij import IJ
from ij.gui import GenericDialog
from ij.plugin import HyperStackConverter

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config


def alignment(imp, title, path, alignmentType, channels, forceSave):
    if alignmentType == ("Rigid Body" or "Scaled Rotation"):
        alignmentType = "[" + alignmentType + "]"
    channelsList = [key.lower() for key, v in channels.items() if v == True]
    # IJ.log(str(channelsList))
    channelStr = ' '.join(channelsList)
    IJ.run(imp, "HyperStackReg ", "transformation=" + ' '.join([alignmentType, channelStr]))
    IJ.log("Processing the file " + title)
    HyperStackConverter.toStack(imp)
    if (not os.path.exists(path)) or forceSave:
        IJ.saveAs(imp, "Tiff", path)
    else:
        IJ.log("The file already exists.Skipping")
    IJ.run("Close All")


def createGUI(channelsNumber):
    gui = GenericDialog("Alignment: Input parameters")
    gui.addMessage("Choose the type of alignment")
    gui.addChoice("Alignment type", ["Affine", "Rigid Body", "Translation", "Scaled Rotation"],
                  "Rigid Body")  # rigidBody is default here
    gui.addMessage("Choose the channels")
    for i in range(channelsNumber):
        gui.addCheckbox("Channel" + str(i + 1), False)
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    alignmentType = gui.getNextChoice()
    channels = {}
    for i in range(channelsNumber):
        channels["Channel" + str(i + 1)] = gui.getNextBoolean()
    forceSave = gui.getNextBoolean()
    return [alignmentType, channels, forceSave]


def main():
    ext = ".tif"
    hsDir = config.concatenatesDir
    outDir = config.alignmentDir
    for hs in os.listdir(hsDir):
        if "concatenate_" in os.path.basename(hs) and hs.endswith(ext):
            stackToCropPath = os.path.join(hsDir, hs)
            imp = IJ.openImage(stackToCropPath)
            channel_no = imp.getNChannels()
            try:
                alignmentType, channels, forceSave = createGUI(channel_no)
            except:
                # pass
                # user canceled dialog
                return
            alignment_path = os.path.join(outDir, hs.split(".")[0] + "alignment_" + alignmentType + ext).replace("\\",
                                                                                                                 "/")
            alignment(imp, hs.split(".")[0], alignment_path, alignmentType, channels, forceSave)
            # imp.close()


if __name__ in ['__builtin__', '__main__']:
    main()
