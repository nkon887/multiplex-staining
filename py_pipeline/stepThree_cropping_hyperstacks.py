import os
import sys

#sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config

from ij import IJ, ImagePlus, VirtualStack
from ij.gui import WaitForUserDialog, Toolbar
from ij.gui import GenericDialog
from ij.io import FileSaver
from ij.plugin import HyperStackConverter


def ask_for_parameters():
    gui = GenericDialog("Overwrite files?")
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    forceSave = gui.getNextBoolean()
    return forceSave


class CroppedStack(VirtualStack):
    def __init__(self):
        # Constructor: tell the superclass VirtualStack about the dimensions
        super(VirtualStack, self).__init__(stack.getWidth(), stack.getHeight(), stack.size())

    def getProcessor(self, n):
        # Modify the same slice at index n every time it is requested
        ip = stack.getProcessor(n)
        ip.setRoi(roi)
        return ip.crop()


#def main():
ext = ".tif"
hsDir = config.hyperstacksDir
hsFiles = os.listdir(hsDir)
IJ.log(hsDir)
stackToCropPath = os.path.join(hsDir, hsFiles[0])
imp = IJ.openImage(stackToCropPath)
hstack = imp.getStack()
stack = ImagePlus("hyper", hstack)
stack.show()
try:
    force_save = ask_for_parameters()
except:
	pass
# user canceled dialog
#       return
# ask the user to define a selection and get the bounds of the selection
IJ.setTool(Toolbar.RECTANGLE)
WaitForUserDialog("Select the area,then click OK.").show()
roi = imp.getRoi()
for hs in os.listdir(hsDir):
    IJ.log(hsDir)
    hyperstackCropped_path = os.path.join(hsDir, os.path.basename(hs).split('.')[0] + "_Cropped" + ext).replace("\\", "/")
    # Save output
    if (not os.path.exists(hyperstackCropped_path)) or force_save:
        IJ.log("Saving the cropped hyperstack as " + hyperstackCropped_path)
        imp = IJ.openImage(os.path.join(config.hyperstacksDir, hs))
        stack = imp.getStack()
        cropped = ImagePlus("cropped", CroppedStack())
        IJ.log(str(cropped.getNSlices()))
        FileSaver(HyperStackConverter.toHyperStack(cropped, cropped.getNSlices(), 1, 1, "xyczt(default)",
                                                       "Grayscale")).saveAsTiff(hyperstackCropped_path)
    else:
        IJ.log("The hyperstack file " + hyperstackCropped_path + " exists. Skipping")
#if __name__ in ['__builtin__', '__main__']:
#    main()