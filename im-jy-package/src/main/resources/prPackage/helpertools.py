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


def find_existing_location(possible_locations, unique_location=1):
    print("searching " + str(len(possible_locations)) + " locations")
    location_list = []
    for location in possible_locations:
        if os.path.isdir(location):
            location_list.append(location)
            print("found location " + location)
    if len(location_list) == 0:
        print("no location found")
    elif unique_location and len(location_list) > 1:
        print("ambigious locations found:" + str(location_list))
    return location_list[0]


def setting_directory(basedir, dir_name):
    dir_path = os.path.join(basedir, dir_name).replace("\\", "/")
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return dir_path


def dapi_tiff_image_filenames(directory, dapi_str, ext):
    dapi_tiff_files = []
    files = os.listdir(directory)
    if not files == []:
        for filename in sorted(files):
            if ((dapi_str or dapi_str.upper() or dapi_str.lower()) in filename) and (filename.endswith(ext)):
                dapi_tiff_files.append(filename)
    return dapi_tiff_files


# to Convert seconds
# into hours, minutes and seconds
def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)
