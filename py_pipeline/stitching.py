import os
import time
from ij import IJ, ImagePlus, ImageStack, Prefs, WindowManager
from loci.plugins import BF
from loci.plugins. in import ImporterOptions
from loci.formats import MetadataTools
from loci.formats. in import ZeissCZIReader
from ij.plugin import ImageCalculator
from ij.io import FileSaver
from java.lang import System
from ij.plugin import HyperStackConverter
import re
from loci.plugins import LociExporter
from loci.plugins.out import Exporter


class stitchingTools:
    def __init__(self, inputdir, outputdir):
        self.inputdir = inputdir
        self.outputdir = outputdir
    def getImageSeries(self, imps, series=0):

        try:
            imp = imps[series]
            pylevelout = series
        except:
            # fallback option
            print('PyLevel = ' + str(series) + ' does not exist.')
            print('Using Pyramid Level = 0 as fallback.')
            imp = imps[0]
            pylevelout = 0

        # get the stack and some info
        imgstack = imp.getImageStack()
        slices = imgstack.getSize()
        width = imgstack.getWidth()
        height = imgstack.getHeight()

        return imp, slices, width, height, pylevelout
    def renameStack(self, stack_width, stack_height, imp, metainfo):
        print("Setting channel names...")
        res_stack = ImageStack(stack_width, stack_height)
        stack = imp.getImageStack()
        for i in range(1, stack.size() + 1):
            res_stack.addSlice(metainfo["channel " + str(i)], stack.getProcessor(i))
        renamed_stack = ImagePlus("renamed", res_stack)
        return renamed_stack
    def save_singleplanes(self, imp, savepath, metainfo, format='tiff'):
        IJ.run(imp, "8-bit", "")
        stack = imp.getImageStack()
        for s in range(1, stack.size() + 1):
            slicetitle = metainfo["fileID"] + "_" + metainfo["channel " + str(s)] + "." + format
            #+ "c" + str(s - 1) + "." + format
            stackindex = s
            print(str(stackindex))
            aframe = ImagePlus(slicetitle, imp.getStack().getProcessor(stackindex))
            outputpath = os.path.join(savepath, slicetitle)
            IJ.saveAs(aframe, "TIFF", outputpath)
    def removeAllTemps(self, directory):
        for filename in os.listdir(directory):
            if not filename.endswith(".xml"):
                os.remove(os.path.join(directory, filename))
    def write_infos_txt(self, metainfo, savingDir):
        p = os.path.join(savingDir, "infos.txt")
        date = metainfo["fileID"].split("_")[0]
        if not os.path.exists(p):
            f = open(p, "w")
            f.write(str(date) + " ")
        else:
            f = open(p, "a")
            f.write("\n" + str(date) + " ")
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + metainfo["channel " + str(channel + 1)])
        #"c" + str(channel))
        f.close()


    def process(self):
        dir = self.inputdir
        shadingfile = ""
        if os.listdir(dir):
            for image_file in os.listdir(dir):
                if image_file.endswith(".czi") and not(re.search(".*shading.*", image_file)):
                    imagefile = os.path.join(dir, image_file)
                    IJ.log("Current File: " + imagefile)
                    czireader = ZeissCZIReader()
                    czireader.allowAutostitching()
                    omeMeta = MetadataTools.createOMEXMLMetadata()
                    czireader.setMetadataStore(omeMeta)
                    czireader.setId(imagefile)
                    czireader.close()
                    stitchtiles = False
                    attach = False
                    # Set the preferences in the ImageJ plugin
                    # Although these preferences are applied, they are not refreshed in the UI
                    Prefs.set("bioformats.zeissczi.allow.autostitch", str(stitchtiles).lower())
                    Prefs.set("bioformats.zeissczi.include.attachments", str(attach).lower())
                    options = ImporterOptions()
                    options.setOpenAllSeries(True)
                    options.setShowOMEXML(False)
                    options.setStitchTiles(False)
                    options.setId(imagefile)
                    options.setStackFormat("Standard ImageJ")
                    options.setColorMode("Default")
                    #options.setColorMode("Grayscale")
                    options.setStackOrder("Default")
                    imps = BF.openImagePlus(options)
                    metaData = {}
                    # metaData["xCoordinate"] = omeMeta.getPlanePositionX(0, 0)
                    # metaData["yCoordinate"] = omeMeta.getPlanePositionY(0, 0)
                    # metaData["zCoordinate"] = omeMeta.getPlanePositionZ(0, 0)
                    imageID = 0
                    metaData["channelsNumber"] = omeMeta.getChannelCount(imageID)
                    for channel in range(metaData["channelsNumber"]):
                        metaData["channel " + str(channel + 1)] = omeMeta.getChannelName(0, channel)
                    # read dimensions XY from OME metadata
                    # read dimensions TZCXY from OME metadata
                    metaData["SizeT"] = omeMeta.getPixelsSizeT(imageID).getValue()
                    metaData["SizeZ"] = omeMeta.getPixelsSizeZ(imageID).getValue()
                    metaData["SizeC"] = omeMeta.getPixelsSizeC(imageID).getValue()
                    metaData["SizeX"] = omeMeta.getPixelsSizeX(imageID).getValue()
                    metaData["SizeY"] = omeMeta.getPixelsSizeY(imageID).getValue()
                    _, slices, metaData["widthTile"], metaData["heightTile"], pylevelout = self.getImageSeries(imps)
                    metaData["num_X_tiles"] = (metaData["SizeX"] + metaData["widthTile"] - 1) // metaData["widthTile"]
                    metaData["num_Y_tiles"] = (metaData["SizeY"] + metaData["heightTile"] - 1) // metaData["heightTile"]
                    metaData["number_of_tiles"] = (len(imps))
                    tilefileID = os.path.basename(imps[0].getTitle())
                    tilefileID_strings = os.path.splitext(tilefileID)[0]
                    fileID = tilefileID_strings.split(".czi - ")[1]
                    fileID = fileID.replace(" ", "_")
                    IJ.log(fileID)
                    metaData["fileID"] = fileID
                    savingDir = os.path.join(self.outputdir, fileID)
                    if not os.path.exists(savingDir):
                        os.makedirs(savingDir)
                    # export the ImgPlus
                    savepath = os.path.join(savingDir, r"LOCI.ome.xml")
                    paramstring = "outfile=[" + savepath + "] windowless=true compression=Uncompressed saveROI=false"
                    plugin = LociExporter()
                    plugin.arg = paramstring
                    t0 = time.time()
                    exporter = Exporter(plugin, imps[0])
                    exporter.run()
                    t1 = time.time()
                    total = t1 - t0
                    print("Export complete OME-TIFF using LOCI: {}".format(total))
                    for image_file in os.listdir(dir):
                        if (image_file.endswith(".czi")) and (re.search(".*shading.*", image_file)) and (re.search(str(metaData["fileID"].split("_")[0]) + ".*", image_file)):
                            shadingfile = os.path.join(dir, image_file)
                            options.setId(shadingfile)
                            shadefile = BF.openImagePlus(options)
                    IJ.log("Current Shading File: " + shadingfile)
                    for i, imp in enumerate(imps):
                        if shadingfile != "":
                            imp_res = ImageCalculator().run("Subtract create stack", imp, shadefile[0])
                        else:
                            imp_res = imp
                        tile_name = "tile_" + str(i + 1).zfill(3) + ".tif"
                        IJ.log("Saving " + tile_name + " under " + savingDir)
#                        HyperStackConverter.toStack(imp_res)
                        FileSaver(imp_res).saveAsTiff(os.path.join(savingDir, tile_name))
                        IJ.log("Saving :  Ends at " + str(time.time()))
                        IJ.run("Close All")
                    prefix = "type=[Grid: snake by rows] order=[Right & Down                ] grid_size_x=" + str(
                        metaData["num_X_tiles"]) + " grid_size_y=" + str(metaData[
                                                                             "num_Y_tiles"]) + " tile_overlap=30 first_file_index_i=001 directory=" + savingDir + " file_names=tile_{iii}.tif output_textfile_name=TileConfiguration.txt "
                    suffix = "fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 compute_overlap computation_parameters=[Save memory (but be slower)] image_output=[Fuse and display]"
                    IJ.run("Grid/Collection stitching", prefix + suffix)
                    res = WindowManager.getCurrentImage()
                    self.removeAllTemps(savingDir)
                    # HyperStackConverter.toStack(res)
                    self.save_singleplanes(res, savingDir, metaData, format='tiff')
                    if os.path.exists(os.path.join(dir, "infos.txt")):
                        with open(os.path.join(dir, "infos.txt")) as f:
                            if not metaData["fileID"].split("_")[0] in f.read():
                                self.write_txt(metaData, dir)
                    else:
                        self.write_txt(metaData, dir)
                    # merged_file_path=os.path.join(savingDir, fileID + ".tif")
                    # result_stack = self.renameStack(res.getWidth(), res.getHeight(), res, metaData)
                    # FileSaver(result_stack).saveAsTiff(merged_file_path)
                    res.changes = False
                    res.close()
                else:
                    IJ.log("Error, cannot find any czi file")
                # clear memory
                System.gc()
                stitchtiles = True
                attach = True
                # Set the preferences in the ImageJ plugin back to default
                Prefs.set("bioformats.zeissczi.allow.autostitch", str(stitchtiles).lower())
                Prefs.set("bioformats.zeissczi.include.attachments", str(attach).lower())
            # Save the log file
            IJ.selectWindow("Log")
            thisFile = os.path.join(dir, "Log.txt")
            IJ.saveAs("Text", thisFile)
        else:
            print("Directory is empty. There are no czi files")