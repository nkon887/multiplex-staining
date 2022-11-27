import os
import shutil


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


def setting_directory(base_dir, dir_name):
    dir_path = os.path.join(base_dir, dir_name).replace("\\", "/")
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return dir_path


# def parse_dir(src_top, dest_top):
#     for dir_path, dir_names, file_names in os.walk(src_top):
#         for file_name in file_names:
#             target_dir = dir_path.replace(src_top, dest_top, 1)
#             if not os.path.exists(target_dir):
#                 os.mkdir(target_dir)
#             src_file = os.path.join(dir_path, file_name)
#             dest_file = os.path.join(target_dir, file_name)
#            shutil.copyfile(src_file, dest_file)

def progress_percentage(perc, width=None):
    # This will only work for python 3.3+ due to use of
    # os.get_terminal_size the print function etc.

    FULL_BLOCK = '█'
    # this is a gradient of incompleteness
    INCOMPLETE_BLOCK_GRAD = ['░', '▒', '▓']

    assert (isinstance(perc, float))
    assert (0. <= perc <= 100.)
    # if width unset use full terminal
    if width is None:
        width = os.get_terminal_size().columns
    # progress bar is block_widget separator perc_widget : ####### 30%
    max_perc_widget = '[100.00%]'  # 100% is max
    separator = ' '
    blocks_widget_width = width - len(separator) - len(max_perc_widget)
    assert (blocks_widget_width >= 10)  # not very meaningful if not
    perc_per_block = 100.0 / blocks_widget_width
    # epsilon is the sensitivity of rendering a gradient block
    epsilon = 1e-6
    # number of blocks that should be represented as complete
    full_blocks = int((perc + epsilon) / perc_per_block)
    # the rest are "incomplete"
    empty_blocks = blocks_widget_width - full_blocks

    # build blocks widget
    blocks_widget = ([FULL_BLOCK] * full_blocks)
    blocks_widget.extend([INCOMPLETE_BLOCK_GRAD[0]] * empty_blocks)
    # marginal case - remainder due to how granular our blocks are
    remainder = perc - full_blocks * perc_per_block
    # epsilon needed for rounding errors (check would be != 0.)
    # based on reminder modify first empty block shading
    # depending on remainder
    if remainder > epsilon:
        grad_index = int((len(INCOMPLETE_BLOCK_GRAD) * remainder) / perc_per_block)
        blocks_widget[full_blocks] = INCOMPLETE_BLOCK_GRAD[grad_index]

    # build perc widget
    str_perc = '%.2f' % perc
    # -1 because the percentage sign is not included
    perc_widget = '[%s%%]' % str_perc.ljust(len(max_perc_widget) - 3)

    # form progressbar
    progress_bar = '%s%s%s' % (''.join(blocks_widget), separator, perc_widget)
    # return progressbar as string
    return ''.join(progress_bar)


def copy_progress(copied, total):
    print('\r' + progress_percentage(100 * copied / total, width=30), end='')


def copyfile(src, dst, *, follow_symlinks=True):
    """Copy data from src to dst.

    If follow_symlinks is not set and src is a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    if shutil._samefile(src, dst):
        raise shutil.SameFileError("{!r} and {!r} are the same file".format(src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if shutil.stat.S_ISFIFO(st.st_mode):
                raise shutil.SpecialFileError("`%s` is a named pipe" % fn)

    if not follow_symlinks and os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    else:
        size = os.stat(src).st_size
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                copyfileobj(fsrc, fdst, callback=copy_progress, total=size)
    return dst


def copyfileobj(fsrc, fdst, callback, total, length=16 * 1024):
    copied = 0
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        callback(copied, total=total)


def copy_with_progress(src, dst, *, follow_symlinks=True):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    print("\nfolder: " + str(os.path.dirname(src)) + " file: " + str(os.path.basename(src)))
    copyfile(src, dst, follow_symlinks=follow_symlinks)
    shutil.copymode(src, dst)
    return dst


def dapi_tiff_image_filenames(directory, dapi_str, ext):
    dapi_tiff_files = []
    files = os.listdir(directory)
    if not files == []:
        for filename in sorted(files):
            if ((dapi_str or dapi_str.upper() or dapi_str.lower()) in filename) and (filename.endswith(ext)):
                dapi_tiff_files.append(filename)
    return dapi_tiff_files
