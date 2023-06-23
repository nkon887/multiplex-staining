import os
import time
import sys
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
from loci.plugins. in import ImportProcess
from ij.gui import GenericDialog
import csv
import logging
sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht

# stiching.py creates its own logger, as a sub logger to 'pipelineGUI.macro.main.STITCHING'
logger = logging.getLogger('pipelineGUI.macro.main.STITCHING')
class stitchingTools:
    def __init__(self, inputdir, outputdir, workingdir, czi_ext, tif_ext, infos_txt, no_shading_file):
        self.inputdir = inputdir
        self.outputdir = outputdir
        self.workingdir= workingdir
        self.czi_ext = czi_ext
        self.tif_ext = tif_ext
        self.no_shading_file = no_shading_file
        self.infos_txt = infos_txt
    def getting_input_parameters(self):
        gui = GenericDialog("Shading Correction")
        gui.addMessage("Choose the shading correction file for each date you want to use")
        dates = []
        czifiles = [self.no_shading_file]
        dir = os.walk(self.inputdir)
        if dir:
            for path, subdirs, files in dir:
                for name in files:
                    file_path = ht.correct_path(path, name)
                    if name.endswith(self.czi_ext):
                        czifiles.append(os.path.basename(file_path))
        for czifile in czifiles:
            date = czifile[0:6]
            if re.match(r'^\d{6}$', date):
                dates.append(date)
        dates = list(set(dates))
        if dates:
            for date, i in zip(dates, range(0, len(dates))):
                date_filtered_czifiles = [x for x in czifiles if date in x]
                date_filtered_czifiles.insert(0, self.no_shading_file)
                gui.addChoice(date + ":", date_filtered_czifiles, date_filtered_czifiles[0])  # czifiles[2] is default here
                if i % 2 == 0 and date!=dates[len(dates)-1]:
                    gui.addToSameRow()
            gui.showDialog()
            if gui.wasCanceled():
                logger.warning("User canceled dialog! Doing nothing. Exit")
                return
            shading_files = {}
            for date in dates:
                shading_files[date] = gui.getNextChoice()
            return [shading_files]
        else:
            logger.warning("The names of czi files don't have the correct form")
            return
    def getImageSeries(self, imps, series=0):

        try:
            imp = imps[series]
            pylevelout = series
        except:
            # fallback option
            logger.exception('PyLevel = ' + str(series) + ' does not exist.')
            logger.exception('Using Pyramid Level = 0 as fallback.')
            imp = imps[0]
            pylevelout = 0

        # get the stack and some info
        imgstack = imp.getImageStack()
        slices = imgstack.getSize()
        width = imgstack.getWidth()
        height = imgstack.getHeight()

        return imp, slices, width, height, pylevelout
    def renameStack(self, stack_width, stack_height, imp, metainfo):
        logger.info("Setting channel names...")
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
            aframe = ImagePlus(slicetitle, imp.getStack().getProcessor(stackindex))
            outputpath = ht.correct_path(savepath, slicetitle)
            IJ.saveAs(aframe, "TIFF", outputpath)
    def removeAllTemps(self, directory):
        for filename in os.listdir(directory):
            if not filename.endswith(".xml"):
                os.remove(ht.correct_path(directory, filename))
    def write_infos_txt(self, metainfo, savingpath):
        date = metainfo["date"]
        if not os.path.exists(savingpath):
            f = open(savingpath, "w")
            f.write(str(date))
        else:
            f = open(savingpath, "a")
            f.write("\n" + str(date))
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + metainfo["channel " + str(channel + 1)])  #"c" + str(channel))
        f.close()

    def get_meta(self, xml_meta, imps, file_id, options, image_id = 0, instrumentIndex = 0, objectiveIndex = 0):
        metaData = {}
        metaData["fileID"] = file_id
        file_id_strings = file_id.split("_")
        metaData["date"] = file_id_strings[0]
        metaData["expID"] = file_id_strings[1]
        metaData["channelsNumber"] = xml_meta.getChannelCount(image_id)
        # read dimensions XYZ from OME metadata
        metaData["xCoordinate"] = xml_meta.getPlanePositionX(image_id, 0)
        metaData["yCoordinate"] = xml_meta.getPlanePositionY(image_id, 0)
        metaData["zCoordinate"] = xml_meta.getPlanePositionZ(image_id, 0)
        # read dimensions TZCXY from OME metadata
        metaData["SizeT"] = xml_meta.getPixelsSizeT(image_id).getValue()
        metaData["SizeZ"] = xml_meta.getPixelsSizeZ(image_id).getValue()
        metaData["SizeC"] = xml_meta.getPixelsSizeC(image_id).getValue()
        metaData["SizeX"] = xml_meta.getPixelsSizeX(image_id).getValue()
        metaData["SizeY"] = xml_meta.getPixelsSizeY(image_id).getValue()
        # read channels from OME metadata
        for channel in range(metaData["channelsNumber"]):
            metaData["channel " + str(channel + 1)] = xml_meta.getChannelName(image_id, channel)
        # read
        _, slices, metaData["widthTile"], metaData["heightTile"], pylevelout = self.getImageSeries(imps)
        metaData["num_X_tiles"] = (metaData["SizeX"] + metaData["widthTile"] - 1) // metaData["widthTile"]
        metaData["num_Y_tiles"] = (metaData["SizeY"] + metaData["heightTile"] - 1) // metaData["heightTile"]
        metaData["number_of_tiles"] = (len(imps))

        try:
            metaData["ObjectiveModel"] = xml_meta.getObjectiveModel(instrumentIndex, objectiveIndex)
            metaData["ObjectiveNominalMagnification"] = xml_meta.getObjectiveNominalMagnification(instrumentIndex, objectiveIndex)
        except:
            # fallback option
            logger.exception('Data about the objective and magnification do not exist.')
            logger.exception('Set Data about the objective to -')
            metaData["ObjectiveModel"] = '-'
            metaData["ObjectiveNominalMagnification"] = '-'
        process = ImportProcess(options)
        process.execute()
        ome_meta = process.getOriginalMetadata()
        metaString = ome_meta.getMetadataString("\t")
        Dict = dict((x.strip(), y.strip())
                    for x, y in ([element.split('\t')[0], ', '.join(element.split('\t')[1:])]
                                 for element in metaString.split('\n')))
        for item in Dict:
                if "Information|Image|Channel|ExposureTime #" in item:
                    channel = int(item.split("#", 1)[1])
                    metaData[item + " " + metaData["channel " + str(channel)] ]= float(Dict[item]) / 1000000  # Dividing by 1000000 to get the values in ms
                elif "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" in item:
                    metaData[item] = Dict[item]
        return metaData
    def write_metadata_txt(self, metainfo, saving_dir):
        p = ht.correct_path(saving_dir, "metadata.txt")
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
                "Information|Image|Channel|ExposureTime #" + str(channel + 1)]))
        f.write("\n" + "Objective: " + str(metainfo["ObjectiveModel"]))
        f.write("\n" + "Objective Magnification: " + str(metainfo[["ObjectiveNominalMagnification"]]))
        f.close()
    def make_dict(self, metainfo, csv_list):
        len_default_channels = 0
        for key in metainfo:
            if "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" in key:
                len_default_channels +=1
        fields = ['date', 'expID', 'channelsNumber'] + ["channel " + str(channel + 1) for channel in range(metainfo['channelsNumber'])] + [
                "Information|Image|Channel|ExposureTime #" + str(channel + 1) + " " +metainfo["channel " + str(channel + 1)]  for channel in range(metainfo['channelsNumber'])] + ["ObjectiveModel", "ObjectiveNominalMagnification"] + [
                "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" + str(default_channel + 1) for default_channel in range(len_default_channels)]
        csv_dict = {}
        for item in fields:
            if item in list(metainfo.keys()):
                csv_dict[item]=metainfo[item]
        csv_list.append(csv_dict)
        return csv_list
    def write_metadata_csv(self, csv_dict_list, saving_dir):
        p = ht.correct_path(saving_dir, "metadata.csv")
        csv_dict_list_update = []
        for item in csv_dict_list:
            csv_dict_update = {}
            for key in item:
                if key != "channelsNumber":
                    csv_dict_update[key] = item[key]
            csv_dict_list_update.append(csv_dict_update)
        len_default_channels = 0
        for key in csv_dict_list[0]:
            if "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" in key:
                len_default_channels +=1
        fields = ['date', 'expID'] + ["channel " + str(channel + 1) for channel in range(csv_dict_list[0]['channelsNumber'])] + [
                "Information|Image|Channel|ExposureTime #" + str(channel + 1) + " " + csv_dict_list[0]["channel " + str(channel + 1)] for channel in range(csv_dict_list[0]['channelsNumber'])] + ["ObjectiveModel", "ObjectiveNominalMagnification"] + [
                "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" + str(default_channel + 1) for default_channel in range(len_default_channels)]
        with open(p, 'wb') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(csv_dict_list_update)
    def write_meta_xml(self, saving_dir, imps):
        # export the ImgPlus
        savepath = ht.correct_path(saving_dir, r"LOCI.ome.xml")
        paramstring = "outfile=[" + savepath + "] windowless=true compression=Uncompressed saveROI=false"
        plugin = LociExporter()
        plugin.arg = paramstring
        t0 = time.time()
        exporter = Exporter(plugin, imps[0])
        exporter.run()
        t1 = time.time()
        total = t1 - t0
        logger.info("Export complete OME-TIFF using LOCI: {}".format(total))
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
        options.setShowMetadata(True)
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
        # fiji Version
        imagejversion = IJ.getVersion()
        logger.info("Current IMAGEJ version: " + imagejversion)
        try:
            shading_files  = self.getting_input_parameters()[0]
        except:
            logger.exception("Could get not the input shading files. Exiting")
            return
        dir = os.walk(self.inputdir)
        if dir:
            csv_data=[]
            czi_paths=[]
            shading_file_paths = []
            for path, subdirs, files in dir:
                for name in files:
                    file_path = ht.correct_path(path, name)
                    if name.endswith(self.czi_ext) and not name in shading_files.values():
                        czi_paths.append(file_path)
                    elif name.endswith(self.czi_ext) and name in shading_files.values():
                        shading_file_paths.append(file_path)
            for image_file_path in czi_paths:
                    #(self.shading_file_exists(".*shading.*", image_file)):
                    imagefile = image_file_path
                    logger.info("Current CZI File: " + imagefile)
                    omeMeta = self.get_omemeta(imagefile)
                    self.set_prefs(stitchtiles=False, attach=False)
                    options = self.set_import_options(imagefile)

                    imps = BF.openImagePlus(options)
                    tilefileID = os.path.basename(imps[0].getTitle())
                    tilefileID_strings = os.path.splitext(tilefileID)[0]
                    fileID = tilefileID_strings.split(self.czi_ext + " - ")[1].replace(" ", "_")
                    savingDir = ht.correct_path(self.outputdir, fileID)
                    if not os.path.exists(savingDir):
                        os.makedirs(savingDir)
                    metaData = self.get_meta(omeMeta, imps, fileID, options)
                    shadingfile = self.no_shading_file
                    for shading_file_path in shading_file_paths:
                        shading_file = os.path.basename(shading_file_path)
                        if shading_file in shading_files[str(metaData["date"])]:
                            print(shading_file)
                            options = self.set_import_options(shading_file_path)
                            shadingfile = BF.openImagePlus(options)
                    logger.info("Current Shading File: " + str(shadingfile[0]))
                    for i, imp in enumerate(imps):
                        if shadingfile != self.no_shading_file:
                            imp_res = ImageCalculator().run("Subtract create stack", imp, shadingfile[0])
                        else:
                            imp_res = imp
                        tile_name = "tile_" + str(i + 1).zfill(3) + self.tif_ext
                        logger.info("Saving " + tile_name + " under " + savingDir)
                        FileSaver(imp_res).saveAsTiff(ht.correct_path(savingDir, tile_name))
                        logger.info("Saving :  Ends at " + str(time.time()))
                        IJ.run("Close All")
                    self.stiching(metaData, savingDir)
                    res = WindowManager.getCurrentImage()
                    self.removeAllTemps(savingDir)
                    self.save_singleplanes(res, savingDir, metaData, format='tif')
                    txt_filename = self.infos_txt
                    txt_savepath = ht.correct_path(self.outputdir, txt_filename)
                    if os.path.exists(txt_savepath):
                        with open(ht.correct_path(txt_savepath)) as f:
                            if not metaData["date"] in f.read():
                                self.write_infos_txt(metaData, txt_savepath)
                    else:
                        self.write_infos_txt(metaData, txt_savepath)
                    csv_data = self.make_dict(metaData, csv_data)
                    res.changes = False
                    res.close()

            # clear memory
            System.gc()
            # Set the preferences in the ImageJ plugin back to default
            self.set_prefs(stitchtiles=True, attach=True)
            if csv_data:
                self.write_metadata_csv(csv_data, self.workingdir)
            # Save the log file
            #win=WindowManager.getWindow("Log")
            #if win is not None:
                #thisFile = ht.correct_path(self.workingdir, "Log.txt")
                #IJ.selectWindow("Log")
                #IJ.saveAs("Text", thisFile)
            #else:
            #    logger.warning("The Window \"Log\" is not open")
        else:
            logger.warning("Directory is empty. There are no czi files")