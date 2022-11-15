import os
import sys
from ij.io import FileSaver
from ij import IJ, ImagePlus
from ij.plugin import HyperStackConverter
from ij.gui import GenericDialog

# sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config


def alignment(imp, title, path, alignmentType, channels, forceSave):
	if alignmentType== "Rigid Body" or "Scaled Rotation":
		alignmentType = "["+alignmentType+"]"
	IJ.run(imp, "HyperStackReg ", "transformation="+alignmentType+" "+"channel1")
	IJ.log("Processing the file " + title)
	HyperStackConverter.toStack(imp)
	if (not os.path.exists(path)) or forceSave:
		IJ.saveAs(imp,"Tiff", path)
	else:
		IJ.log("File already exists.Skipping")
	IJ.run("Close All")
    
def createGUI(channelsNumber):
    gui = GenericDialog("Alignment: Input parameters")
    gui.addMessage("Choose the type of alignment")
    gui.addChoice("Alignment type", ["Affine", "Rigid Body", "Translation", "Scaled Rotation"],
                  "Rigid Body")  # rigidBody is default here
    gui.addMessage("Choose the channels")    
    for i in range(channelsNumber):
    	gui.addCheckbox("Channel"+str(i+1), False)
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    alignmentType = gui.getNextChoice()
    channels = {}
    for i in range(channelsNumber):
        channels["Channel" + str(i+1)] = gui.getNextBoolean()    
    forceSave = gui.getNextBoolean()
    return [alignmentType, channels, forceSave]


ext = ".tif"
hsDir = config.concatenatesDir
outDir = config.alignmentDir
hsFiles = []
for hs in os.listdir(hsDir):
    if "concatenate_" in os.path.basename(hs) and hs.endswith(ext):
        stackToCropPath = os.path.join(hsDir, hs)
        imp = IJ.openImage(stackToCropPath)
        channel_no=imp.getNChannels()
        #IJ.log(str(channel_no))
        alignmentType, channels, forceSave = createGUI(channel_no)
        alignment_path = os.path.join(outDir, hs.split(".")[0]+ "alignment_" + ext).replace("\\", "/")
        alignment(imp, hs.split(".")[0], alignment_path, alignmentType, channels, forceSave)
        #imp.close()