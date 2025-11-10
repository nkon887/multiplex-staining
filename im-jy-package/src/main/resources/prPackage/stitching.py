# -*- coding: utf-8 -*-
import os
import time
import sys
from ij import IJ, ImagePlus, ImageStack, Prefs, WindowManager
from ij.process import ImageConverter
from loci.plugins import BF
from loci.plugins. in import ImporterOptions
from loci.formats import MetadataTools
from loci.formats. in import ZeissCZIReader
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
from ij import IJ, ImagePlus
from ij.plugin import ImagesToStack, HyperStackConverter
from ij.process import ByteProcessor, ShortProcessor, FloatProcessor
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

    def removeAllTemps(self, directory, keep_dirs=None, keep_files=None):
        """
        Remove all files/folders in directory except those listed
        """

        import os, shutil

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

        # Do NOT subtract minimums
        # Do NOT shift to 0/0 normalize
        # Keep raw pixel coordinates (may be negative!)

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
        Writes TileConfiguration.txt in Zeiss-compatible floating-point format.
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

    def stitching(self, savingDir, outputDir):
        # Ensure output folder exists
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        prefix = "type=[Positions from file] order=[Defined by TileConfiguration] directory=[" + savingDir + "] layout_file=TileConfiguration.txt "
        suffix = (
                "fusion_method=[Linear Blending] "
                + "regression_threshold=0.10 "
                + "max/avg_displacement_threshold=2.50 "
                + "absolute_displacement_threshold=3.50 "
                + "computation_parameters=[Save computation time (but use more RAM)] "
                + "image_output=[Write to disk] "
                + "output_directory=[" + outputDir + "] "
                + "subpixel_accuracy=true compute_overlap=true "
                + "downsample_tiles=1 " # 1 = full resolution
                + "downsample_images=false " # keep tiles as-is before alignment
                + "save_ij_xml=false "
                + "set_compute_BoundingBox=false compute_full_image=true "
                + "ignore_viewport=true "
        )
        logger.info("Running stitching...")
        IJ.run("Grid/Collection stitching", prefix + suffix)
        logger.info("Stitching finished. Checking output directory: %s" % outputDir)

    def show_output_images_for_further_process(self, outputDir, savepath, metainfo, filename,
                                               format='tiff', selected_resolution='original', res=None):

        # --- CASE 1: outputDir with extension-less stitched images ---
        if res is None:
            files = [f for f in os.listdir(outputDir)
                     if "." not in f and os.path.isfile(os.path.join(outputDir, f))]
            if not files:
                logger.warning("No extension-less stitched output files found in: %s" % outputDir)
                raise SystemExit

            # Sort by channel index if present
            def parse_channel(fname):
                m = re.search(r'_c(\d+)', fname)
                return int(m.group(1)) if m else 0

            files.sort(key=parse_channel)
            logger.info("[INFO] Found stitched outputs: %s" % str(files))

            for s, fname in enumerate(files):
                path = os.path.join(outputDir, fname)
                logger.info("Processing: %s" % path)
                imp = IJ.openImage(path)
                if imp is None:
                    logger.warning("Could not open: %s" % fname)
                    continue

                # --- Convert bit depth if needed ---
                if selected_resolution in ["8-bit", "16-bit", "32-bit"]:
                    IJ.run(imp, selected_resolution, "")

                IJ.run(imp, "Grays", "")

                # ----------------------------------------------------
                # ADD ZEISS FIXED BORDER PADDING
                # Zeiss image is always 5 px wider and 11 px taller
                # Fiji: 18637x23162
                # Zeiss: 18642x23173
                # ----------------------------------------------------
                fiji_w = imp.getWidth()
                fiji_h = imp.getHeight()

                zeiss_w = fiji_w + 5
                zeiss_h = fiji_h + 11

                imp = self.zeiss_pad_fixed(imp, zeiss_w, zeiss_h)
                # ----------------------------------------------------

                # Build save path
                channel_name = metainfo.get("channel " + str(s + 1), "ch" + str(s + 1))
                save_name = filename + "_" + channel_name + "." + format
                save_path = ht.correct_path(savepath, save_name)

                IJ.saveAs(imp, self.TIFF_ext, save_path)
                logger.info("Saved: %s" % save_path)
                imp.close()

            # Remove stitched temp tiles
            try:
                for f in files:
                    fp = os.path.join(outputDir, f)
                    if os.path.exists(fp):
                        os.remove(fp)

                # Remove stitched_output folder
                if os.path.isdir(outputDir):
                    shutil.rmtree(outputDir)

                logger.info("[CLEANUP] Removed stitched_output folder")
            except Exception as e:
                logger.warning("Cleanup failed: %s" % str(e))

            logger.info("Saved stitched TIFFs to: %s" % savepath)
            return



        # --- CASE 2: res (ImagePlus stack) provided ---
        else:
            if selected_resolution != 'original':
                converter = ImageConverter(res)
                if selected_resolution == "8-bit":
                    converter.convertToGray8()
                elif selected_resolution == "16-bit":
                    converter.convertToGray16()
                elif selected_resolution == "32-bit":
                    converter.convertToGray32()

            stack = res.getImageStack()
            num_slices = stack.size()
            logger.info("Processing %d slices individually...", num_slices)

            dr_min = res.getDisplayRangeMin()
            dr_max = res.getDisplayRangeMax()

            for s in range(1, num_slices + 1):
                channel_name = metainfo.get("channel " + str(s), "ch" + str(s))
                slicetitle = metainfo["fileID"] + "_" + channel_name
                endfilename = filename + "_" + channel_name + "." + format
                outputpath = ht.correct_path(savepath, endfilename)

                slice_proc = stack.getProcessor(s)
                aframe = ImagePlus(slicetitle, slice_proc)

                # Apply grayscale and preserve intensity
                IJ.run(aframe, "Grays", "")
                aframe.setDisplayRange(dr_min, dr_max)
                aframe.updateAndDraw()

                IJ.saveAs(aframe, self.TIFF_ext, outputpath)
                logger.info("[OK] Saved slice %d/%d -> %s", s, num_slices, outputpath)
                aframe.close()

            # --- Optional cleanup of temporary folder ---
            if os.path.isdir(outputDir):
                try:
                    shutil.rmtree(outputDir)
                    logger.info("[CLEANUP] Removed temporary folder: %s" % outputDir)
                except Exception as e:
                    logger.warning("Could not delete folder: %s" % str(e))

            logger.info("[DONE] All slices processed and saved separately to: %s" % savepath)

    def zeiss_pad_fixed(self, imp, zeiss_width, zeiss_height):

        w = imp.getWidth()
        h = imp.getHeight()

        pad_w = max(zeiss_width - w, 0)
        pad_h = max(zeiss_height - h, 0)

        if pad_w == 0 and pad_h == 0:
            return imp

        ip = imp.getProcessor()

        if isinstance(ip, ByteProcessor):
            out = ByteProcessor(zeiss_width, zeiss_height)
        elif isinstance(ip, ShortProcessor):
            out = ShortProcessor(zeiss_width, zeiss_height)
        else:
            out = FloatProcessor(zeiss_width, zeiss_height)

        # Insert original at (0,0)
        out.insert(ip, 0, 0)

        return ImagePlus(imp.getTitle(), out)

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
        Zeiss-like shadow (flat-field) correction with clipping.
        Corrected = Raw / (Flat / mean(Flat))
        Automatically clips intensities to image bit depth.
        """

        stack_shadingfile = shadingfile.getImageStack()
        stack_imp = imp.getImageStack()

        # collect channel labels
        channels_shadingfile = [metaData_shadingFile["channel " + str(s)]
                                for s in range(1, stack_shadingfile.size() + 1)]
        channels_imp = [metaData_imp["channel " + str(s)]
                        for s in range(1, stack_imp.size() + 1)]

        # detect bit depth from input image
        bit_depth = imp.getBitDepth()
        if bit_depth == 8:
            max_val = 255
        elif bit_depth == 12:   # rare case: not standard in ImageJ
            max_val = 4095
        elif bit_depth == 16:
            max_val = 65535
        else:
            max_val = float("inf")  # no clipping for float images

        shadowcorrected = []

        for imp_stackindex, channel_name in enumerate(channels_imp):
            raw_ip = stack_imp.getProcessor(imp_stackindex + 1).convertToFloat()

            if channel_name in channels_shadingfile:
                shadingfile_stackindex = channels_shadingfile.index(channel_name)
                flat_ip = stack_shadingfile.getProcessor(shadingfile_stackindex + 1).convertToFloat()

                # mean of flat-field
                stats = ImagePlus("flat", flat_ip).getStatistics()
                mean_flat = stats.mean if stats.mean > 0 else 1.0

                width, height = raw_ip.getWidth(), raw_ip.getHeight()
                corrected_ip = FloatProcessor(width, height)

                # pixelwise correction + clipping
                for y in range(height):
                    for x in range(width):
                        f_val = flat_ip.getf(x, y)
                        r_val = raw_ip.getf(x, y)
                        if f_val > 0:
                            val = r_val / (f_val / mean_flat)
                        else:
                            val = 0
                        # clip
                        if val < 0:
                            val = 0
                        elif val > max_val:
                            val = max_val
                        corrected_ip.setf(x, y, val)

                imp_res = ImagePlus(channel_name, corrected_ip)

            else:
                # no shading available → keep raw
                imp_res = ImagePlus(channel_name, raw_ip)

            shadowcorrected.append(imp_res)

        # combine back to stack
        stack = ImagesToStack.run(shadowcorrected) if shadowcorrected else None
        if stack is None:
            return None

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
        # fiji Version
        logger.info("Current IMAGEJ version: " +  IJ.getVersion())
        if not os.path.exists(self.tempfile):
            logger.warning("No csv file was found. Something went wrong when setting the parameters in the the "
                           "dialog for setting the parameters for stitching. The user may have cancelled it or "
                           "deleted it. Repeat the step if you want to stitch the channel images "
                           "with the DAPI image as reference and set the parameters. Doing nothing.")
            return
        try:
            data = ht.read_data_from_csv(self.tempfile)
        except:
            logger.exception("Could not get the input parameters. Exiting")
            return
        selected_files = []
        selected_resolutions = []
        shading_files = {}
        for case in data:
            selected_files = selected_files + [case['selected_files'].split(";")]
            selected_resolutions.append(case['resolution'])
            shading_files[case["date"]] = case['selected_shading_file']
        selected_files=list(set([x for xs in selected_files for x in xs]))
        selected_resolution = list(set(selected_resolutions))[0]
        dir = os.walk(self.inputdir)
        if dir:
            csv_data = []
            czi_paths = []
            shading_file_paths = []
            for file_path in selected_files:
                filename=os.path.basename(file_path)
                if filename.endswith(self.czi_ext) and not filename in shading_files.values() and not config.shading_word in filename.lower():
                    czi_paths.append(file_path)
                elif filename.endswith(self.czi_ext) and filename in shading_files.values():
                    shading_file_paths.append(file_path)
            czi_paths.sort()
            default_channels = []
            for image_file_path in czi_paths:
                imagefile = image_file_path
                self.set_prefs(stitchtiles=False, attach=False)
                options = self.set_import_options(imagefile)
                default_channels = default_channels + self.setting_default_channels(options)
                default_channels = list(set(default_channels))
            for image_file_path in czi_paths:
                imagefile = image_file_path
                logger.info("Current CZI File: " + imagefile)
                omeMeta = self.get_omemeta(imagefile)
                self.set_prefs(stitchtiles=False, attach=False)
                options = self.set_import_options(imagefile)
                omeMeta_no_stitch = self.get_omemeta_no_stitching(imagefile)
                imps = BF.openImagePlus(options)
                tilefileID = os.path.basename(imps[0].getTitle())
                tilefileID_strings = os.path.splitext(tilefileID)[0]
                if len(imps)==1:
                    fileID = tilefileID_strings.split(self.czi_ext + " - ")[0].replace(" ", "_")
                else:
                    fileID = tilefileID_strings.split(self.czi_ext + " - ")[1].replace(" ", "_")
                metaData = self.get_meta(omeMeta, imps, fileID, options, default_channels)
                scenesnumber, scenes_tiles, series_not_to_exclude = self.setting_series(options)
                tiles_to_skip_by_many_scenes=[]
                for i in range(len(imps)):
                    if i not in series_not_to_exclude:
                        tiles_to_skip_by_many_scenes.append(i)
                shadingfile = self.no_shading_file
                shadingfilepath  = ""
                for shading_file_path in shading_file_paths:
                    shading_file = os.path.basename(shading_file_path)
                    if shading_file in shading_files[str(metaData["date"])]:
                        options = self.set_import_options(shading_file_path)
                        shadingfile = BF.openImagePlus(options)
                        shadingfilepath = shading_file_path
                if shadingfile==self.no_shading_file:
                    logger.info("Current Shading File: " + shadingfile)
                else:
                    logger.info("Current Shading File: " + shadingfilepath)

                if scenesnumber >= 1:
                    for scene in range(scenesnumber):
                        for key in scenes_tiles:
                            if key == scene:
                                if scenesnumber==1:
                                    filename = fileID
                                else:
                                    filename = fileID + "-scene-" + str(scene)
                                savingDir = ht.correct_path(self.outputdir, filename)
                                outputDir = ht.correct_path(savingDir, "stitched_output")
                                if not os.path.exists(savingDir):
                                    os.makedirs(savingDir)
                                if not os.path.exists(outputDir):
                                    os.makedirs(outputDir)
                                if os.listdir(savingDir):
                                    self.removeAllTemps(savingDir)
                                for i, tile in enumerate(scenes_tiles[key]):
                                    imp = imps[tile-1]
                                    if shadingfile != self.no_shading_file:
                                        omeMeta_shadingFile = self.get_omemeta(shadingfilepath)
                                        metaData_shadingFile = self.get_meta(omeMeta_shadingFile, shadingfile,
                                                                             shadingfilepath, options,
                                                                             default_channels)
                                        imp_res = self.shadowCorrection(imp, shadingfile[0], metaData, metaData_shadingFile)

                                    else:
                                        imp_res = imp
                                    tile_name = "tile_" + str(i + 1).zfill(3) + self.tif_ext
                                    logger.info("Saving " + tile_name + " under " + savingDir)
                                    FileSaver(imp_res).saveAsTiff(ht.correct_path(savingDir, tile_name))
                                    logger.info("Saving :  Ends at " + str(time.time()))
                                    if len(scenes_tiles[key])>1:
                                        coordinates = self.get_meta_not_stiched(metaData, omeMeta_no_stitch,
                                                                            [position-1 for position in scenes_tiles[key]])
                                        self.write_tile_configuration_file(tile_name, coordinates[i], savingDir)
                                    IJ.run("Close All")
                                if len(scenes_tiles[key]) != 1:
                                    self.stitching(savingDir, outputDir)
                                #    res = WindowManager.getCurrentImage()
                                    res=None
                                else:
                                    tile_name = "tile_" + str(1).zfill(3) + self.tif_ext
                                    res = IJ.openImage(ht.correct_path(savingDir, tile_name))
                                self.removeAllTemps(savingDir, keep_dirs=["stitched_output"])
                                self.show_output_images_for_further_process(outputDir, savingDir, metaData, filename, 'tif', selected_resolution, res)
                                csv_data = self.make_dict(metaData, filename, csv_data)
                                if res is not None:
                                    res.changes = False
                                    res.close()
                else:
                    logger.error("czi file is damaged")

            # clear memory
            System.gc()
            # Set the preferences in the ImageJ plugin back to default
            self.set_prefs(stitchtiles=True, attach=True)
            if csv_data:
                self.write_metadata_csv(csv_data, self.workingdir)

        else:
            logger.warning("Directory is empty. There are no czi files")