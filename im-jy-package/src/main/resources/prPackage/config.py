# settings
import logging

# im-jy-package.config.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.config')
info_txt_file = 'infos.txt'
channel_list = ["channel 0", "channel 1", "channel 2", "channel 3"]
dates_number = 20
input_dates = 'dates'
channel_patterns = ["c0", "c1", "c2", "c3"]
standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["", "", "", "_"]
dapi_str = "dapi"
stack_name = "Stack"
czi_ext = ".czi"
tiff_ext = ".tif"
cropped_suffix = "_Cropped"
error_subfolder_name = "error_subfolder"
no_shading_file = "No_shading_file"
shading_word = "shading"
metadata_csv_file = "metadata.csv"
TIFF_ext = "TIFF"
csv_ext = ".csv"
