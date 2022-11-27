from ij.gui import GenericDialog
from ij import IJ


def ask_to_overwrite():
    gui = GenericDialog("Overwrite files?")
    gui.addMessage("Should the existing files be overwritten?")
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        IJ.log("User canceled dialog! Doing nothing. Exit")
        return
    force_save = gui.getNextBoolean()
    return force_save
