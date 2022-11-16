##!python
import os
import pythontools as pt

baseDir = pt.find_existing_location(["J:/", "C:/Users/nko88/Desktop/attic"])
workingDir = os.path.join(baseDir, "workingDir").replace("\\", "/")
if not os.path.exists(workingDir):
    os.mkdir(workingDir)
inputDir = os.path.join(workingDir, "input").replace("\\", "/")
if not os.path.exists(inputDir):
    os.mkdir(inputDir)
hyperstacksDir = os.path.join(workingDir, "hyperstacks").replace("\\", "/")
if not os.path.exists(hyperstacksDir):
    os.mkdir(hyperstacksDir)
concatenatesDir = os.path.join(workingDir, "concatenates").replace("\\", "/")
if not os.path.exists(concatenatesDir):
    os.mkdir(concatenatesDir)
alignmentDir = os.path.join(workingDir, "alignment").replace("\\", "/")
if not os.path.exists(alignmentDir):
    os.mkdir(alignmentDir)

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
