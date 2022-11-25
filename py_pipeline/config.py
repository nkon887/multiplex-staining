##!python
import pythontools as pt

baseDir = pt.find_existing_location(["J:/", "C:/Users/nko88/Desktop/attic"])
workingDir = pt.setting_directory(baseDir, "workingDir")
inputDir = pt.setting_directory(workingDir, "01_input")
hyperstacksDir = pt.setting_directory(workingDir, "02_hyperstacks")
concatenatesDir = pt.setting_directory(workingDir, "03_concatenates")
alignmentDir = pt.setting_directory(workingDir, "04_alignment")
contrastBgAdjustDir = pt.setting_directory(workingDir, "05_contrastBG")
mergeChannelsDir = pt.setting_directory(workingDir, "06_mergedChannels")

# setting stepOne

info_txt_file = 'infos.txt'
table_dapi_title = "Dapi Channel"
table_dapi_entry = "0dapi"
channel_list = ["channel 1", "channel 2", "channel 3"]
dates_number = 20
dapi_channel = "c0"
input_dates = 'dates'
channel_patterns = ["c1", "c2", "c3"]
standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
standard_replacements = ["", "", "", "_"]

# settings stepTwo

dapi_str = "dapi"
stack_name = "Stack"

# settings stepTwo, stepThree,  stepFour, stepFive

tiff_ext = ".tif"
