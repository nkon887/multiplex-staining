# multiplex.helpertools.py
import os
import logging
import multiplex.setup_logger

# multiplex.helpertools.py creates its own logger, as a sub logger to 'multiplex'
logger = logging.getLogger('multiplex.helpertools')


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


def setting_directory(*args, **kwargs):
    dir_path = os.path.join(*args, **kwargs).replace("\\", "/")
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


def correct_path(*args, **kwargs):
    path = os.path.join(*args, **kwargs).replace("\\", "/")
    return path


def gpu_tesing(self):
    import tensorflow as tf
    import warnings
    warnings.filterwarnings('ignore')
    # Checking Version of Tensorflow
    logger.info("Version of Tensorflow: ", tf.__version__)
    # Checking if cuda is there.
    cuda_availability = tf.test.is_built_with_cuda()
    gpu_availability = tf.test.is_gpu_available()
    logger.info("Cuda Availability: ", cuda_availability)
    # Checking GPU is available or not.
    logger.info("GPU  Availability: ", gpu_availability)
    if cuda_availability and gpu_availability:
        return True
    else:
        return False
