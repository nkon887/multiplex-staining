# multiplex package

This package consists of the steps for preprocessing of czi images which are converted to tiff images using FIJI and its modules
The following steps of multiplex fluorescence immunostaining analysis pipeline for preprocessing of czi images are in this package:

1. DATACHECK
2. DAPISEGMENTATION
3. OUTPUT

This package contains also config scripts and GUI scripts of multiplex fluorescence immunostaining analysis pipeline
and setuplogger and also execution scripts for all the steps of multiplex fluorescence immunostaining analysis pipeline. Also, this package contains integration test and unit test.
Integration test checks if gui  of the package multiplex correctly defined and its objects (buttons) are created and are as expected configured. The unit test checks the function correct_path of multiplex.helpertools 
In order to execute tests the following steps should be done.

1. Go to Start and search for "Anaconda Prompt" and click to open. Start the terminal. To navigate to the  execution  folder of the cloned git repository and execute, run the commands in the terminal (if the conda environment myenv already created).
    ```Bash
    cd path-to-the-cloned-multiplex-staining/multiplex-staining/Multiplex_Package/
    conda activate myenv    
    python -m pytest -pyargs multiplex
    ```
   If conda environment myenv doesn't exist, the run the following commands in terminal:
    ```Bash
    cd path-to-the-cloned-multiplex-staining/multiplex-staining/Multiplex_Package/
    pip install pytest
    pip install yargs
    pip install "git+https://github.com/nkon887/multiplex-staining.git#multiplex&subdirectory=Multiplex_package"   
    python -m pytest -pyargs multiplex
    ```
   The output should look then as follows
 ================================================= test session starts =================================================
platform win32 -- Python 3.10.12, pytest-7.2.0, pluggy-1.0.0
rootdir: C:\Users\nko88\PycharmProjects\multiplex-staining\Multiplex_package
collected 3 items

multiplex\tests\integration\integration_image_preparation_test.py ..                                             [ 66%]
multiplex\tests\unit\helpertools_correct_path_test.py .                                                          [100%]

================================================== 3 passed in 6.04s ==================================================
  