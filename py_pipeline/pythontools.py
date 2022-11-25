import errno
import os
import shutil
from ij.gui import GenericDialog


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


def parse_dir(src_top, dest_top):
    for dir_path, dir_names, file_names in os.walk(src_top):
        for file_name in file_names:
            target_dir = dir_path.replace(src_top, dest_top, 1)
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)
            src_file = os.path.join(dir_path, file_name)
            dest_file = os.path.join(target_dir, file_name)
            shutil.copyfile(src_file, dest_file)


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
