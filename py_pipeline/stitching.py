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
import re
from loci.plugins import LociExporter
from loci.plugins.out import Exporter


class stitchingTools:
    def __init__(self, inputdir, outputdir, czi_ext, tif_ext):
        self.inputdir = inputdir
        self.outputdir = outputdir
        self.czi_ext = czi_ext
        self.tif_ext = tif_ext
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
    def write_infos_txt(self, metainfo, saving_dir):
        p = os.path.join(saving_dir, "infos.txt")
        date = metainfo["date"]
        if not os.path.exists(p):
            f = open(p, "w")
            f.write(str(date))
        else:
            f = open(p, "a")
            f.write("\n" + str(date))
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + metainfo["channel " + str(channel + 1)])  #"c" + str(channel))
        f.close()

    def get_meta(self, meta, imps, file_id, image_id = 0):
        metaData = {}
        metaData["fileID"] = file_id
        file_id_strings = file_id.split("_")
        metaData["date"] = file_id_strings[0]
        metaData["expID"] = file_id_strings[1]
        metaData["channelsNumber"] = meta.getChannelCount(image_id)
        # read dimensions XYZ from OME metadata
        metaData["xCoordinate"] = meta.getPlanePositionX(image_id, 0)
        metaData["yCoordinate"] = meta.getPlanePositionY(image_id, 0)
        metaData["zCoordinate"] = meta.getPlanePositionZ(image_id, 0)
        # read dimensions TZCXY from OME metadata
        metaData["SizeT"] = meta.getPixelsSizeT(image_id).getValue()
        metaData["SizeZ"] = meta.getPixelsSizeZ(image_id).getValue()
        metaData["SizeC"] = meta.getPixelsSizeC(image_id).getValue()
        metaData["SizeX"] = meta.getPixelsSizeX(image_id).getValue()
        metaData["SizeY"] = meta.getPixelsSizeY(image_id).getValue()
        # read channels from OME metadata
        for channel in range(metaData["channelsNumber"]):
            metaData["channel " + str(channel + 1)] = meta.getChannelName(image_id, channel)
        # read
        _, slices, metaData["widthTile"], metaData["heightTile"], pylevelout = self.getImageSeries(imps)
        metaData["num_X_tiles"] = (metaData["SizeX"] + metaData["widthTile"] - 1) // metaData["widthTile"]
        metaData["num_Y_tiles"] = (metaData["SizeY"] + metaData["heightTile"] - 1) // metaData["heightTile"]
        metaData["number_of_tiles"] = (len(imps))
        for channel in range(metaData["channelsNumber"]):
            metaData[
                "PlaneExposureTime_" + str(metaData["channel " + str(channel + 1)])] = str(meta.getPlaneExposureTime(image_id, channel).value()) + " s"
        metaData["ObjectiveSettingsRefractiveIndex"] = meta.getObjectiveSettingsRefractiveIndex(image_id)
        return metaData
    def write_metadata_txt(self, metainfo, saving_dir):
        p = os.path.join(saving_dir, "metadata.txt")
        date = metainfo["date"]
        if not os.path.exists(p):
            f = open(p, "w")
            f.write("date: " + str(date))
        else:
            f = open(p, "a")
            f.write("\n" + "date: " + str(date))
        f.write("\n" + "experimentID: " + metainfo["expID"])
        f.write("\n" + "Channels:")
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + metainfo["channel " + str(channel + 1)]) #"c" + str(channel))
        f.write("\n" + "ExposureTimes:")
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + "Channel " + str(channel+1) + ": " + str(metainfo[
                "PlaneExposureTime_" + str(metainfo["channel " + str(channel + 1)])]))
        f.write("\n" + "Scale: " + str(metainfo["ObjectiveSettingsRefractiveIndex"]))
        f.close()

    def write_meta_xml(self, saving_dir, imps):
        # export the ImgPlus
        savepath = os.path.join(saving_dir, r"LOCI.ome.xml")
        paramstring = "outfile=[" + savepath + "] windowless=true compression=Uncompressed saveROI=false"
        plugin = LociExporter()
        plugin.arg = paramstring
        t0 = time.time()
        exporter = Exporter(plugin, imps[0])
        exporter.run()
        t1 = time.time()
        total = t1 - t0
        print("Export complete OME-TIFF using LOCI: {}".format(total))
    def set_prefs(self, stitchtiles, attach):
        # Set the preferences in the ImageJ plugin
        # Although these preferences are applied, they are not refreshed in the UI
        Prefs.set("bioformats.zeissczi.allow.autostitch", str(stitchtiles).lower())
        Prefs.set("bioformats.zeissczi.include.attachments", str(attach).lower())
    def set_import_options(self, image_file, openAllSeries = True, showOMEXML = False, stichTiles = False, stackFormat = "Standard ImageJ", colorMode = "Default", stackOrder = "Default"):
        options = ImporterOptions()
        options.setOpenAllSeries(openAllSeries)
        options.setShowOMEXML(showOMEXML)
        options.setStitchTiles(stichTiles)
        options.setId(image_file)
        options.setStackFormat(stackFormat)
        options.setColorMode(colorMode)
        options.setStackOrder(stackOrder)
        return options
    def get_omemeta(self, image_file):
        czireader = ZeissCZIReader()
        czireader.allowAutostitching()
        omeMeta = MetadataTools.createOMEXMLMetadata()
        czireader.setMetadataStore(omeMeta)
        czireader.setId(image_file)
        czireader.close()
        return omeMeta
    def shading_file_exists(self, pattern, imagefile):
        exist = re.search(pattern, imagefile)
        return exist

    def stiching(self, metaData, savingDir):
        prefix = "type=[Grid: snake by rows] order=[Right & Down                ] grid_size_x=" + str(
            metaData["num_X_tiles"]) + " grid_size_y=" + str(metaData[
                                                                 "num_Y_tiles"]) + " tile_overlap=30 first_file_index_i=001 directory=" + savingDir + " file_names=tile_{iii}.tif output_textfile_name=TileConfiguration.txt "
        suffix = "fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 compute_overlap computation_parameters=[Save memory (but be slower)] image_output=[Fuse and display]"
        IJ.run("Grid/Collection stitching", prefix + suffix)
    def process(self):
        dir = self.inputdir
        if os.listdir(dir):
            for image_file in os.listdir(dir):
                if image_file.endswith(self.czi_ext) and not(self.shading_file_exists(".*shading.*", image_file)):
                    imagefile = os.path.join(dir, image_file)
                    IJ.log("Current File: " + imagefile)
                    omeMeta = self.get_omemeta(imagefile)
                    self.set_prefs(stitchtiles=False, attach=False)
                    options = self.set_import_options(imagefile)
                    imps = BF.openImagePlus(options)
                    tilefileID = os.path.basename(imps[0].getTitle())
                    tilefileID_strings = os.path.splitext(tilefileID)[0]
                    fileID = tilefileID_strings.split(self.czi_ext + " - ")[1].replace(" ", "_")
                    IJ.log(fileID)
                    savingDir = os.path.join(self.outputdir, fileID)
                    if not os.path.exists(savingDir):
                        os.makedirs(savingDir)
                    metaData = self.get_meta(omeMeta, imps, fileID)
                    shadingfile = ""
                    for im_file in os.listdir(dir):
                        if im_file.endswith(self.czi_ext) and self.shading_file_exists(".*shading.*", im_file) and self.shading_file_exists(str(metaData["date"]) + ".*", im_file):
                            shadingfilepath = os.path.join(dir, im_file)
                            options = self.set_import_options(shadingfilepath)
                            shadingfile = BF.openImagePlus(options)
                    IJ.log("Current Shading File: " + str(shadingfile[0]))
                    for i, imp in enumerate(imps):
                        if shadingfile != "":
                            imp_res = ImageCalculator().run("Subtract create stack", imp, shadingfile[0])
                        else:
                            imp_res = imp
                        tile_name = "tile_" + str(i + 1).zfill(3) + self.tif_ext
                        IJ.log("Saving " + tile_name + " under " + savingDir)
                        FileSaver(imp_res).saveAsTiff(os.path.join(savingDir, tile_name))
                        IJ.log("Saving :  Ends at " + str(time.time()))
                        IJ.run("Close All")
                    self.stiching(metaData, savingDir)
                    res = WindowManager.getCurrentImage()
                    self.removeAllTemps(savingDir)
                    self.save_singleplanes(res, savingDir, metaData, format='tiff')
                    txt_filename = "infos.txt"
                    if os.path.exists(os.path.join(dir, txt_filename)):
                        with open(os.path.join(dir, txt_filename)) as f:
                            if not metaData["date"] in f.read():
                                self.write_infos_txt(metaData, dir)
                    else:
                        self.write_infos_txt(metaData, dir)
                    meta_filename = "metadata.txt"
                    if os.path.exists(os.path.join(dir, meta_filename)):
                        with open(os.path.join(dir, meta_filename)) as f:
                            if not metaData["date"] in f.read():
                                self.write_metadata_txt(metaData, dir)
                    else:
                        self.write_metadata_txt(metaData, dir)
                    res.changes = False
                    res.close()
                else:
                    IJ.log("Error, cannot find any czi file")
                # clear memory
                System.gc()
                # Set the preferences in the ImageJ plugin back to default
                self.set_prefs(stitchtiles=True, attach=True)
            # Save the log file
            IJ.selectWindow("Log")
            thisFile = os.path.join(dir, "Log.txt")
            IJ.saveAs("Text", thisFile)
        else:
            print("Directory is empty. There are no czi files")