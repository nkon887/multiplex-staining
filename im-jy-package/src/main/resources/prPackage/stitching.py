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
from loci.formats.in import DynamicMetadataOptions
sys.path.append(os.path.abspath(os.getcwd()))
import helpertools as ht
from ij.plugin import ImagesToStack
from ij.plugin import HyperStackConverter
import config
# im-jy-package.stiching.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.macro.im-jy-package.main.STITCHING')


class stitchingTools:
    def __init__(self, inputdir, outputdir, workingdir, czi_ext, tif_ext, infos_txt, metadata_csv_file, no_shading_file, shading_word, TIFF_ext):
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
                shading_consisting_date_filtered_czifiles = [x for x in date_filtered_czifiles if config.shading_word in x.lower() and x!=self.no_shading_file]
                if shading_consisting_date_filtered_czifiles:
                    primary_selected_file = shading_consisting_date_filtered_czifiles[0]
                else:
                    primary_selected_file = date_filtered_czifiles[0]
                gui.addChoice(date + ":", date_filtered_czifiles,
                              primary_selected_file)  # czifiles[2] is default here
                if i % 2 == 0 and date != dates[len(dates) - 1]:
                    gui.addToSameRow()
            gui.addChoice("Resolution", ["8-bit", "16-bit", "32-bit", "original"],
                          "8-bit")  # set resolution, 8-bit is default here
            gui.showDialog()
            if gui.wasCanceled():
                logger.warning("User canceled dialog! Doing nothing. Exit")
                return
            shading_files = {}
            for date in dates:
                shading_files[date] = gui.getNextChoice()
            selected_resolution = gui.getNextChoice()
            return [shading_files], selected_resolution
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

    def save_singleplanes(self, imp, savepath, metainfo, filename, format='tiff', selected_resolution='original'):
        if selected_resolution!='original':
            IJ.run(imp, selected_resolution, "")
        stack = imp.getImageStack()
        for s in range(1, stack.size() + 1):
            slicetitle = metainfo["fileID"] + "_" + metainfo["channel " + str(s)] + "." + format
            endfilename = filename + "_" + metainfo["channel " + str(s)] + "." + format
            stackindex = s
            aframe = ImagePlus(slicetitle, imp.getStack().getProcessor(stackindex))
            outputpath = ht.correct_path(savepath, endfilename)
            IJ.saveAs(aframe, self.TIFF_ext, outputpath)

    def removeAllTemps(self, directory):
        for filename in os.listdir(directory):
            #if not filename.endswith(".xml"):
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
        if positions_not_to_exclude:
            for i, position in enumerate(positions_not_to_exclude):
                coordinates[i] = [xml_meta.getPlanePositionX(position, 0).value(), xml_meta.getPlanePositionY(position, 0).value()]
        else:
            for i in range(imageCount):
                coordinates[i] = [xml_meta.getPlanePositionX(i, 0).value(), xml_meta.getPlanePositionY(i, 0).value()]
        x_min = coordinates[0][0]
        y_min = coordinates[0][1]
        for k in coordinates:
            coordinates[k][0] -= x_min
            coordinates[k][1] -= y_min
            coordinates[k][0] *= 1/metaData["PhysicalSizeX"]
            #-1.885
            coordinates[k][1] *= 1/metaData["PhysicalSizeY"]
            #-1.885
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

    def make_dict(self, metainfo, csv_list):
        len_default_channels = 0
        for key in metainfo:
            #if "Experiment|HardwareSettingsPool|HardwareSetting|Name #" in key:
            if "DefaultChannel #" in key:
                len_default_channels += 1
        fields = ['date', 'expID', 'channelsNumber', 'defaultChannelsNumber'] + ["channel " + str(channel + 1) for channel in
                                                        range(metainfo['defaultChannelsNumber'])] +["marker for channel " + str(channel + 1) for channel in
                                      range(metainfo['defaultChannelsNumber'])] + [
                     "ExposureTime #" + str(channel + 1) + " " + metainfo["DefaultChannel #" + str(channel + 1)] for channel in
                     range(metainfo['defaultChannelsNumber'])] + \
                 ["ObjectiveModel", "ObjectiveNominalMagnification"] + [
            "DefaultChannel #" + str(default_channel + 1) for default_channel in range(len_default_channels)] + ['SizeX', 'SizeY']
                                                        #range(metainfo['channelsNumber'])] + [
                     #"Information|Image|Channel|ExposureTime #" + str(channel + 1) + " " + metainfo[
                     #    "channel " + str(channel + 1)] for channel in range(metainfo['channelsNumber'])] +
        # [
        # "Experiment|HardwareSettingsPool|HardwareSetting|Name #" + str(
        #     default_channel + 1) for default_channel in range(len_default_channels)]

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
        savepath = ht.correct_path(savingDir, r"TileConfiguration.txt")
        if not os.path.exists(savepath):
            f = open(savepath, "w")

            f.write("# Define the number of dimensions we are working on\ndim = 2\n\n# Define the image coordinates")
            f.write("\n" + tile_name + "; ; (" + str(coordinates[0]) +", " + str(coordinates[1]) +")")
        else:
            f = open(savepath, "a")
            f.write("\n" + tile_name + "; ; (" + str(coordinates[0]) +", " + str(coordinates[1]) +")")
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
        prefix = "type=[Positions from file] order=[Defined by TileConfiguration] directory=" + savingDir + " layout_file=TileConfiguration.txt "
        suffix = "fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 compute_overlap subpixel_accuracy computation_parameters=[Save computation time (but use more RAM)] image_output=[Fuse and display]"
        IJ.run("Grid/Collection stitching", prefix + suffix)
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
        stack_shadingfile = shadingfile.getImageStack()
        stack_imp = imp.getImageStack()
        channels_shadingfile = []
        channels_imp = []

        for s in range(1, stack_shadingfile.size() + 1):
            channels_shadingfile.append(metaData_shadingFile["channel " + str(s)])
        for s in range(1, stack_imp.size() + 1):
            channels_imp.append(metaData_imp["channel " + str(s)])
        shadowcorrected = []
        for imp_stackindex in range(len(channels_imp)):
            if channels_imp[imp_stackindex] in channels_shadingfile:
                shadingfile_stackindex = channels_shadingfile.index(channels_imp[imp_stackindex])
                aframe = ImagePlus(channels_imp[imp_stackindex], imp.getStack().getProcessor(imp_stackindex+1))
                bframe = ImagePlus(channels_shadingfile[shadingfile_stackindex], shadingfile.getStack().getProcessor(shadingfile_stackindex+1))
                imp_res = ImageCalculator().run("Subtract create", aframe, bframe)
            else:
                imp_res = ImagePlus(channels_imp[imp_stackindex], imp.getStack().getProcessor(imp_stackindex+1))
            shadowcorrected.append(imp_res)
        stack = None
        if shadowcorrected:
            stack = ImagesToStack.run(shadowcorrected)
        res_stack = HyperStackConverter.toHyperStack(stack, metaData_imp["SizeC"], metaData_imp["SizeZ"], metaData_imp["SizeT"], metaData_imp["DimensionsOrder"], "Grayscale")
        return res_stack

    def process(self):
        # fiji Version
        imagejversion = IJ.getVersion()
        logger.info("Current IMAGEJ version: " + imagejversion)
        try:
            shading_files_dict, selected_resolution = self.getting_input_parameters()
            shading_files = shading_files_dict[0]
        except:
            logger.exception("Could get not the input shading files. Exiting")
            return
        dir = os.walk(self.inputdir)
        if dir:
            csv_data = []
            czi_paths = []
            shading_file_paths = []
            for path, subdirs, files in dir:
                for name in files:
                    file_path = ht.correct_path(path, name)
                    if name.endswith(self.czi_ext) and not name in shading_files.values() and not config.shading_word in name.lower():
                        czi_paths.append(file_path)
                    elif name.endswith(self.czi_ext) and name in shading_files.values():
                        shading_file_paths.append(file_path)
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
                # savingDir = ht.correct_path(self.outputdir, fileID)
                # if not os.path.exists(savingDir):
                #     os.makedirs(savingDir)
                # if os.listdir(savingDir):
                #     self.removeAllTemps(savingDir)
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

                # if scenesnumber == 1:
                #     coordinates = self.get_meta_not_stiched(metaData, omeMeta_no_stitch)
                #     for i, imp in enumerate(imps):
                #         if shadingfile != self.no_shading_file:
                #             imp_res = ImageCalculator().run("Subtract create stack", imp, shadingfile[0])
                #         else:
                #             imp_res = imp
                #         tile_name = "tile_" + str(i + 1).zfill(3) + self.tif_ext
                #         logger.info("Saving " + tile_name + " under " + savingDir)
                #         FileSaver(imp_res).saveAsTiff(ht.correct_path(savingDir, tile_name))
                #         logger.info("Saving :  Ends at " + str(time.time()))
                #         if len(imps) > 1:
                #             self.write_tile_configuration_file(tile_name, coordinates[i], savingDir)
                #         IJ.run("Close All")
                #     if len(imps) != 1:
                #         self.stitching(savingDir)
                #         res = WindowManager.getCurrentImage()
                #     else:
                #         tile_name = "tile_" + str(1).zfill(3) + self.tif_ext
                #         res = IJ.openImage(ht.correct_path(savingDir, tile_name))
                #     self.removeAllTemps(savingDir)
                #     self.save_singleplanes(res, savingDir, metaData, format='tif')
                #     txt_filename = self.infos_txt
                #     txt_savepath = ht.correct_path(self.outputdir, txt_filename)
                #     if os.path.exists(txt_savepath):
                #         with open(ht.correct_path(txt_savepath)) as f:
                #             if not metaData["date"] in f.read():
                #                 self.write_infos_txt(metaData, txt_savepath)
                #     else:
                #         self.write_infos_txt(metaData, txt_savepath)
                #     csv_data = self.make_dict(metaData, csv_data)
                #     res.changes = False
                #     res.close()
                if scenesnumber >= 1:
                    for scene in range(scenesnumber):
                        for key in scenes_tiles:
                            if key == scene:
                                if scenesnumber==1:
                                    filename = fileID
                                else:
                                    filename = fileID + "-scene-" + str(scene)
                                savingDir = ht.correct_path(self.outputdir, filename)
                                if not os.path.exists(savingDir):
                                    os.makedirs(savingDir)
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
                                    self.stitching(savingDir)
                                    res = WindowManager.getCurrentImage()
                                else:
                                    tile_name = "tile_" + str(1).zfill(3) + self.tif_ext
                                    res = IJ.openImage(ht.correct_path(savingDir, tile_name))
                                self.removeAllTemps(savingDir)
                                self.save_singleplanes(res, savingDir, metaData, filename, 'tif', selected_resolution)
                                # txt_filename = self.infos_txt
                                # txt_savepath = ht.correct_path(self.outputdir, txt_filename)
                                # if os.path.exists(txt_savepath):
                                #    with open(ht.correct_path(txt_savepath)) as f:
                                #        if not metaData["date"] in f.read():
                                #            self.write_infos_txt(metaData, txt_savepath)
                                #else:
                                #    self.write_infos_txt(metaData, txt_savepath)
                                csv_data = self.make_dict(metaData, csv_data)
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