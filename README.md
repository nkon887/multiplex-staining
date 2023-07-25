# multiplex fluorescence immunostaining analysis pipeline for preprocessing of czi images

## Description
This pipeline enables the user to process and prepare multiplex staining
microscopy images for further tissue or cell population analysis.
It consists of three main packages 1/ multiplex (python package), 2/ im-jy-package (FIJI package) and 3/ adapted cellsegpackage (python package using  scripts and model from `https://github.com/michaellee1/CellSeg`)
It converts czi unstitched data to stitched tiff images and extracts thereby necessary metadata. 
It works further with the tiff images and uses extracted metadata.

3, 4 channel images per date corresponding to one experiment are treated individually. 
Since the position of the region of interest changes from date to date, the channel images must be aligned. 
If the alignment of the raw data does not work properly, the images of each date are treated separately as
a batch and processed (cropped) to repeat the alignment. It is possible to process more than one batch in
one pass. After this process, the images are processed so that they are ready for segmentation.

## Requirements

1. Anaconda (Python > 3.10)
2. Fiji (Jython)
3. Git Bash
4. Access to github repository

## Set-Up
1. Install anaconda https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html (only once)
2. Install git bash https://gitforwindows.org/ (only once)
3. Clone this repository. (only once)

    ```Bash
    git clone https://github.com/nkon887/multiplex-staining.git
    ```
4. Install FIJI on your PC https://imagej.net/software/fiji/downloads:
5. Set up the `FIJIPATH` environment variable:
   Go to `Start` - `Edit system variables` - `Environment variables`. There set the system variable `Variable name` to `FIJIPATH` and `Variable value` to the file location of ImageJ-win64.exe (of your `FIJI`)
6. Copy the jar file im-jy-package-0.1.0-SNAPSHOT.jar from "path-to-the-cloned-multiplex-staining-directory/multiplex-staining/im-jy-package/target" to `jars/Lib` (manually or using Git Bash. `Lib` may not exist yet (only once).
    ```Bash
    mkdir -p path-to-Fiji/jars/Lib
    cp path-to-the cloned-multiplex-staining-directory/multiplex-staining/im-jy-package/target/im-jy-package-0.1.0-SNAPSHOT.jar path-to-ImageJ/jars/Lib/
    ```
7. Go to Start and search for "Anaconda Prompt" and click to open. Start the terminal. To navigate to the  execution  folder of the cloned git repository and execute, run the commands in the terminal:
    ```Bash
    cd path-to-the-cloned-multiplex-staining/multiplex-staining/Multiplex_Pipeline_Execution/
    python exe.py
    ```
8. After creating a new environment, a graphical user interface (GUI) window (multiplex) will appear asking you if you have a graphics processing unit (GPU) on your computer (or not selecting it if you don't. It is important that you make your selection before you perform the DAPISEGMENTATION step).
   
   
   ![image](https://drive.google.com/uc?export=view&id=1W8AODATeOfiUPeD2lCmZjEf9Yuh0U-Zw)
   

   All buttons are deactivated on the left. In order to activate, you need to select the input location (where your raw czi data is located) and the destination location (where you want to store the output of the pipeline). After you have provided all the inputs, the required environments for running the pipeline steps will be created (please be patient, it takes some time (7-30 minutes). It is performed only during the first execution of the pipeline. In the next runs, the environments are only checked for their existence. It takes about 1 minute). At the end, the steps for which you provided input will be activated (if your target directory does not contain workingDir and subfolders, only the first step STITCHING will be activated. Otherwise, you can continue where you stopped with the next step of the pipeline or run the previous steps again).
   To execute the steps, you need to click the step button on the left side of the GUI window. When one of the pipeline steps is completed, the button turns yellow.
9. The structure for the processed image files in your destination directory is then:
   ```Explorer
        workingDir/
                  /01_input
                           /infos.txt
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
1. For the STITCHING step (im-jy-package) your data should be in czi format and have the name according to the scheme `date(6 numbers like "010723")_patientID.czi`. If you want shading correction, you must provide the shading correction file for each date with a name that includes the date (6 numbers like "010723") and `shading`. If you do not have the shading file, the stitching will be done without the shading correction. During this step FIJI will open and a dialog will appear where you have to select the shading correction file (or no shading) for each date.
   Example:
   
  
   ![image](https://drive.google.com/uc?export=view&id=1ndEROklR7bWkE7lMVQFfvIDWVzW3vcKa)


   After submitting (clicking `OK`, `Cancel` ends the step), the stitching is performed, the images for each channel used are created and saved as tiff files in the date_patientID subfolder in the `01_input` folder, and the infos.txt file with the channel data for each date is created in the `01_input` folder. Example: 
   
   
   ![image](https://drive.google.com/uc?export=view&id=1Kqd2l3wuQEXxlY7pFm4FgltHJHTyusmC).
   
   
   Also, the metadata.csv file is created in the workingDir. This csv file contains `date`, `expID`, `channel number`, `exposure time` for each channel, `ObjectiveModel`, `ObjectiveNominalMagnification`, `Default Channel #num` for each default channel for each processed czi file. Example: 
   
   
   ![image](https://drive.google.com/uc?export=view&id=1XjSc6imPysIJAivxbDaiUruE7St_l8me)     
   
   
   When STITCHING is finished the buttons turns yellow and the next button `DATACHECK` is activated, and also you get on the right output in the `output window`.


   ![image](https://drive.google.com/uc?export=view&id=12VYWTIMNe8OIyOrLQrmAJ93XBWdi8v8a)


2. When you execute the DATACHECK step (multiplex), a window of the graphical user interface (GUI) is loaded showing the input directory path, a table of channels with the used channel cells marked in red for each date and below the output window.

   
   ![image](https://drive.google.com/uc?export=view&id=1fXMlQZc-GRDlp1kdVDd0JAf7eY6qT5_H)


   The red cells should be filled by the user with the used markers. Then the user has to click on the SUBMIT button, which triggers the renaming of the tiff images and their patient ID subfolders. The tiff images will be evaluated and you will get data in the output window such as how many batches there are for each patient ID, which of them are selected for alignment and which are not (since they have only one batch) and what markers, files and their size each patient ID has. Also, infos.txt file will be updated by adding markers from the table entered by the user.


   ![image](https://drive.google.com/uc?export=view&id=1fhwvf2dtons7szrDAmC5p7oa0V3o_3KT)


3. The next step is `ALIGNMENT` (im-jy-package). You will be prompted to set some parameters like `Background Parameters` and `Overwrite option`. After you have confirmed the selection by clicking `OK` (`Cancel` ends the step), the matching of all directories sorted by `patientID` is performed. Before alignment the number of tiff images will be adjusted to have the same number of files for each separate patientID by copies of the dapi file in the certain folder(s). If the image is corrupted, it will be copied to the error folder `error_subfolder` in `02_alignment`.
   

   ![image](https://drive.google.com/uc?export=view&id=1qTd2QW7XyAbtN2KOxD1hrHnxF97trbyS)
   
   During the alignment three temporary folders `temp`, `out` and `transforms` are created in `02_alignment` if input data are in `01_input_dir`. These temporary subsubfolders are emptied after alignment of each `patientID` and deleted after the alignment is finished for all `patientID`s. After successful alignment the dapi files are treated with the background subtraction and are combined with other channel images of the certain `patientID` into a stack and stored in the folder `02_alignment` or the input of misaligned data from `01_input_dir` is copied to the folder `02_01_input_to_precrop`.


4. The next step is `REALIGNMENT` (im-jy-package). In this step the folder `02_01_input to precrop` will be checked. You need to set some parameters like `Hyperstack Parameters` and `Overwrite option`. By pressing the `OK` button (`Cancel` ends the step) the hyperstacks will be created for each date for each `patientID`. 
   

   ![image](https://drive.google.com/uc?export=view&id=1PwwjVpY1yK6Hy_Oopzhm5z7nRUwzIRw5)


   If it is not empty, the hyperstacks for each patient ID and date are created and saved in the `02_02_stacks` folder. If the image is corrupted, the images of a certain date will be copied to the error folder `error_subfolder` for each `patientID`. As next, the user is prompted to set `Overwrite option`. If you press `Ok` (`Cancel` ends the step) the hyperstack of a certain `patientID` of a certain date is loaded, and you have to set the region of interest and confirm your selection. 
   

   ![image](https://drive.google.com/uc?export=view&id=1b-Iic1xFFn_P1tFwFrGeROqw_vju_WQW)


   After that all hyperstacks of this `patientID` are loaded with identic region of interest. You can adjust it by clicking inside it and moving. (Not recommended: You can also change the size of the region of interest if needed). After that you need to confirm it by clicking `Ok` in the `Action required` dialog. 
   

   ![image](https://drive.google.com/uc?export=view&id=1edKobjy015l790w-L7q4L-Wy1oovqTee)


   Then the images will be cropped and stored as separate images in the folder `'02_03_cropped_input` in subfolders sorted by patient and date having the form `date_patientID` and their files `date_patientID_channel.tif`. If the image is corrupted, the images of a certain date will be copied to the error folder `error_subfolder` in the folder `02_02_stacks`. The next substep is to realign the problem data. The user will be asked to set some parameters. 
   

   ![image](https://drive.google.com/uc?export=view&id=1qTd2QW7XyAbtN2KOxD1hrHnxF97trbyS)


   They have to check if the input is in the folder `02_03_cropped_input` and set the same parameters as in the `ALIGNMENT` step. The data will be realigned and after alignment the image files will be aligned and saved in the folder `02_alignment` or the input data will be saved in the folder `02_01_input_to_precrop`


5. In the next step `CROPPING` (im-jy-package) all image stacks in `02_alignment` are cropped. The user is prompted to set `Overwrite option`. If you press `Ok` (`Cancel` ends the step) 
   

   ![image](https://drive.google.com/uc?export=view&id=1bbeMgmctzmsLJBc9MzxWpCYSIKkIeqxU)


   the stack of a certain `patientID` is loaded, and you have to set the region of interest and confirm your selection by clicking `Ok` in the `Action required` dialog.
   

   ![image](https://drive.google.com/uc?export=view&id=1edKobjy015l790w-L7q4L-Wy1oovqTee)


   Then the stack is cropped and saved in the folder `02_alignment` with the extension `_Cropped`


6. In the next step `BACKGROUNDADJUSTMENT` (im-jy-package) the background subtraction takes place. Thereby the user is prompted to set the background parameter settings. Then the user is prompted to set `Overwrite option`. If you press `Ok` (`Cancel` ends the step), the background substractioncorresponding marker images.
   

   ![image](https://drive.google.com/uc?export=view&id=16aw2RnzqdsGoSsbC8KzNUMvElswYDJd1)


   The cropped stacks of images from `02_alignment` are processed and each slice of each aligned stack is saved with (extension:_no_background) and without background subtraction (extension:_background_sub) in the folder `06_bg_processed`


7. In the next step `MERGING_CHANNELS` (im-jy-package), the images from dapi and other channels from the step background substraction selected by the user are merged and saved in the folder `07_mergedChannels`. At the beginning, the user is asked to set parameters for the selection of the dapi image for each patient ID and the images of the channels to be merged with the selected dapi image. There is an option to select all markers. Then the user is prompted to set `Overwrite option`. If you press `Ok` (`Cancel` ends the step), the selected marker images are merged with the selected dapi image.


   ![image](https://drive.google.com/uc?export=view&id=1xWoPaQUTFVtYvu_JDKnVwl7O987iDvaX)


8. The next step is `DAPISEGMENTATION` (multiplex, cellsegpackage). Thereby the data are put to the correct input form and segmented using the CellSeg package (the scripts and pretrained model from `https://github.com/michaellee1/CellSeg` are adapted to our purpose, contour to entire filling of segmented cells (cell masks), separating neighboured cell masks from each other). Then the segmentation file with the cells of different colour (grayscale gradient) is converted to the binary mask (multiplex), the small holes in the cells are filled and small artifacts removed. Then the masks are resized (im-jy-package) to have the same size as origin segmented image 


9. After the last pipeline step `OUTPUT` all other subfolders in the folder workingDir are deleted and only the final subfolder "o6_results_output" and metadata.csv remain in the main folder

## Notes:
+ if errors are occurring while the execution, there are outputs on the console of FiJi and in AnacondaPrompt and the history is stored in logs.log in the execution folder
+ during the execution, there is also an output on the console of FiJi and AnacondaPrompt and is stored in logs.log
+ The execution times of the steps of image processing is outputed in the end on the console of AnacondaPrompt and in logs.log
