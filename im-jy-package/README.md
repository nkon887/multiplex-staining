# multiplex-staining Preprocessing of images

## Description
This pipeline enables the user to process and prepare multiplex staining
microscopy images for further cell population analysis
It works for the tiff images

3, 4 channel images per datum corresponding to one experiment are treated individually. Since the position of the region of interest changes from date to date, the channel images must be aligned. If the alignment of the raw data does not work properly, the images of each date are treated separately as a batch and processed (cropped) to repeat the alignment. It is possible to process more than one batch in one pass. After this process, the images are processed so that they are ready for segmentation.

## Requirements

1. Python > 3.3
2. Fiji + Turboreg + Hyperstackreg (Jython)
3. Git Bash
4. See package list  `environment.yml` to create the environment `multiplex`
## Set-Up
1. Install conda https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html (only once)
2. Clone this repository. (only once)

    ```Bash
    git clone https://github.com/nkon887/multiplex-staining.git
    ```
3. Create the environment from the environment.yml file using terminal (only once):
   ```Bash
      conda env create -f env_multiplex.yml
    ```
4. Copy the jar file to `jars/Lib`. `Lib` may not exist, yet (only once).

    ```Bash
    mkdir -p path-to-ImageJ/jars/Lib
    cp target/im-jy-package-0.1.0-SNAPSHOT.jar path-to-ImageJ/jars/Lib/
    ```
5. Set up the `FIJIPATH` environment variable:
   Go to `Start` - `Edit system variables` - `Environment variables`. There set the system variable `Variable name` to `FIJIPATH` and `Variable value` to the file location of ImageJ-win64.exe (of your `FIJI`)
6. Copy the folder `wdir_scripts` to directory of your choice
7. Start the bash terminal, navigate to the  `wdir_scripts`  folder and run the following bash script `exec.sh`
    ```Bash
    conda activate multiplex
    /bin/sh exec.sh
    ```
8. The execution creates a directory structure for the processed image files
   ```Explorer
        workingDir/
                  /01_input
                  /02_alignment_SV
                  /03_input_to_precrop
                  /04_stacks
                  /05_cropped_input
                  /06_bg_processed
                  /07_mergedChannels
   ```
9. You will be asked to specify the input folder (default (already set) during `image_preparation`: `workindir/input_dir`)
You have to put the tiff files after stitching into the folder `input_dir`  and the file `infos.txt` so that the data and channels in the `image preparation table`. The form it must have is:
   ```txt
   ...
   221123
   c0 0dapi
   c1 heppar1 (647)
   c2 mpo (750
   221124
   c0 0dapi
   c1 iba1(donotuse) (647)
   c2 cd20 (750)
   ...
   ```
   An example file can be found in the ´wdir_scripts´ folder in the subfolder ´example/01_inputdir´. In the example subfolder you can also find the example subfolder structure for the current pipeline.
   If you click the `Browse` button, the table will be updated when something changes in the `infos.txt` file. You can enter data and channels into the table manually. Once this is done, you can click the `Submit` button. It will be processed in such a way that all folders will be renamed in `input_dir` that have the form `date_patientID` and their files `date_patientID_channel.tif` after renaming
   At the end you will also get in the window `Output` evaluation file paths and the width and height values of the tiff images sorted by `patientID` and `marker`. Above you see also the progress bar `Progress` where you see if the data are processed (white: not processed, blue: processed)  
You can adjust the width and height of the image and save it in the appropriate folder in `01_input_dir`. If you want to continue, you must press `Exit`.
10. The next step is `alignment`. You will be prompted to set some parameters like `Directory Path`, `Background Parameters` and `Overwrite option`. After you have confirmed the selection by clicking `OK` (`Cancel` ends the step), the matching of all directories sorted by `patientID` is performed. Before alignment the number of tiff images will be adjusted to have the same number of files for each separate patientID by copies of the dapi file in the certain folder(s). If the image is corrupted, it will be copied to the error folder `error_subfolder` in `02_alignment_SV` 
    During the alignment three temporary folders `temp`, `out` and `transforms` are created in `02_alignment_SV` if input data are in `01_input_dir` and are emptied after alignment of each `patientID` and deleted after the alignment is finished for all `patientID`s. After the alignment, the files are combined into a stack and stored in the folder `02_alignment_SV` or the raw data of misaligned data from `input_dir` is copied to the folder `03_input_to_precrop`. After successful alignment the dapi files are treated with the background subtraction and are combined with other channel images of the certain `patientID` into a stack and stored in the folder `02_alignment_SV`
11. The next step is to check the folder `03_input to precrop`. You need to set some parameters like `Directory Path`, `Hyperstack Parameters` and `Overwrite option`. By pressing the `OK` button (`Cancel` ends the step) the hyperstacks will be created for each date for each `patientID`. If it is not empty, the hyperstacks for each patient ID and date are created and saved in the `04_stacks` folder. If the image is corrupted, the images of a certain date will be copied to the error folder `error_subfolder` for each `patientID` 
12. In the next step `cropping` the user is prompted to set `Overwrite option`. If you press `Ok` (`Cancel` ends the step) the hyperstack of a certain `patientID` of a certain date is loaded, and you have to set the region of interest and confirm your selection. After that all hyperstacks of this `patientID` are loaded with identic region of interest. You can adjust it by clicking inside it and moving. (Not recommended: You can also change the size of the region of interest if needed). After that you need to confirm it by clicking `Ok` in the `Action required` dialog. Then the images will be cropped and stored as separate images in the folder `'05_cropped_input` in subfolders sorted by patient and date having the form `date_patientID` and their files `date_patientID_channel.tif`. If the image is corrupted, the images of a certain date will be copied to the error folder `error_subfolder` in the folder `04_stacks`  
13. The next step is to realign the problem data. The user will be asked to set some parameters. They have to check if the input is in the folder `05_cropped_input` and set the same parameters as in the `alignment` step. The data will be realigned and after alignment the image files will be aligned and saved in the folder `02_alignment_SV` or the raw data will be saved in the folder `03_input_to_precrop`
14. In the next step all image stacks in `alignment_SV` are cropped. the user is prompted to set `Overwrite option`. If you press `Ok` (`Cancel` ends the step) the stack of a certain `patientID` is loaded, and you have to set the region of interest and confirm your selection by clicking `Ok` in the `Action required` dialog. Then the stack is cropped and saved in the folder `alignment_SV` with the extension `_Cropped`
15. In the next step the background subtraction takes place. The cropped stacks of images from `02_alignment_SV` are processed and each slice of each aligned stack is saved with (extension:_no_background) and without background subtraction (extension:_background_sub) in the folder `06_bg_processed`
16. In the last step, the images from dapi and other channels from the step background substraction selected by the user are merged and saved in the folder `07_mergedChannels`. At the beginning, the user is asked to set parameters for the selection of the dapi image for each patient ID and the images of the channels to be merged with the selected dapi image  
## Notes:
+ if errors are occurring while the execution, there are outputs on the console of FiJi and in GitBash 
+ during the execution, there is also an output on the console of FiJi and GitBash
+ The execution times of the steps of image processing is outputed in the end on the console of GitBash 