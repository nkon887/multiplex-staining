####@ File(label='Original .CZI file', style='directory') input_dir
####@ File(label='"Choose an output location"', style='directory') output_dir
import os
import time
from ij import IJ, WindowManager
from ij.gui import GenericDialog
from ij.io import FileSaver
from java.lang import System

class Stitcher:
    def __init__(self, input_dir, output_dir, tiff_ext):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tiff_ext = tiff_ext
    # Dialog to find out how many channels, timepoints, and angles to anticipate
    def dialog_create(self):
        gui = GenericDialog("Parameters of your acquisition")
        gui.addMessage("First, define here the parameters of your acquisition")
        gui.addNumericField("Number of channels?", 1, 0)  # 0 for no decimal part
        gui.addMessage("How many tiles/views are there?")
        gui.addNumericField("Tiles/views?",10, 0)  # 0 for no decimal part
        gui.addMessage("Do you want to bin (downsample)?")
        gui.addNumericField("Bin in X",1, 0)  # 0 for no decimal part
        gui.addNumericField("Bin in Y",1, 0)  # 0 for no decimal part
        gui.addNumericField("Bin in Z",1, 0)  # 0 for no decimal part
        gui.showDialog()
        if gui.wasCanceled():
            print("User canceled dialog! Doing nothing. Exit")
            return
        numChan = int(gui.getNextNumber())  # This always return a double (ie might need to cast to int)
        numTile = int(gui.getNextNumber())
        binX = int(gui.getNextNumber())
        binY = int(gui.getNextNumber())
        binZ = int(gui.getNextNumber())
        return numChan, numTile, binX, binY, binZ
    def dialog_create_next(self, numChan):
        gui = GenericDialog("Parameters of your acquisition")
        chanDefaults = ["","green","red","",""]
        # Make a dialog to find out the parameters of the channels
        gui.addMessage("What are the names of your channels?")
        for currChan in range(numChan):
            print(str(currChan))
            if currChan > 4:
                chanDefaults[currChan] = ""
            gui.addStringField("Channel "+ str(currChan+1) +":", chanDefaults[currChan+1])
        gui.addMessage(" ")
        gui.addMessage("After clicking OK, you will be prompted to select\n" +
                        "the original .CZI file and an output location for \n" +
                        "the files corresponding to each channel.")
        gui.showDialog()
        chanName=[]
        for currChan in range(numChan):
            print(str(currChan))
            chanName.append(gui.getNextString())
            chanName[currChan]=chanName[currChan].replace(" ", "_")
        return chanName

    def process(self):
        numChan, numTile, binX, binY, binZ = self.dialog_create()
        chanName = self.dialog_create_next(numChan)
        # Get the path to each file and the output directory
        filePath=self.input_dir
        fileName= os.path.basename(filePath)
        outputDir=self.output_dir
        # Inside the output directory, make a directory for each channel
        for currChan in range(numChan):
            chanDir = os.path.join(outputDir, chanName[currChan])
            if not os.path.exists(chanDir):
                os.mkdir(chanDir)
        # Create markers for elapsed time.
        openElapsed = 0
        processElapsed = 0
        timesDone = 0
        timesRemain = 0
        filesRemain = numTile
        filesDone = 0
        absoluteStart = time.time()

        # Determine file structure
        if numChan == 1 and numTile > 1:
            print("Number of Channels = " + str(numChan) + ".  Number of Angles = " + "numAngle")
            # Open file
            for Tile in range(1, numTile, 1):
                print("Opening Tile " + Tile)
                startedAt = time.time()
                # Open the file
                IJ.run("Bio-Formats Importer", "open=" + filePath + " color_mode=Grayscale view=Hyperstack stack_order=XYCZT series_" + str(Tile))
                print("Opened Tile "+ Tile)
                # Downsample and save
                if binX + binY + binZ > 3:
                    print("Downsampling")
                    IJ.run("Bin...", "x=" + binX + " y=" + binY + " z=" + binZ + " bin=Average")
                    print("Downsampled Tile " + Tile + ": " + binX + " x " + binY + " x " + binZ + " times")
                filename=os.path.join(outputDir, chanName[1], "tile_" + IJ.pad(Tile,2) + ".tif")
                res = WindowManager.getCurrentImage()
                FileSaver(res).saveAsTiff(filename)
                res.close()
                # clear memory
                System.gc()
                # Update counters
                openElapsed += time.time() - startedAt
                filesDone += 1
                filesRemain -= 1
                print("Files completed = " + filesDone + " Files remaining = " + filesRemain)
            totalTime = (time.time()-absoluteStart)/(1000*60)
            print("ALL DONE! It took "+ totalTime)
            # Save the log file
            IJ.selectWindow("Log")
            thisFile = os.path.join(outputDir, "CZI_to_TIF.log")
            IJ.saveAs("text",thisFile)
        elif numChan > 1 and numTile > 1:
            print("Number of Channels = " + str(numChan) + ".  Number of Tiles = " + str(numTile))
            # Open file
            for Tile in range(1,numTile,1):
                print("Opening Tile " + str(Tile))
                startedAt = time.time()
                # Open the file
                IJ.run("Bio-Formats Importer", "open=" + filePath + " color_mode=Grayscale view=Hyperstack stack_order=XYCZT series_" + str(Tile))
                print("Opened Tile "+ str(Tile))
                # Split channels
                IJ.run("Split Channels")
                windowlist = WindowManager.getIDList()
                print(windowlist)
                for i,id in enumerate(windowlist):
                    print(i)
                    print(id)
                    prefix = WindowManager.getImage(id).getTitle().startswith("C" + str((i+1)))
                    print("Found window: " +  WindowManager.getImage(id).getTitle() + "  Window assigned to channel (1 = YES): " + str(prefix))
                    if prefix:
                        IJ.selectWindow(WindowManager.getImage(id).getTitle())
                        imp = WindowManager.getCurrentImage()
                        imp.setTitle("Channel_" + str(i))
                        print("Window renamed: " + "Channel_" + str(i))
                        LUT = imp.getFileInfo().whiteIsZero
                        if LUT:
                            print("Channel_" + str(i) + "'s LUT is inverted!")
                            IJ.run("Invert LUT", "stack")
                            print("Inverted LUT")
                        # Downsample and save
                        if binX + binY + binZ > 3:
                            print("Downsampling")
                            IJ.run("Bin...", "x=" + binX + " y=" + binY + " z=" + binZ + " bin=Average")
                            print("Downsampled Tile "+ Tile +": " + binX + " x " + binY + " x " + binZ + " times")
                        filename=os.path.join(outputDir, chanName[i], "tile_" + IJ.pad(Tile,2) + ".tif")
                        #res = WindowManager.getCurrentImage()
                        FileSaver(imp).saveAsTiff(filename)
                        imp.close()
                    else:
                        print("Error, cannot find any open channel windows")
                # clear memory
                System.gc()
                # Update counters
                openElapsed += time.time() - startedAt
                filesDone += 1
                filesRemain -= 1
                print("Files completed = " + str(filesDone) + " Files remaining = " + str(filesRemain))
            totalTime = (time.time()-absoluteStart)/(1000*60)
            print("ALL DONE! It took "+ str(totalTime))
            # Save the log file
            IJ.selectWindow("Log")
            thisFile = os.path.join(outputDir, "CZI_to_TIF.log")
            IJ.saveAs("Text", thisFile)