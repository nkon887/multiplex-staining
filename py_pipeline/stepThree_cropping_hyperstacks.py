import sys, os
from ij import IJ, ImagePlus, VirtualStack
from ij.io import FileSaver
from ij.plugin import HyperStackConverter

sys.path.append(os.path.abspath(os.getcwd()))
# sys.path.append(os.path.abspath("C:/Users/nko88/PycharmProjects/muliplex-staining/py_pipeline"))
import config
from ij.plugin.frame import RoiManager
from ij.gui import WaitForUserDialog, Toolbar
from ij.gui import GenericDialog


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


ext = ".tif"
hsDir = config.hyperstacksDir
hsFiles = []
for hs in os.listdir(hsDir):
    if not ("_Cropped" in os.path.basename(hs)):
        hsFiles.append(hs)
# IJ.log(hsDir)
stackToCropPath = os.path.join(hsDir, hsFiles[0])
imp = IJ.openImage(stackToCropPath)
imp.show()
# imp = IJ.getImage()
stack = imp.getStack()
try:
    force_save = ask_for_parameters()
except:
    pass
# user canceled dialog
#       return
# remove all the previous ROIS
rm = RoiManager.getInstance()
if not rm:
    rm = RoiManager()
    rm.runCommand("reset")
# ask the user to define a selection and get the bounds of the selection
IJ.setTool(Toolbar.RECTANGLE)
WaitForUserDialog("Select the area,then click OK.").show()
roi = imp.getRoi()
imp.setRoi(roi)
rm.addRoi(roi)
rois = rm.getRoisAsArray()  # this is a list of rois (only 1 as it got cleared
for hs in hsFiles:
    hyperstackCropped_path = os.path.join(hsDir, os.path.basename(hs).split('.')[0] + "_Cropped" + ext).replace(
        "\\", "/")
    # Save output
    if (not os.path.exists(hyperstackCropped_path)) or force_save:
        if not hs == hsFiles[0]:
            imp = IJ.openImage(os.path.join(config.hyperstacksDir, hs))
            IJ.log(str(imp.isStack()))
            if not (imp.isStack() or imp.isHyperStack()):
                IJ.log("The input" + hs + "is not a Stack. Skipping")
                continue
            imp.show()
            stack = imp.getStack()
            # ask the user to define a selection and get the bounds of the selection
            imp.setRoi(rois[0])
            WaitForUserDialog("Adjust the area,then click OK.").show()
            roi = imp.getRoi()
            imp.setRoi(roi)
            rm.addRoi(roi)
        cropped = ImagePlus("cropped", CroppedStack())
        # cropped.show()
        imp.close()
        FileSaver(HyperStackConverter.toHyperStack(cropped, cropped.getNSlices(), 1, 1, "xyczt(default)",
                                                   "Grayscale")).saveAsTiff(hyperstackCropped_path)
    else:
        IJ.log("The hyperstack file " + hyperstackCropped_path + " exists. Skipping")
rm.close()
