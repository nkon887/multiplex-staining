import os
import shutil
import sys

from ij.gui import GenericDialog
from ij import IJ

from loci.formats import ChannelSeparator


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


def dimensions_of(path, main_dir, error_dir):
    fr = None
    try:
        fr = ChannelSeparator()
        fr.setGroupFiles(False)
        fr.setId(path)
        return fr.getSizeX(), fr.getSizeY()
    except:
        # Print the error, if any
        print(sys.exc_info())
        print("ImportProcess failed to execute on %s" % path)
        dir_name = os.path.basename(path).split(".")[0].split("_")[1]
        filename = os.path.basename(path)
        dirpath = os.path.join(main_dir, dir_name, error_dir).replace("\\",
                                                                      "/")
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        shutil.copy(path.replace("\\", "/"), os.path.join(dirpath, filename).replace("\\",
                                                                                     "/"))
    finally:
        fr.close()
