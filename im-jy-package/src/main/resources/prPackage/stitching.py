# -*- coding: utf-8 -*-
import os
import time
import sys
from ij import IJ, ImagePlus, ImageStack, Prefs, WindowManager
from ij.process import ImageConverter
from ij.plugin import ImagesToStack, HyperStackConverter
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
import csv
import logging
from loci.formats.in import DynamicMetadataOptions
sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
import shutil
import config
# im-jy-package.stiching.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.STITCHING')


class stitchingTools:
    def __init__(self, inputdir, outputdir, workingdir, czi_ext, tif_ext, infos_txt, metadata_csv_file, no_shading_file, shading_word, TIFF_ext, forceSave):
        self.inputdir = inputdir
        self.outputdir = outputdir
        self.workingdir = workingdir
        self.czi_ext = czi_ext
        self.tif_ext = tif_ext
        self.no_shading_file = no_shading_file
        self.infos_txt = infos_txt
        self.metadata_csv_file = metadata_csv_file
        self.shading_word = shading_word
        self.TIFF_ext=TIFF_ext
        self.force_save = int(forceSave[0])
        self.tempfile = os.path.join(self.workingdir, "temp_stitch.csv")

    def getImageSeries(self, imps, series=0):

        try:
            imp = imps[series]
            pylevelout = series
        except:
            # fallback option
            logger.exception('PyLevel = ' + str(series) + ' does not exist.\nUsing Pyramid Level = 0 as fallback.')
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

    def save_singleplanes(self, imp, savepath, metainfo, filename, format='tiff', selected_resolution='original'):
        stack = imp.getImageStack()
        for s in range(1, stack.size() + 1):
            slicetitle = metainfo["fileID"] + "_" + metainfo["channel " + str(s)] + "." + format
            endfilename = filename + "_" + metainfo["channel " + str(s)] + "." + format
            stackindex = s
            aframe = ImagePlus(slicetitle, imp.getStack().getProcessor(stackindex))
            if selected_resolution =="8-bit":
                ImageConverter(aframe).convertToGray8()
            elif selected_resolution =="16-bit":
                ImageConverter(aframe).convertToGray16()
            elif selected_resolution =="32-bit":
                ImageConverter(aframe).convertToGray32()
            aframe.updateAndDraw()
            outputpath = ht.correct_path(savepath, endfilename)
            IJ.saveAs(aframe, self.TIFF_ext, outputpath)

    def removeAllTemps(self, directory, keep_dirs=None, keep_files=None):
        """
        Remove all files/folders in directory except those listed
        """

        keep_dirs = set(keep_dirs or [])
        keep_files = set(keep_files or [])
        for name in os.listdir(directory):
            path = os.path.join(directory, name)

            if os.path.isdir(path) and name in keep_dirs:
                continue
            if os.path.isfile(path) and name in keep_files:
                continue

            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    logger.info("Removed folder: %s" % path)
                else:
                    os.remove(path)
                    logger.info("Removed file: %s" % path)
            except Exception as e:
                logger.error("Could not remove %s: %s", path, str(e))

    def write_infos_txt(self, metainfo, savingpath):
        date = metainfo["date"]
        if not os.path.exists(savingpath):
            f = open(savingpath, "w")
            f.write(str(date))
        else:
            f = open(savingpath, "a")
            f.write("\n" + str(date))
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + metainfo["channel " + str(channel + 1)])  # "c" + str(channel))
        f.close()

    def get_meta(self, xml_meta, imps, file_id, options, default_channels, image_id=0, instrumentIndex=0, objectiveIndex=0):
        metaData = {}
        metaData["fileID"] = file_id
        file_id_strings = file_id.split("_")
        metaData["date"] = file_id_strings[0]
        metaData["expID"] = "_".join(file_id_strings[1:])
        metaData["channelsNumber"] = xml_meta.getChannelCount(image_id)
        metaData["defaultChannelsNumber"] = len(default_channels)
        # read dimensions XYZ from OME metadata
        metaData["xCoordinate"] = xml_meta.getPlanePositionX(image_id, 0)
        metaData["yCoordinate"] = xml_meta.getPlanePositionY(image_id, 0)
        metaData["zCoordinate"] = xml_meta.getPlanePositionZ(image_id, 0)
        # read dimensions TZCXY from OME metadata
        metaData["DimensionsOrder"] = xml_meta.getPixelsDimensionOrder(image_id).getValue()
        metaData["SizeT"] = xml_meta.getPixelsSizeT(image_id).getValue()
        metaData["SizeZ"] = xml_meta.getPixelsSizeZ(image_id).getValue()
        metaData["SizeC"] = xml_meta.getPixelsSizeC(image_id).getValue()
        metaData["SizeX"] = xml_meta.getPixelsSizeX(image_id).getValue()
        metaData["SizeY"] = xml_meta.getPixelsSizeY(image_id).getValue()
        metaData["PhysicalSizeX"] = xml_meta.getPixelsPhysicalSizeX(image_id).value()
        metaData["PhysicalSizeY"] = xml_meta.getPixelsPhysicalSizeY(image_id).value()
        # read channels from OME metadata
        #for channel in range(metaData["channelsNumber"]):
        for i in range(metaData["defaultChannelsNumber"]):
            if i<metaData["channelsNumber"]:
                metaData["channel " + str(i + 1)] = xml_meta.getChannelName(image_id, i)
            else:
                metaData["channel " + str(i + 1)] = ""
        for i in range(metaData["defaultChannelsNumber"]):
            if i < metaData["channelsNumber"]:
                if "DAPI" in metaData["channel " + str(i + 1)]:
                    metaData["marker for channel " + str(i + 1)] = "0dapi"
                else:
                    metaData["marker for channel " + str(i + 1)] = ""

        # read
        _, slices, metaData["widthTile"], metaData["heightTile"], pylevelout = self.getImageSeries(imps)
        metaData["num_X_tiles"] = (metaData["SizeX"] + metaData["widthTile"] - 1) // metaData["widthTile"]
        metaData["num_Y_tiles"] = (metaData["SizeY"] + metaData["heightTile"] - 1) // metaData["heightTile"]
        metaData["number_of_tiles"] = (len(imps))

        try:
            metaData["ObjectiveModel"] = xml_meta.getObjectiveModel(instrumentIndex, objectiveIndex)
            metaData["ObjectiveNominalMagnification"] = xml_meta.getObjectiveNominalMagnification(instrumentIndex,
                                                                                                  objectiveIndex)
        except:
            # fallback option
            logger.exception('Data about the objective and magnification do not exist.\nSet Data about the objective to -')
            metaData["ObjectiveModel"] = '-'
            metaData["ObjectiveNominalMagnification"] = '-'
        process = ImportProcess(options)
        process.execute()
        ome_meta = process.getOriginalMetadata()
        metaString = ome_meta.getMetadataString("\t")
        Dict = dict((x.strip(), y.strip())
                    for x, y in ([element.split('\t')[0], ', '.join(element.split('\t')[1:])]
                                 for element in metaString.split('\n')))
        exposure_time_values = {}
        default_channels_current = []
        for item in Dict:
            if "Information|Image|Channel|ExposureTime #" in item:
                channel = int(item.split("#", 1)[1])
                #metaData[item + " " + metaData["channel " + str(channel)]]
                exposure_time_values[metaData["channel " + str(channel)]]=float(
                    Dict[item]) / 1000000  # Dividing by 1000000 to get the values in ms
            elif "Experiment|HardwareSettingsPool|HardwareSetting|Name #" in item:
                default_channels_current.append(self.extract_substring_surrounded_by_brachets(Dict[item])[0])
                #metaData[item]
        default_channels_current=list(set(default_channels_current))

        for channel in range(len(default_channels)):
            if channel < len(default_channels_current):
                channel_name = default_channels_current[channel]
            else:
                channel_name =""

            metaData["DefaultChannel #" + str(channel + 1)] = channel_name
        for i, channel in enumerate(default_channels):
            if channel in exposure_time_values:
                metaData["ExposureTime #" + str(i + 1) + " " + str(default_channels[i])] = exposure_time_values[channel]
            else:
                metaData["ExposureTime #" + str(i + 1) + " " + str(default_channels[i])] = ""
        return metaData

    def extract_substring_surrounded_by_brachets(self, string):
        substrings = []
        in_brackets = False
        current_substring = ""
        for c in string:
            if c == "[":
                in_brackets = True
            elif c == "]" and in_brackets:
                substrings.append(current_substring)
                current_substring = ""
                in_brackets = False
            elif in_brackets:
                current_substring += c
        if current_substring:
            substrings.append(current_substring)
        comma_separated_substrings = []
        for substring in substrings:
            if "," in substring:
                comma_separated_substrings=comma_separated_substrings + substring.split(",")
                substrings.remove(substring)
        substrings = substrings + comma_separated_substrings
        return substrings

    def get_meta_not_stiched(self, metaData, xml_meta, positions_not_to_exclude=None):
        if positions_not_to_exclude is None:
            positions_not_to_exclude = []

        imageCount = xml_meta.getImageCount()
        coordinates = {}

        # --- 1. Collect ABSOLUTE stage coordinates ---
        if positions_not_to_exclude:
            for i, position in enumerate(positions_not_to_exclude):
                x = xml_meta.getPlanePositionX(position, 0).value()
                y = xml_meta.getPlanePositionY(position, 0).value()
                coordinates[i] = [x, y]
        else:
            for i in range(imageCount):
                x = xml_meta.getPlanePositionX(i, 0).value()
                y = xml_meta.getPlanePositionY(i, 0).value()
                coordinates[i] = [x, y]

        # --- 2. Convert stage microns to PIXELS ---
        px_size_x = metaData["PhysicalSizeX"]
        px_size_y = metaData["PhysicalSizeY"]

        for k in coordinates:
            coordinates[k][0] = coordinates[k][0] / px_size_x
            coordinates[k][1] = coordinates[k][1] / px_size_y

        return coordinates

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
            f.write("\n" + metainfo["channel " + str(channel + 1)])  # "c" + str(channel))
        f.write("\n" + "ExposureTimes:")
        for channel in range(metainfo["channelsNumber"]):
            f.write("\n" + "Channel " + str(channel + 1) + ": " + str(metainfo[
                                                                          "Information|Image|Channel|ExposureTime #" + str(
                                                                              channel + 1)]))
        f.write("\n" + "Objective: " + str(metainfo["ObjectiveModel"]))
        f.write("\n" + "Objective Magnification: " + str(metainfo[["ObjectiveNominalMagnification"]]))
        f.close()

    def make_dict(self, metainfo, filename, csv_list):
        metainfo["expID"]= "_".join(filename.split("_")[1:])
        len_default_channels = 0
        for key in metainfo:
            if "DefaultChannel #" in key:
                len_default_channels += 1
        fields = ['date', 'expID', 'channelsNumber', 'defaultChannelsNumber'] + ["channel " + str(channel + 1) for channel in
                                                        range(metainfo['defaultChannelsNumber'])] +["marker for channel " + str(channel + 1) for channel in
                                      range(metainfo['defaultChannelsNumber'])] + [
                     "ExposureTime #" + str(channel + 1) + " " + metainfo["DefaultChannel #" + str(channel + 1)] for channel in
                     range(metainfo['defaultChannelsNumber'])] + \
                 ["ObjectiveModel", "ObjectiveNominalMagnification"] + [
            "DefaultChannel #" + str(default_channel + 1) for default_channel in range(len_default_channels)] + ['SizeX', 'SizeY']

        csv_dict = {}
        for item in fields:
            if item in list(metainfo.keys()):
                csv_dict[item] = metainfo[item]
        csv_list.append(csv_dict)
        return csv_list

    def write_metadata_csv(self, csv_dict_list, saving_dir):
        p = ht.correct_path(saving_dir, self.metadata_csv_file)
        csv_dict_list_update = []
        for item in csv_dict_list:
            csv_dict_update = {}
            for key in item:
                if key != "channelsNumber":
                    csv_dict_update[key] = item[key]
            csv_dict_list_update.append(csv_dict_update)
        len_default_channels = 0
        for key in csv_dict_list[0]:
            #if "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" in key:
            if "DefaultChannel #" in key:
                len_default_channels += 1
        fields = ['date', 'expID'] + ["channel " + str(channel + 1) for channel in
                                      range(csv_dict_list[0]['defaultChannelsNumber'])] +["marker for channel " + str(channel + 1) for channel in
                                      range(csv_dict_list[0]['defaultChannelsNumber'])] + [
                     "ExposureTime #" + str(channel + 1) + " " + csv_dict_list[0]["DefaultChannel #" + str(channel + 1)] for channel in
                     range(csv_dict_list[0]['defaultChannelsNumber'])] + [
                     "ObjectiveModel", "ObjectiveNominalMagnification"] + [
        "DefaultChannel #" + str(default_channel + 1) for default_channel in range(len_default_channels)] + ['SizeX', 'SizeY']

        #                 range(csv_dict_list[0]['channelsNumber'])] + [
        # "Information|Image|Channel|ExposureTime #" + str(channel + 1) + " " + csv_dict_list[0][
        # "channel " + str(channel + 1)] for channel in range(csv_dict_list[0]['channelsNumber'])] +[\
        # "Experiment|AcquisitionBlock|RegionsSetup|TilesSetup|MultiTrackSetup|Track|Channel|AdditionalDyeInformation|ShortName #" + str(
        #    default_channel + 1) for default_channel in range(len_default_channels)]
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
    def write_tile_configuration_file(self, tile_name, coordinates, savingDir):

        """
        Writes TileConfiguration.txt in floating-point format
        """
        savepath = ht.correct_path(savingDir, "TileConfiguration.txt")

        # Check if file exists
        new_file = not os.path.exists(savepath)

        f = open(savepath, "a")

        # Write header once
        if new_file:
            f.write("# Define the number of dimensions we are working on\n")
            f.write("dim = 2\n\n")
            f.write("# Define the image coordinates\n")

        # Write tile line with full precision (no rounding)
        x = float(coordinates[0])
        y = float(coordinates[1])
        line = "%s; ; (%.6f, %.6f)\n" % (tile_name, x, y)
        f.write(line)

        f.close()

    def set_prefs(self, stitchtiles, attach):
        # Set the preferences in the ImageJ plugin
        # Although these preferences are applied, they are not refreshed in the UI
        Prefs.set("bioformats.zeissczi.allow.autostitch", str(stitchtiles).lower())
        Prefs.set("bioformats.zeissczi.include.attachments", str(attach).lower())

    def set_import_options(self, image_file, openAllSeries=True, showOMEXML=False, stichTiles=False,
                           stackFormat="Standard ImageJ", colorMode="Default", stackOrder="Default"):
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

    def get_omemeta_no_stitching(self, image_file):
        czireader = ZeissCZIReader()
        czi_options = DynamicMetadataOptions()
        czi_options.setBoolean("zeissczi.autostitch", False)
        czi_options.setBoolean("zeissczi.attachments", False)
        czireader.setMetadataOptions(czi_options)
        omeMeta = MetadataTools.createOMEXMLMetadata()
        czireader.setMetadataStore(omeMeta)
        czireader.setId(image_file)
        czireader.close()
        return omeMeta

    def shading_file_exists(self, pattern, imagefile):
        exist = re.search(pattern, imagefile)
        return exist

    def stitching(self, savingDir):
        prefix = "type=[Positions from file] order=[Defined by TileConfiguration] directory=[" + savingDir + "] layout_file=TileConfiguration.txt "
        suffix = (
                 "fusion_method=[Linear Blending] "
                 + "regression_threshold=0.10 "
                 + "max/avg_displacement_threshold=2.50 "
                 + "absolute_displacement_threshold=3.50 "
                 + "compute_overlap subpixel_accuracy "
                 + "computation_parameters=[Save computation time (but use more RAM)] "
                 + "image_output=[Fuse and display] "
        )
        logger.info("Running stitching...")
        IJ.run("Grid/Collection stitching", prefix + suffix)
        logger.info("Stitching finished. Checking output directory: %s" % savingDir)

    def setting_default_channels(self, options):
        process = ImportProcess(options)
        process.execute()
        ome_meta = process.getOriginalMetadata()
        metaString = ome_meta.getMetadataString("\t")
        Dict = dict((x.strip(), y.strip())
                    for x, y in ([element.split('\t')[0], ', '.join(element.split('\t')[1:])]
                                 for element in metaString.split('\n')))
        default_channels = []
        for item in Dict:
            if "Experiment|HardwareSettingsPool|HardwareSetting|Name #" in item:
                default_channels.append(self.extract_substring_surrounded_by_brachets(Dict[item])[0])
        default_channels=list(set(default_channels))
        return default_channels
    def setting_series(self, options):
        process = ImportProcess(options)
        process.execute()
        ome_meta = process.getOriginalMetadata()
        metaString = ome_meta.getMetadataString("\t")
        Dict = dict((x.strip(), y.strip())
                    for x, y in ([element.split('\t')[0], ', '.join(element.split('\t')[1:])]
                                 for element in metaString.split('\n')))
        scenes_counter = 0
        for item in Dict:
            if "Information|Image|S|Scene|Index" in item:
                scenes_counter = scenes_counter + 1
        scenes = []
        series = []
        for item in Dict:
            if "Positions|Series" in item:
                temp = item.split("Positions|Series", 1) [1]
                temp=temp.split("|",1)[0]
                series.append(temp)
                scenes.append(Dict[item])
        tiles_in_scenes ={}
        for i in range(scenes_counter):
            seriesinINscene = []
            for j, scene in enumerate(scenes):
                if int(scene) == i:
                    seriesinINscene.append(int(series[j]))
            tiles_in_scenes[i] = list(set(seriesinINscene))
        series_not_to_exclude=list(set([int(i)-1 for i in series]))
        return scenes_counter, tiles_in_scenes, series_not_to_exclude

    def shadowCorrection(self, imp, shadingfile, metaData_imp, metaData_shadingFile):
        """
        Per-slice shading subtraction
        """

        stack_shadingfile = shadingfile.getImageStack()
        stack_imp = imp.getImageStack()

        # Extract channel order from metadata
        channels_imp = [metaData_imp["channel " + str(i)] for i in range(1, stack_imp.size() + 1)]
        channels_shadingfile = [metaData_shadingFile["channel " + str(i)] for i in range(1, stack_shadingfile.size() + 1)]

        shadowcorrected = []

        # Loop through channels in order
        for imp_stackindex in range(len(channels_imp)):
            if channels_imp[imp_stackindex] in channels_shadingfile:
                shadingfile_stackindex = channels_shadingfile.index(channels_imp[imp_stackindex])
                aframe = ImagePlus(channels_imp[imp_stackindex], imp.getStack().getProcessor(imp_stackindex+1))
                bframe = ImagePlus(channels_shadingfile[shadingfile_stackindex], shadingfile.getStack().getProcessor(shadingfile_stackindex+1))
                imp_res = ImageCalculator().run("Subtract create", aframe, bframe)
            else:
                imp_res = ImagePlus(channels_imp[imp_stackindex], imp.getStack().getProcessor(imp_stackindex+1))
            shadowcorrected.append(imp_res)

        # --- Build stack in correct channel order ---
        if not shadowcorrected:
            return imp

        stack = ImagesToStack.run(shadowcorrected)

        # --- Hyperstack reconstruction ---
        res_stack = HyperStackConverter.toHyperStack(
                  stack,
                  metaData_imp["SizeC"],
                  metaData_imp["SizeZ"],
                  metaData_imp["SizeT"],
                  metaData_imp["DimensionsOrder"],
                  "Grayscale"
        )
        return res_stack

    def process(self):
        """
          - read CSV with user's choices
          - separate CZI image files from shading CZIs
          - (optionally) apply shading correction per tile
          - write tiles, stitch (if >1), export stitched outputs for post-steps
          - write metadata CSV
        """
        logger.info("Current IMAGEJ version: " + IJ.getVersion())

        # --- 0) Check CSV with stitching parameters ---
        if not os.path.exists(self.tempfile):
            logger.warning(
                "No csv file was found. The user may have cancelled the stitching parameter dialog. Doing nothing.")
            return

        try:
            data = ht.read_data_from_csv(self.tempfile)
        except Exception:
            logger.exception("Could not get the input parameters from CSV. Exiting.")
            return

        if not data:
            logger.warning("CSV with stitching parameters is empty. Doing nothing.")
            return

        # --- 1) Collect selected files, resolutions, shading file info ---

        def _dedupe_preserve_order(seq):
            seen = {}
            out = []
            for x in seq:
                if x not in seen:
                    seen[x] = True
                    out.append(x)
            return out

        selected_files_flat = []
        selected_resolutions = []
        shading_files = {}  # date -> shading file string (as in CSV)

        for case in data:
            try:
                sel = case['selected_files']
                if sel:
                    parts = [p.strip() for p in sel.split(";") if p.strip()]
                    selected_files_flat.extend(parts)
                selected_resolutions.append(case.get('resolution', 'original'))
                shading_files[str(case["date"])] = case['selected_shading_file']
            except Exception:
                logger.exception("Malformed CSV row: " + repr(case))

        selected_files_flat = _dedupe_preserve_order(selected_files_flat)
        if not selected_files_flat:
            logger.warning("No selected files in CSV. Doing nothing.")
            return

        unique_res = _dedupe_preserve_order(selected_resolutions)
        if unique_res:
            selected_resolution = unique_res[0]
            if len(unique_res) > 1:
                logger.warning("Multiple resolutions in CSV: " + str(unique_res) +
                               ". Using first one: " + selected_resolution)
        else:
            selected_resolution = 'original'

        # --- 2) Validate input directory ---
        if not (self.inputdir and os.path.isdir(self.inputdir)):
            logger.warning("Input directory is missing or not a directory: " + str(self.inputdir))
            return

        # --- 3) Split selected files into CZI images vs shading CZIs ---

        czi_paths = []
        shading_file_paths = []

        for file_path in selected_files_flat:
            if not file_path:
                continue
            filename = os.path.basename(file_path)
            if not filename.endswith(self.czi_ext):
                continue

            # Treat as shading if:
            #  - filename matches any shading_files[...] entry (substring match)
            #  - OR filename contains config.shading_word (if available)
            is_shading = False
            try:
                if config.shading_word and config.shading_word in filename.lower():
                    is_shading = True
            except Exception:
                pass

            if not is_shading:
                # Check against shading_files values
                for v in shading_files.values():
                    if filename in str(v):
                        is_shading = True
                        break

            if is_shading:
                shading_file_paths.append(file_path)
            else:
                czi_paths.append(file_path)

        czi_paths.sort()
        shading_file_paths.sort()

        if not czi_paths:
            logger.warning("No CZI image files to process after filtering. Nothing to do.")
            return

        # --- 4) Determine default channels once by scanning CZI files ---
        default_channels = []

        for image_file_path in czi_paths:
            try:
                self.set_prefs(stitchtiles=False, attach=False)
                img_options = self.set_import_options(image_file_path)
                chs = self.setting_default_channels(img_options)
                for ch in chs:
                    if ch not in default_channels:
                        default_channels.append(ch)
            except Exception:
                logger.exception("Error while probing default channels for: " + image_file_path)

        # --- 5) Main loop over CZI files ---
        csv_data = []

        for file_index, image_file_path in enumerate(czi_paths):
            imps = None
            shading_imps = None

            try:
                logger.info("Current CZI File: " + image_file_path)

                omeMeta = self.get_omemeta(image_file_path)

                # use separate options objects for image and shading
                self.set_prefs(stitchtiles=False, attach=False)
                img_options = self.set_import_options(image_file_path)
                omeMeta_no_stitch = self.get_omemeta_no_stitching(image_file_path)

                imps = BF.openImagePlus(img_options)
                if not imps or len(imps) == 0:
                    logger.error("No images returned by Bio-Formats for: " + image_file_path)
                    continue

                # Derive fileID
                tilefileID = os.path.basename(imps[0].getTitle())
                tilefileID_strings = os.path.splitext(tilefileID)[0]
                if len(imps) == 1:
                    fileID = tilefileID_strings.split(self.czi_ext + " - ")[0].replace(" ", "_")
                else:
                    parts = tilefileID_strings.split(self.czi_ext + " - ")
                    if len(parts) > 1:
                        fileID = parts[1].replace(" ", "_")
                    else:
                        fileID = tilefileID_strings.replace(" ", "_")

                metaData = self.get_meta(omeMeta, imps, fileID, img_options, default_channels)

                scenesnumber, scenes_tiles, series_not_to_exclude = self.setting_series(img_options)

                # Pick shading CZI for this CZI (if any)
                shadingfile = self.no_shading_file
                shadingfilepath = ""
                shading_options = None

                try:
                    current_date_key = str(metaData["date"])
                    if current_date_key in shading_files:
                        wanted = shading_files[current_date_key]
                        for shading_file_path in shading_file_paths:
                            shading_file = os.path.basename(shading_file_path)
                            if shading_file in str(wanted):
                                shadingfilepath = shading_file_path
                                break
                except Exception:
                    logger.exception("Error matching shading file by date for: " + image_file_path)

                if shadingfilepath:
                    try:
                        shading_options = self.set_import_options(shadingfilepath)
                        shading_imps = BF.openImagePlus(shading_options)
                        shadingfile = shading_imps
                        logger.info("Current Shading File: " + shadingfilepath)
                    except Exception:
                        logger.exception("Could not open shading file: " + shadingfilepath)
                        shadingfile = self.no_shading_file
                        shading_imps = None
                        shading_options = None
                else:
                    logger.info("Current Shading File: " + str(shadingfile))

                # Precompute shading metadata ONCE per CZI
                omeMeta_shadingFile = None
                metaData_shadingFile = None
                if shadingfile != self.no_shading_file and shading_imps:
                    try:
                        omeMeta_shadingFile = self.get_omemeta(shadingfilepath)
                        metaData_shadingFile = self.get_meta(
                            omeMeta_shadingFile,
                            shading_imps,
                            shadingfilepath,
                            shading_options,
                            default_channels
                        )
                    except Exception:
                        logger.exception("Could not compute shading metadata; tiles will be uncorrected.")
                        shadingfile = self.no_shading_file
                        omeMeta_shadingFile = None
                        metaData_shadingFile = None

                # --- Process per scene ---
                if scenesnumber >= 1:
                    for scene in range(scenesnumber):
                        if scene not in scenes_tiles:
                            continue

                        # Scene-specific file name
                        if scenesnumber == 1:
                            filename = fileID
                        else:
                            filename = fileID + "-scene-" + str(scene)

                        savingDir = ht.correct_path(self.outputdir, filename)
                        outputDir = ht.correct_path(savingDir, "stitched_output")

                        if not os.path.exists(savingDir):
                            os.makedirs(savingDir)
                        if not os.path.exists(outputDir):
                            os.makedirs(outputDir)

                        # Clean temp content before new tiles
                        if os.listdir(savingDir):
                            try:
                                self.removeAllTemps(savingDir)
                            except Exception:
                                logger.exception("removeAllTemps failed for: " + savingDir)

                        # Precompute coordinates ONCE per scene
                        scene_positions = scenes_tiles[scene]
                        coordinates = None
                        if len(scene_positions) > 1:
                            try:
                                positions_zero_based = [pos - 1 for pos in scene_positions]
                                coordinates = self.get_meta_not_stiched(
                                    metaData,
                                    omeMeta_no_stitch,
                                    positions_zero_based
                                )
                            except Exception:
                                logger.exception("get_meta_not_stiched failed for scene " + str(scene))
                                coordinates = None
                        # --- Tile loop ---
                        for i, tile in enumerate(scene_positions):
                            try:
                                imp = imps[tile - 1]

                                # Apply shading correction if available
                                if shadingfile != self.no_shading_file and metaData_shadingFile is not None:
                                    imp_res = self.shadowCorrection(
                                        imp,
                                        shadingfile[0],
                                        metaData,
                                        metaData_shadingFile
                                    )
                                else:
                                    imp_res = imp

                                tile_name = "tile_" + str(i + 1).zfill(3) + self.tif_ext
                                tile_path = ht.correct_path(savingDir, tile_name)
                                logger.info("Saving " + tile_name + " under " + savingDir)
                                FileSaver(imp_res).saveAsTiff(tile_path)

                                # Write coordinates if available (stitched case)
                                if coordinates is not None and i < len(coordinates):
                                    try:
                                        self.write_tile_configuration_file(
                                            tile_name,
                                            coordinates[i],
                                            savingDir
                                        )
                                    except Exception:
                                        logger.exception("Failed writing TileConfiguration for " + tile_name)

                            except Exception:
                                logger.exception(
                                    "Tile export failed (scene " + str(scene) + ", tile " + str(tile) + ").")
                        # Close all windows once per scene
                        try:
                            IJ.run("Close All")
                        except Exception:
                            pass

                        # Stitch if multiple tiles, or just reopen single tile
                        res = None
                        try:
                            if len(scene_positions) > 1:
                                self.stitching(savingDir)
                                res = WindowManager.getCurrentImage()
                            else:
                                single_tile = ht.correct_path(savingDir, "tile_" + str(1).zfill(3) + self.tif_ext)
                                if os.path.exists(single_tile):
                                    res = IJ.openImage(single_tile)
                        except Exception:
                            logger.exception("Stitching failed for: " + savingDir)
                            res = None

                        # Clean temp but keep stitched_output
                        try:
                            self.removeAllTemps(savingDir, keep_dirs=["stitched_output"])
                        except Exception:
                            logger.exception("removeAllTemps (keep stitched_output) failed for: " + savingDir)

                        # Convert stitched outputs for further processing
                        try:
                            self.save_singleplanes(
                                res,
                                savingDir,
                                metaData,
                                filename,
                                'tif',
                                selected_resolution,
                            )
                        except Exception:
                            logger.exception("convert_and_save_output_images_for_further_process failed for: " + filename)

                        # Collect metadata row
                        try:
                            csv_data = self.make_dict(metaData, filename, csv_data)
                        except Exception:
                            logger.exception("make_dict failed for: " + filename)

                        # Close result image if any
                        try:
                            if res is not None:
                                res.changes = False
                                res.close()
                        except Exception:
                            pass

                else:
                    logger.error("CZI file appears damaged or has zero scenes: " + image_file_path)

            except Exception:
                logger.exception("Fatal error while processing: " + image_file_path)

            finally:
                # Close imported images to free memory
                try:
                    if imps:
                        for _imp in imps:
                            try:
                                _imp.close()
                            except Exception:
                                pass
                except Exception:
                    pass

                try:
                    if shading_imps:
                        for _s in shading_imps:
                            try:
                                _s.close()
                            except Exception:
                                pass
                except Exception:
                    pass

                # Limit garbage collection: every 5 CZI files
                try:
                    if (file_index + 1) % 5 == 0:
                        System.gc()
                except Exception:
                    pass

                # Reset prefs back for next loop
                try:
                    self.set_prefs(stitchtiles=True, attach=True)
                except Exception:
                    pass

        # --- 6) Write metadata CSV once at the end ---
        try:
            if csv_data:
                self.write_metadata_csv(csv_data, self.workingdir)
                logger.info("Metadata CSV written under: " + str(self.workingdir))
            else:
                logger.warning("No metadata rows were generated; CSV not written.")
        except Exception:
            logger.exception("Failed writing metadata CSV.")
