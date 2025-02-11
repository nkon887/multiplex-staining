# multiplex fluorescence immunostaining analysis pipeline for preprocessing of czi images

## Description
This pipeline enables the user to prepare multiplex staining
microscopy images for further tissue or cell population analysis.
It consists of three main packages 1/ multiplex (python package), 2/ im-jy-package (Fiji package) and 3/ adapted cellsegpackage (python package using  scripts and model from `https://github.com/michaellee1/CellSeg`)
It converts czi unstitched data to stitched tiff images and extracts thereby necessary metadata. The czi files may consist of one scene (unstitched set of tile images with one or more channels or entire image sets  (no tiles) containing channels) or series of scenes mixed with not image files.
It works further with the tiff images and uses extracted metadata.

3, 4 channel images per date corresponding to one experiment are treated individually. 
Since the position of the region of interest changes from date to date, the channel images must be aligned. 
If the alignment of the raw data does not work properly, the images of each date are treated separately as
a batch and processed (cropped) to repeat the alignment. It is possible to process more than one batch in
one pass. After this process, the images are processed so that they are ready for further marker-specific segmentation and image analysis in other software.

The steps performed by this pipeline are:</br>
large scan stitching > channel renaming > sequential image alignment > background subtraction and channel merging > DAPI segmentation </br>
This pipeline generates all images required for: marker segmentation, imaging data generation and analysis

## Requirements
1. Anaconda (Python > 3.10) or Miniforge (Python >= 3.12 )
2. Fiji (Jython)
3. Git Bash
4. Access to GitHub repository
5. Images as czi files without any "space" in the file name.
6. Each image (incl. shading correction if available) name should start with 6 digits stating the image acquisition date (e.g. 230701). The files should be named according to the scheme date(6 digits) underscore "\_" patientID (replace the underscore "\_" or the space " " within the patient ID with another character such as "-")

## Set-Up
1. Install anaconda https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html or miniforge https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe if you don't have it on your PC (only once)
2. Before proceeding with the setup and installation, check if you already have environments for the multiplex pipeline such as `multiplex`, `myenv`, `cellsegsegmenter_cpu` and `cellsegsegmenter_gpu` in anaconda or miniforge (see the screenshots below). If the environments are already set, then you need to delete them to set the environments with the updated version of the multiplex pipeline

   ![image](https://drive.google.com/uc?export=view&id=1ISIxmsBqbMoTHH3wyO5_djdVV7DBbZ0M)

   ![image](https://drive.google.com/uc?export=view&id=1PVn7yv3CLEBsFPdgDU5t2KRtXuXf3C92)

3. Installation
   - ### Using git bash 
      - Install git bash https://gitforwindows.org/ (only once)
      - Clone this repository. (only once)
        ```Bash
        git clone https://github.com/nkon887/multiplex-staining.git
        ```
        If it doesn't work for you, then you have to set environment variables
        http_proxy with a value http://proxy.charite.de:8080
        and
        https_proxy with a value http://proxy.charite.de:8080
        If it still doesn't work for you, use another installation method
      - Install Fiji on your PC https://imagej.net/software/fiji/downloads (only once)
      - Set up the `FijiPATH` environment variable (only once):
        Go to `Start` - `Edit system variables` - `Environment variables`. There set the system variable `Variable name` to `FijiPATH` and `Variable value` to the file location of ImageJ-win64.exe of your `Fiji`
      - Copy the jar file im-jy-package-0.1.0-SNAPSHOT.jar from "path-to-the-cloned-multiplex-staining-directory/multiplex-staining/im-jy-package/target" to `jars/Lib` (manually or using Git Bash. `Lib` may not exist yet (only once).
        ```Bash
        mkdir -p path-to-Fiji/jars/Lib
        cp path-to-the cloned-multiplex-staining-directory/multiplex-staining/im-jy-package/target/im-jy-package-0.1.0-SNAPSHOT.jar path-to-ImageJ/jars/Lib/
        ```
      - Go to Start and search for "Anaconda Prompt" or "Miniforge Prompt" and click to open. Start the terminal. Navigate to the  execution  folder of the cloned git repository and run the commands in the terminal:
          ```Bash
          cd path-to-the-cloned-multiplex-staining/multiplex-staining/Multiplex_Pipeline_Execution/
          python exe.py
          ```
      - You must wait until the environments are set and the multiplex pipeline window opens.
      - After creating a new environment (myenv), a graphical user interface (GUI) window (multiplex) will appear asking you if you have a graphics processing unit (GPU) on your computer (or not selecting it if you don't. It is important that you make your selection before you perform the DAPISEGMENTATION step).
        ![image](https://drive.google.com/uc?export=view&id=1W8AODATeOfiUPeD2lCmZjEf9Yuh0U-Zw)
        All buttons are deactivated on the left. In order to activate, you need to select the input location (where your raw czi data is located, usually in the microscopy-core server) and the destination location (where you want to store the output of the pipeline, recommended is local hard disk of a workstation if space is available. The path should not have any spaces in the names of the subfolders). After you have provided all the inputs, the required environments for running the pipeline steps will be created (please be patient, it takes some time (7-30 minutes). It is performed only during the first execution of the pipeline. In the next runs, the environments are only checked for their existence (it takes about 1 minute). At the end, the steps for which you provided input will be activated (if your target directory does not contain workingDir and subfolders, only the first step `STITCH` will be activated. Otherwise, you can continue where you stopped with the next step of the pipeline or run the previous steps again).
        It is possible to run multiple series independently, just make sure you select the appropriate output folder and this will allow you to restart from where you left that particular series.
        To execute the steps, you need to click the step button on the left side of the GUI window. When one of the pipeline steps is completed, the button turns yellow. Also, in the main window the state changes from "`Step` is running. Waiting..." to "DONE" in the output_box.
        ![image](https://drive.google.com/uc?export=view&id=1zQJGhhRoQWqE57nmIJCImkfOWiSQ2eRn)
   - ### Local Installation
      - download and unzip the zipped file https://drive.google.com/file/d/1-12zusii34W02ncfnynAMl_ZpJEZUOQN/view?usp=drive_link
        ![image](https://drive.google.com/uc?export=view&id=1EVqBv0A8jcwNcTIbsOHib6fKtWqJbKax)
        There you have two modules: multiplex package (multiplex-staining) and cellseg package (CellSeg_package) and test data (raw_input)
      - Or download from github directly by clicking on the green button and selecting download as zip. See images below
        ![image](https://drive.google.com/uc?export=view&id=182RPRTrFizRkylXiDCQ8mN3iurB3jcfg)
        ![image](https://drive.google.com/uc?export=view&id=1UlPwEbSlnx0naaCR1-Qhnz8AQlp3NHzS)
      - Then you have to unzip the files and the content put to the corresponding folders `CellSeg_package` and `multiplex-staining` in the one main folder called `pipeline` 
      - Install Fiji on your PC https://imagej.net/software/fiji/downloads (only once)
      - Set up the `FijiPATH` environment variable (only once):
        Go to `Start` - `Edit system variables` - `Environment variables`. There set the system variable `Variable name` to `FijiPATH` and `Variable value` to the file location of ImageJ-win64.exe of your `Fiji`
      - Copy the jar file `im-jy-package-0.1.0-SNAPSHOT.jar` from "path-to-the-cloned-multiplex-staining-directory/multiplex-staining/im-jy-package/target" to `jars/Lib` (manually or using Git Bash. `Lib` may not exist yet (only once).
        ```Bash
        mkdir -p path-to-Fiji/jars/Lib
        cp path-to-the cloned-multiplex-staining-directory/multiplex-staining/im-jy-package/target/im-jy-package-0.1.0-SNAPSHOT.jar path-to-ImageJ/jars/Lib/
        ``` 
      - Now you must execute the following commands in the terminal:
        ```Bash
           cd path-to-the-cloned-or-downloaded-multiplex-staining/multiplex-staining/Multiplex_Pipeline_Execution/
           python exe_with_installing_all_packages.py
        ``` 
      - You must wait until the environments are set and the multiplex pipeline window opens.
      - After creating a new environment (myenv), a graphical user interface (GUI) window (multiplex) will appear asking you if you have a graphics processing unit (GPU) on your computer (or not selecting it if you don't. It is important that you make your selection before you perform the `DAPISEG` step).
        ![image](https://drive.google.com/uc?export=view&id=1W8AODATeOfiUPeD2lCmZjEf9Yuh0U-Zw)
        All buttons are deactivated on the left. In order to activate, you need to select the input location (where your raw czi data is located, usually in the microscopy-core server) and the destination location (where you want to store the output of the pipeline, recommended is local hard disk of a workstation if space is available. The path should not have any spaces in the names of the subfolders). After you have provided all the inputs, the required environments for running the pipeline steps will be created (please be patient, it takes some time (7-30 minutes). It is performed only during the first execution of the pipeline. In the next runs, the environments are only checked for their existence (it takes about 1 minute). At the end, the steps for which you provided input will be activated (if your target directory does not contain workingDir and subfolders, only the first step `STITCH` will be activated. Otherwise, you can continue where you stopped with the next step of the pipeline or run the previous steps again).
        It is possible to run multiple series independently, just make sure you select the appropriate output folder and this will allow you to restart from where you left that particular series.
        To execute the steps, you need to click the step button on the left side of the GUI window. When one of the pipeline steps is completed, the button turns yellow. Also, in the main window the state changes from "`Step` is running. Waiting..." to "DONE" in the output_box.
        ![image](https://drive.google.com/uc?export=view&id=1zQJGhhRoQWqE57nmIJCImkfOWiSQ2eRn)
4. The structure for the processed image files in your destination directory is then:
   ```Explorer
        workingDir/
                  /01_input
                           /date_caseID_subfolder(s)
                  /02_alignment
                           /aligned stack(s) as tiff_file(s)
                  /02_01_input_to_precrop
                           /date_caseID_subfolder(s) (if not missaligned copied from 01_input)
                  /02_02_stacks
                           /caseID_subfolder(s) with the stacks as tiff_files 
                  /02_03_cropped_input
                           /date_caseID_subfolder(s) of precropped tiff file(s)
                  /03_bg_processed
                           /caseID_subfolder(s) with background processed tiff file(s) 
                  /04_mergedChannels
                  /05_dapi_seg
                           /01_input_folder
                           /02_seg_output
                           /03_dapi_seg_binary
                           /04_binary_size_correct
                  /06_results_output
                           /CaseID subfolder(s) (nessesary output of all previous steps combined for each CaseID)
                           /mergedChannels  containing CaseID subfolders with output tiff images from the step mergedChannels
                  metadata.csv
   ```
## Steps
1. For the `STITCH` step (im-jy-package) your data should be in czi format and have the name according to the scheme `date(6 numbers like "230701")_sampleID.czi`. If you want shading correction, you must provide the shading correction file for each date with a name that includes the date (6 numbers like "230701") and `shading`. If you do not have the shading file, the `STITCH` step will be done without the shading correction. During this step a dialog will appear where you have a list of selected files and not selected (the files that have names or format that don't follow the scheme), the user has to select the shading correction file (or no shading `No_shading_file`) for each date and resolution of output tif file (`8-bit` per default).
   Example:
    
   ![image](https://drive.google.com/uc?export=view&id=1ndEROklR7bWkE7lMVQFfvIDWVzW3vcKa)

   After submitting (clicking `OK`, `Cancel` ends the step), the `STITCH` step is performed where Fiji will open and will either process the data or exit if you canceled the dialog. The images for each channel used are created and saved as tiff files in the date_sampleID subfolder in the `01_input` folder. Example:

   ![image](https://drive.google.com/uc?export=view&id=1Kqd2l3wuQEXxlY7pFm4FgltHJHTyusmC)
      
   Also, the `metadata.csv` file is created in the workingDir. This csv file contains `date`, `expID`, `channel number`, `exposure time` for each channel, `ObjectiveModel`, `ObjectiveNominalMagnification`, `Default Channel #num` for each default channel for each processed czi file. Also columns `marker for channel #ChannelNumber` for corresponding channel will be stored and updated in the next step `DATACHECK`. Also, the sizes of each tif tile is stored in this file as `SizeX`, `SizeY`. Example: 

   ![image](https://drive.google.com/uc?export=view&id=1XjSc6imPysIJAivxbDaiUruE7St_l8me)     
    
   When `STITCH` is finished the button turns yellow and the next button `DATACHECK` is activated, and also you get on the right output in the `output window`.
   ALTERNATIVELY if you have more images that are to be added to the analysis: Run all previous steps from a distinct folder. After, copy/paste the content of the metadata file into the metadata from the first cycle. Copy the newly generated images into the input folder.

   ![image](https://drive.google.com/uc?export=view&id=12VYWTIMNe8OIyOrLQrmAJ93XBWdi8v8a)

3. When you execute the `DATACHECK` step (multiplex), a window of the graphical user interface (GUI) is loaded showing the input directory path, a table of channels with the used channel cells marked in red for each date and below the output window.
 
   ![image](https://drive.google.com/uc?export=view&id=1fXMlQZc-GRDlp1kdVDd0JAf7eY6qT5_H)

   The red cells should be filled by the user with the used markers. Then the user has to click on the SUBMIT button, which triggers the renaming of the tiff images and their sample ID subfolders. The tiff images will be evaluated and you will get data in the output window such as how many batches there are for each sample ID, which of them are selected for alignment and which are not (since they have only one batch) and what markers, files and their size each sample ID has. When finished, click on the EXIT button.

   ![image](https://drive.google.com/uc?export=view&id=1fhwvf2dtons7szrDAmC5p7oa0V3o_3KT)

4. The next step is `ALIGN` (im-jy-package, Button `ALIGN/REALIGN`). In the `main window`  you have to select the option `ALIGN` and  select `FORCESAVE` option (if you want to overwrite the existing output files), click then on the button `ALIGN/REALIGN`. You will be prompted to set some parameters like `Feature Extraction Model`, `Registration Model` and `Background Parameters` for DAPI images. After you have confirmed the selection by clicking `OK` (`Cancel` ends the step), the matching of all directories sorted by `sampleID` is performed. Before alignment the number of tiff images will be adjusted to have the same number of files for each separate sampleID by copies of the DAPI file in the certain folder(s). If the image is corrupted, it will be copied to the error folder `error_subfolder` in the folder `02_alignment`.

   ![image](https://drive.google.com/uc?export=view&id=1qTd2QW7XyAbtN2KOxD1hrHnxF97trbyS)
   
   During the alignment three temporary folders `temp`, `out` and `transforms` are created in `02_alignment` if input data are in `01_input_dir`. These temporary subsubfolders are emptied after alignment of each `sampleID` and deleted after the alignment is finished for all `sampleIDs`. After successful alignment the DAPI files are treated with the background subtraction and are combined with other channel images of the certain `sampleID` into a stack and stored in the folder `02_alignment` or the input of misaligned data from `01_input_dir` is copied to the folder `02_01_input_to_precrop`. If the batch (images of one `patientID`) contains image files of one date (`single batch`) only stack of this images will be created without any alignment as it is not needed.

5. The next step is `REALIGN` (im-jy-package). In the `main window`  you have to select the option `REALIGN` and  select `FORCESAVE` option (if you want to overwrite the existing output files), click then on the button `ALIGN/REALIGN`. In this step the folder `02_01_input to precrop` will be checked. 

   ![image](https://drive.google.com/uc?export=view&id=1PwwjVpY1yK6Hy_Oopzhm5z7nRUwzIRw5)

   If it is not empty, you need to set some parameters like `Hyperstack Parameters`. By pressing the `OK` button (`Cancel` ends the step) the hyperstacks will be created for each date and for each `sampleID`.

   The hyperstacks for each sampleID and date are created and saved in the `02_02_stacks` folder. If the image is corrupted, the images of a certain date will be copied to the error folder `error_subfolder` for each `sampleID`. If you press `Ok` (`Cancel` ends the step) the hyperstack of a certain `sampleID` of a certain date is loaded, and you have to set the region of interest and confirm your selection.

   After that all hyperstacks of this `sampleID` are loaded with identical region of interest. You can adjust it by clicking inside it and moving. (Not recommended: You can also change the size of the region of interest if needed). After that you need to confirm it by clicking `Ok` in the `Action required` dialog.

   ![image](https://drive.google.com/uc?export=view&id=1edKobjy015l790w-L7q4L-Wy1oovqTee)

   Then the images will be cropped and stored as separate images in the folder `'02_03_cropped_input` in subfolders sorted by patient and date having the form `date_sampleID` and their files `date_sampleID_channel.tif`. If the image is corrupted, the images of a certain date will be copied to the error folder `error_subfolder` in the folder `02_02_stacks`.

   ![image](https://drive.google.com/uc?export=view&id=1qTd2QW7XyAbtN2KOxD1hrHnxF97trbyS)

   The next substep is to align again the problem data. The user have to check if the input is in the folder `02_03_cropped_input` and set the same parameters as in the `ALIGN` step. The data will be realigned and after this the image files will be saved in the folder `02_alignment` or the input data will be saved in the folder `02_01_input_to_precrop`

6. In the next step `CROP` (im-jy-package) all image stacks in `02_alignment` are cropped. The user may set `ForceSave` option in the `main window` to overwrite the output data and to select one of the three modes of the cropping step (`Manual Selection`, `Semiautomatic Selection` or `Automatic Selection`). By `Manual Selection` the stack of a certain `sampleID` is loaded, and the user has to set the region of interest manually and then after the confirmation (clicking `Ok` in the `Action required` dialog) it is automatically cropped. By `Semiautomatic Selection` the coordinates of the rectangle frame excluding the black regions of the background will be automatically determined and preset for the user and it can be then adjusted if needed, then after confirmation (clicking `Ok` in the `Action required` dialog) the image files are cropped


   ![image](https://drive.google.com/uc?export=view&id=1edKobjy015l790w-L7q4L-Wy1oovqTee)

   By `Automatic Selection` the coordinates of the rectangle form excluding the black background regions are automatically determined and automatically cut without user intervention.

   So, after each selection type the stack is cropped and saved in the folder `02_alignment` with the extension `_Cropped`

7. In the next step `ADJUST BG` (im-jy-package) the background subtraction for the necessary markers takes place. The user may set `ForceSave` option in the `main window` to overwrite the output data. Thereby the user is prompted to set the background parameter settings. If you press `Ok` (`Cancel` ends the step), the background subtraction applies to the selected images.
   

   ![image](https://drive.google.com/uc?export=view&id=16aw2RnzqdsGoSsbC8KzNUMvElswYDJd1)


   The cropped stacks of images from `02_alignment` are processed and each slice of each aligned stack is saved with (extension: `_background_sub`) and without background subtraction (extension: `_no_background`) in the folder `06_bg_processed`


8. For the step `MERGE CHANNELS` (im-jy-package) the user may set `ForceSave` option in the `main window` to overwrite the output data. In this step, the images from DAPI and other channels from the step background subtraction selected by the user are merged and saved in the folder `07_mergedChannels`. At the beginning, the user is asked to set parameters for the selection of the DAPI image for each sampleID and the images of the channels to be merged with the selected DAPI image. If you press `Ok` (`Cancel` ends the step), the selected marker images are merged with the selected DAPI images.


   ![image](https://drive.google.com/uc?export=view&id=1xWoPaQUTFVtYvu_JDKnVwl7O987iDvaX)


9. The next step is `DAPISEG` (multiplex, cellsegpackage). The user may set `ForceSave` option to overwrite the output data and `GPU option` to process the data faster in the `main window`. Thereby the data are put to the correct input form and segmented using the CellSeg package (the scripts and pretrained model from `https://github.com/michaellee1/CellSeg` are adapted to our purpose, contour to entire filling of segmented cells (cell masks), separating neighboured cell masks from each other). Then the segmentation file with the cells of different colour (grayscale gradient) is converted to the binary mask (multiplex), the small holes in the cells are filled and small artifacts removed. Then the masks are resized (im-jy-package) to have the same size as origin segmented image 

   ![image](https://drive.google.com/uc?export=view&id=1ErYM0Iu56O5m4PS_vjE8Cn4NMpzSg6Dx)

10. After the last pipeline step `OUTPUT` all other subfolders in the folder workingDir are deleted and only the final subfolder "o6_results_output" and metadata.csv remain in the main folder

11. Another possibility is to execute `FAST BUTTON` to do `BG ADJUST`, `MERGE CHANNELS` and `DAPISEG` at once with setting all parameters for these three steps before execution.

   ![image](https://drive.google.com/uc?export=view&id=1jKuhlt8-BsSbLGndPm0EF4-zd61YceqP)
## Notes:
+ If errors are occurring during the execution, there are outputs on the console of Fiji and in AnacondaPrompt and the history is stored in logs.log in the execution folder
+ During the execution, there is also an output on the console of Fiji and AnacondaPrompt and is stored in logs.log
+ The execution times of the steps of image processing are outputted in the end on the console of AnacondaPrompt and in logs.log
<!---+ In the case that you cannot install the packages from GitHub due to the authentication issues. In this case, you should download the repositories from GitHub containing the packages multiplex and cellsegpackage (https://github.com/nkon887/multiplex-staining and https://github.com/nkon887/CellSeg_package) and install them separately for the environments.
  For myenv you should do:
  ```Bash
     conda activate myenv
     pip install path-to-the-cloned-repository-multiplex-statining/Multiplex_package
  ```
  For multiplex you should do:
  ```Bash
     conda activate multiplex
     pip install path-to-the-cloned-repository-multiplex-staining/Multiplex_package
  ```
  For the environments cellsegsegmenter_cpu and cellsegsegmenter_gpu  you need also to download or clone the following repository https://github.com/nkon887/CellSeg_package
  ```Bash
    git clone https://github.com/nkon887/CellSeg_package.git
  ```
   Alternatively, you can click on the `Code` (right button marked as green) and in the dropdown list select `Download ZIP` (see the figure below)
   ![image](https://drive.google.com/uc?export=view&id=1UlPwEbSlnx0naaCR1-Qhnz8AQlp3NHzS)

  For cellsegsegmenter_cpu:
  ```Bash
     conda activate cellsegsegmenter_cpu
     pip install path-to-the-cloned-repository-multiplex-staining/Multiplex_package
     pip install path-to-the-cloned-repository-CellSeg_package/
  ```
  For cellsegsegmenter_gpu:
  ```Bash
     conda activate cellsegsegmenter_gpu
     pip install path-to-the-cloned-repository-multiplex-staining/Multiplex_package
     pip install path-to-the-cloned-repository-CellSeg_package/
  ```
--->
+ GPU acceleration for CellSegPackage requires Visual Studio 2017 (https://www.visualstudio.com/thank-you-downloading-visual-studio/?sku=Community&rel=15), CUDA 10.0 (https://developer.nvidia.com/cuda-10.0-download-archive?target_os=Windows&target_arch=x86_64&target_version=10&target_type=exenetwork), CUDNN 7.6.5 (https://developer.nvidia.com/rdp/cudnn-archive), and a CUDA compatible GPU. If you have it on your PC, then select GPU for the DAPISEGMENTATION
