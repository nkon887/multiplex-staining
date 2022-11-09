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
hyperstacksDir = os.path.join(inputDir, "hyperstacks").replace("\\", "/")
if not os.path.exists(hyperstacksDir):
    os.mkdir(hyperstacksDir)
