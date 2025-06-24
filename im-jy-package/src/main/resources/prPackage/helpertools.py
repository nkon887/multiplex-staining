import logging
import os
import shutil
import sys
import time
from datetime import datetime

from ij.gui import GenericDialog
from loci.formats import ChannelSeparator

# im-jy-package.helpertools.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.helpertools')


def ask_to_overwrite(step_name):
    gui = GenericDialog(step_name.upper() + " - Overwrite files?")
    gui.addMessage("Should the existing files be overwritten?")
    gui.addCheckbox("forceSave", False)
    gui.showDialog()
    if gui.wasCanceled():
        logger.warning("User canceled dialog! Doing nothing. Exit")
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
        logger.exception(sys.exc_info())
        logger.exception("ImportProcess failed to execute on %s" % path)
        dir_name = os.path.basename(path).split(".")[0].split("_")[1]
        filename = os.path.basename(path)
        dirpath = correct_path(main_dir, dir_name, error_dir)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        shutil.copy(path.replace("\\", "/"), correct_path(dirpath, filename))
    finally:
        fr.close()


def find_existing_location(possible_locations, unique_location=1):
    logger.info("searching " + str(len(possible_locations)) + " locations")
    location_list = []
    for location in possible_locations:
        if os.path.isdir(location):
            location_list.append(location)
            logger.info("found location " + location)
    if len(location_list) == 0:
        logger.warning("no location found")
    elif unique_location and len(location_list) > 1:
        logger.warning("ambigious locations found:" + str(location_list))
    return location_list[0]


def setting_directory(*args, **kwargs):
    dir_path = correct_path(*args, **kwargs)
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


def step_execution(step, func, *args, **kwargs):
    # logger.info(step)
    # func_name = func.__name__
    # logger.info("Starting " + func_name)
    # start
    # dd/mm/YY H:M:S
    logger.info("Start time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])
    start_time = time.time()
    func(*args, **kwargs)
    end_time = time.time()
    logger.info("Duration of the program execution: " + convert(end_time - start_time) + "\nEnd time = " + str(datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S.%f"))[:-7])


def correct_path(*args, **kwargs):
    path = os.path.join(*args, **kwargs).replace("\\", "/")
    return path


def read_data_from_csv(tempfile):
    with open(tempfile) as f:
        headers = next(f).rstrip().split(',')
        data = [dict(zip(headers, line.rstrip().split(','))) for line in f]
        data.sort()
    return data
