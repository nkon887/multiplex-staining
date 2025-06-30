# Multiplex Fluorescence Immunostaining Analysis Pipeline For Preprocessing Of Czi Images

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

## Software Requirements
1. Miniforge (Python >= 3.12 )
2. Fiji (ImageJ 2.14.0/1.54f, Java 1.8.0_322, Jython)
3. Access to GitHub repository
4. Space for environments 6,6 GB
5. GPU acceleration for CellSegPackage requires Visual Studio 2017 (https://www.visualstudio.com/thank-you-downloading-visual-studio/?sku=Community&rel=15), CUDA 10.0 (https://developer.nvidia.com/cuda-10.0-download-archive?target_os=Windows&target_arch=x86_64&target_version=10&target_type=exenetwork), CUDNN 7.6.5 (https://developer.nvidia.com/rdp/cudnn-archive), and a CUDA compatible GPU. If you have it on your PC (you can check it in MiniForge Prompt).
      ```Miniforge Prompt
      nvidia-smi
      ```
     See example outpput below
   ![alt text](https://drive.google.com/uc?export=view&id=1xRbs62vaHWFmw3hC8GFtpLiZQYsiLF0Z)

## Supported Input Data
> [!CAUTION]
> 1. Images as czi files without any `space` such as ` ` in the file name.
> 2. Each image (incl. shading correction if available) name should start with 6 digits stating the image acquisition date (e.g. 230701). The files should be named according to the scheme date(6 digits) underscore `_` patientID (replace the underscore `_` or the space ` ` within the patient ID with another character such as `-`)
> Example: 123456_patientID
> 3. The pipeline creates folders, which the user don't have to change
> 4.Each batch should have at least two channels(markers): DAPI and one another marker

## Set-Up
1. Install miniforge https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe if you don't have it on your PC (only once)
2. Installation \ Software Execution
   - download and unzip the zipped file https://drive.google.com/file/d/1qKQKeDuvo5uztlP-rl4Mvs3vHvtpCVxw/view?usp=sharing
    ![alt text](https://drive.google.com/uc?export=view&id=1EVqBv0A8jcwNcTIbsOHib6fKtWqJbKax) (once during first software execution)
    There you have only folder `Multiplex_Pipeline_Execution` with execution file `install_tar_gz_envs_with_path_ask.py` and im-jy-package with `im-jy-package-0.1.0-SNAPSHOT.jar` in it. Or download from github directly by clicking on the green button and selecting download as zip. See images below
    ![alt text](https://drive.google.com/uc?export=view&id=182RPRTrFizRkylXiDCQ8mN3iurB3jcfg)
    (once during first software execution). Next time skip this substep.
   - Then you have to unzip the file (once during first software execution). Next time skip this step.
   - download then the tar.gz files from `Charite OneDrive` https://charitede-my.sharepoint.com/:f:/r/personal/natalja_amiridze_charite_de/Documents/Natalia/envs_archives?csf=1&web=1&e=RaC4lm and store these files in the subfolder (name this subfolder something like `tar_envs`, so that the name doesn't contain any space).  
   - As test data you can download and unzip this file https://drive.google.com/file/d/1gOXjYkKwmDVb5129u52WE24drqn89Pyq/view?usp=drive_link. There you find two czi files with a shading file and the description txt file `StainingSequence.txt` with marker information 
   - Install Fiji on your PC https://imagej.net/software/fiji/downloads (once during first software execution). Next time skip this step
   - Set up the `FIJIPATH` environment variable (only once):
      - Go to `Start` - `Edit system variables` - `Environment variables`. There set the system variable `Variable name` to `FIJIPATH` and `Variable value` to the file location of ImageJ-win64.exe of your `Fiji`. (once during first software execution). Next time skip this step
      - Navigate to the  execution  folder of the cloned git repository and run the commands in the Miniforge Prompt:
         ```Miniforge Prompt
         cd [...path-to-the-downloaded-multiplex-staining...]/multiplex-staining/Multiplex_Pipeline_Execution/
         python install_tar_gz_envs_with_path_ask.py
         ```
      - You are promted to give path to the subfolder directory where tar.gz files are stored, choose it by clicking on the button `browse` then push on a button `Continue` (see image below)
     ![alt text](https://drive.google.com/uc?export=view&id=1lj4uq8YJh4M0Gd0K-yx9uS5MAyF3EE9C)
      - If it is first time you're using the software and environments are not already set, then you must wait until the environments are set and the multiplex pipeline window opens (usually takes 7-10 minutes). Otherwise, the interface will be loaded in some seconds 
      - A graphical user interface (GUI) window (multiplex) will pop up. Next time you don't have to install and if you don't want to use it right at the moment, just exit it. In the main interface window you are asked to select it if you have a graphics processing unit (GPU) on your computer or not to select it if you don't. It is important that you make your selection before you perform the `DAPISEG` step. The forceSave enables the user to overwrite the output data, which maybe already be present as output. The cropping options are to select a mode of the image cropping, dependent on what you want. If you want to select image frame on your own, select then `Manual Selection`, if you want to have already preselected frame, which excludes black area by creating a preselected rectangle frame around tissue, then Semiautomatic Mode has to be selected and the user has then a possibility to check it and make final frame selection, how image should be cropped. Another Mode `Automatic Selection` is the mode where automatically the black area, which surrounds the tissue will be automatically cropped out without user corrections.
      ![alt text](https://drive.google.com/uc?export=view&id=1W8AODATeOfiUPeD2lCmZjEf9Yuh0U-Zw)
   
      All buttons are deactivated on the left. In order to activate, you need to select the input location (where your raw czi data is located, usually in the microscopy-core server) and the destination location (where you want to store the output of the pipeline, recommended is local hard disk of a workstation if space is available. The path should not have any spaces in the names of the subfolders). After you have provided all the inputs, the required environments for running the pipeline steps will be created (please be patient, it takes some time (7-30 minutes)). It is performed only during the first execution of the pipeline. In the next runs, the environments are only checked for their existence (it takes about 1 minute). At the end, the steps for which you provided input will be activated (if your target directory does not contain workingDir and subfolders, only the first step `IMAGE PREPARATION` will be activated. Otherwise, you can continue where you stopped with the next step of the pipeline or run the previous steps again).
      It is possible to run multiple series independently, just make sure you select the appropriate output folder and this will allow you to restart from where you left that particular series.
      To execute the steps, you need to click the step button on the left side of the GUI window. When one of the pipeline steps is completed, the button turns yellow. Also, in the main window the state changes from "`Step` is running. Waiting..." to "DONE" in the output_box.
      ![alt text](https://drive.google.com/uc?export=view&id=1zQJGhhRoQWqE57nmIJCImkfOWiSQ2eRn)
4. The structure for the processed image files in your destination directory is then:
   ```Explorer
        workingDir/
                  /01_input
                           /date_caseID_subfolder(s)
                  /02_alignment
                           /aligned stack(s) as tiff_file(s)
                  /02_01_input_to_precrop
                           /date_caseID_subfolder(s) (if not missaligned copied from 01_input)
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
1. 
> [!CAUTION]
> For the `IMAGE PREPARATION` step (im-jy-package) if you want shading correction, you must provide the shading correction file for each date with a name that includes the date (6 numbers like "230701") followed by the underscore `_` and word`shading` in czi format.

   If you do not have the shading file, the `IMAGE PREPARATION` step can be done without the shading correction. During this step a dialog will appear where you have a list of selected files and not selected (the files that have names or format that don't follow the scheme), the user has to select the shading correction file (or no shading `No_shading_file`) for each date and resolution of output tif file (`8-bit` per default).
   Example: 
   ![alt text](https://drive.google.com/uc?export=view&id=1ndEROklR7bWkE7lMVQFfvIDWVzW3vcKa)
   After submitting (clicking `OK`, `Cancel` ends the step), the `IMAGE PREPARATION` step is performed where Fiji will open and will either process the data or exit if you canceled the dialog. The images for each channel used are created and saved as tiff files in the date_sampleID subfolder in the `01_input` folder. Example:
   ![alt text](https://drive.google.com/uc?export=view&id=1Kqd2l3wuQEXxlY7pFm4FgltHJHTyusmC)
   Also, the `metadata.csv` file is created in the workingDir. This csv file contains `date`, `expID`, `channel number`, `exposure time` for each channel, `ObjectiveModel`, `ObjectiveNominalMagnification`, `Default Channel #num` for each default channel for each processed czi file. Also columns `marker for channel #ChannelNumber` for corresponding channel will be stored and updated in the next step `DATACHECK`. Also, the sizes of each tif tile is stored in this file as `SizeX`, `SizeY`. Example: 
   ![alt text](https://drive.google.com/uc?export=view&id=1XjSc6imPysIJAivxbDaiUruE7St_l8me)     
   When `IMAGE PREPARATION` is finished the button turns yellow and the next button `DATACHECK` is activated, and also you get on the right output in the `output window`.
   ALTERNATIVELY if you have more images that are to be added to the analysis: Run all previous steps from a distinct folder. After, copy/paste the content of the metadata file into the metadata from the first cycle. Copy the newly generated images into the input folder.
   ![alt text](https://drive.google.com/uc?export=view&id=12VYWTIMNe8OIyOrLQrmAJ93XBWdi8v8a)
   For 2 batches it takes about 1 min and 42s time to process

3. When you execute the `DATACHECK` step (multiplex), a window of the graphical user interface (GUI) is loaded showing the input directory path, a table of channels with the used channel cells marked in red for each date and below the output window.
 
   ![alt text](https://drive.google.com/uc?export=view&id=1fXMlQZc-GRDlp1kdVDd0JAf7eY6qT5_H)

   The red cells should be filled by the user with the used markers. Then the user has to click on the SUBMIT button, which triggers the renaming of the tiff images and their sample ID subfolders. The tiff images will be evaluated and you will get data in the output window such as how many batches there are for each sample ID, which of them are selected for alignment and which are not (since they have only one batch) and what markers, files and their size each sample ID has. When finished, click on the EXIT button.

   ![alt text](https://drive.google.com/uc?export=view&id=1fhwvf2dtons7szrDAmC5p7oa0V3o_3KT)
   For 2 batches it takes about 3 min time to process (including the time the user edits the table)

3. The next step is `ALIGN` (im-jy-package, Button `ALIGN`). In the `main window`  you have to select `ForceSave` option (if you want to overwrite the existing output files), click then on the button `ALIGN`. You will be prompted to set some parameters like `Feature Extraction Model`, `Registration Model` (see https://imagej.net/plugins/register-virtual-stack-slices) and `Background Parameters` (see https://imagej.net/plugins/rolling-ball-background-subtraction)  and ´autoContrast´ ( to increase the contrast optimally) for DAPI images. After you have confirmed the selection by clicking `OK` (`Cancel` ends the step), the matching of all directories sorted by `sampleID` is performed. Before alignment the number of tiff images will be adjusted to have the same number of files for each separate sampleID by copies of the DAPI file in the certain folder(s). If the image is corrupted, it will be copied to the error folder `error_subfolder` in the folder `02_alignment`.

   ![alt text](https://drive.google.com/uc?export=view&id=1qTd2QW7XyAbtN2KOxD1hrHnxF97trbyS)
   
   During the alignment three temporary folders `temp`, `out` and `transforms` are created in `02_alignment` if input data are in `01_input_dir`. These temporary subsubfolders are emptied after alignment of each `sampleID` and deleted after the alignment is finished for all `sampleIDs`. After successful alignment the DAPI files are treated with the background subtraction and are combined with other channel images of the certain `sampleID` into a stack and stored in the folder `02_alignment` or the input of misaligned data from `01_input_dir` is copied to the folder `02_01_input_to_precrop`. If the batch (images of one `patientID`) contains image files of one date (`single batch`) only stack of this images will be created without any alignment as it is not needed.
   Pro batch it takes usually up to 2 hours but may be longer if images have to many features

4. In the next step `CROP` (im-jy-package/multiplex) all image stacks produced during the step `ALIGN` and stored in `02_alignment` are cropped. The user may set `ForceSave` option in the `main window` to overwrite the output data and to select one of the three modes of the cropping step (`Manual Selection`, `Semiautomatic Selection` or `Automatic Selection`). By `Manual Selection` the stack of a certain `sampleID` is loaded, and the user has to set the region of interest manually and then after the confirmation (clicking `Ok` in the `Action required` dialog) it is automatically cropped. By `Semiautomatic Selection` the coordinates of the rectangle frame excluding the black regions of the background will be automatically determined and preset for the user and it can be then adjusted if needed, then after confirmation (clicking `Ok` in the `Action required` dialog) the image files are cropped


   ![alt text](https://drive.google.com/uc?export=view&id=1edKobjy015l790w-L7q4L-Wy1oovqTee)

   By `Automatic Selection` the coordinates of the rectangle form excluding the black background regions are automatically determined and automatically cut without user intervention.

   So, after each selection type the stack is cropped and saved in the folder `02_alignment` with the extension `_Cropped`
   The step takes some minute to process the data

5. In the next step `ADJUST BG` (im-jy-package) the background subtraction for the necessary markers takes place (please see https://imagej.net/plugins/rolling-ball-background-subtraction). The user may set `ForceSave` option in the `main window` to overwrite the output data. Thereby the user is prompted to set the background parameter settings. If you press `Ok` (`Cancel` ends the step), the background subtraction applies to the selected images.
   

   ![alt text](https://drive.google.com/uc?export=view&id=16aw2RnzqdsGoSsbC8KzNUMvElswYDJd1)


   The cropped stacks of images from `02_alignment` are processed and each slice of each aligned stack is saved with (extension: `_background_sub`) and without background subtraction (extension: `_no_background`) in the folder `06_bg_processed`
   The step takes some minute to process the data

6. For the step `MERGE CHANNELS` (im-jy-package) the user may set `ForceSave` option in the `main window` to overwrite the output data. In this step, the images from DAPI and other channels from the step background subtraction selected by the user are merged and saved in the folder `07_mergedChannels`. At the beginning, the user is asked to set parameters for the selection of the DAPI image for each sampleID and the images of the channels to be merged with the selected DAPI image. If you press `Ok` (`Cancel` ends the step), the selected marker images are merged with the selected DAPI images.


   ![alt text](https://drive.google.com/uc?export=view&id=1xWoPaQUTFVtYvu_JDKnVwl7O987iDvaX)
   The step takes some minute to process the data

7. The next step is `DAPISEG` (multiplex, cellsegpackage). The user may set `ForceSave` option to overwrite the output data and `GPU option` to process the data faster in the `main window`. Thereby the data are put to the correct input form and segmented using the CellSeg package (the scripts and pretrained model from `https://github.com/michaellee1/CellSeg` are adapted to our purpose, contour to entire filling of segmented cells (cell masks), separating neighboured cell masks from each other). Then the segmentation file with the cells of different colour (grayscale gradient) is converted to the binary mask (multiplex), the small holes in the cells are filled and small artifacts removed. Then the masks are resized (im-jy-package) to have the same size as origin segmented image 

   ![alt text](https://drive.google.com/uc?export=view&id=1ErYM0Iu56O5m4PS_vjE8Cn4NMpzSg6Dx)
   The step takes some minute to one hour if the image is big

8. By the step `CLEAN OUTPUT` the user is asked (see dialog window below)  to confirm to clean redundant intermediate data and store only the results. If the user confirms, all other subfolders in the folder workingDir are deleted and only the final subfolder "o6_results_output" and metadata.csv remain in the main folder after this step
   
   ![alt text](https://drive.google.com/uc?export=view&id=1T8DbHWzG5jLqWSXoTJQE3XHtk4-J5oxg)
   The step takes some minute to one hour if the image is big.

9. Another possibility is to execute `COMBI:BG MERGE DAPISEG` to do `BG ADJUST`, `MERGE CHANNELS` and `DAPISEG` at once with setting all parameters for these three steps before execution.

   ![alt text](https://drive.google.com/uc?export=view&id=1jKuhlt8-BsSbLGndPm0EF4-zd61YceqP)

## Notes:
+ If errors are occurring during the execution, there are outputs on the console of Fiji and in AnacondaPrompt and the history is stored in logs.log in the execution folder
+ During the execution, there is also an output on the console of Fiji and AnacondaPrompt and is stored in `logs.log`
+ The execution times of the steps of image processing are outputted in the end on the console of MiniForgePrompt and in `logs.log`
