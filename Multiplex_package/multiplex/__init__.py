# multiplex.__init__.py
import multiplex.gui as gui
from multiplex.ppconfig import PIPELINEConfig
from tkinter import *
from multiplex.setup_logger import logger
import subprocess


def create_conda_environment(env_name, requirements_file):
    env_exists = False
    try:
        subprocess.run(f"conda activate {env_name}", shell=True, check=True)
        env_exists = True
    except subprocess.CalledProcessError as e:
        pass
    if not env_exists:
        subprocess.run(f"conda env create -f {requirements_file}", shell=True)
        logger.info(f"Conda environment {env_name} created.")
    else:
        logger.info(f"{env_exists} Conda environment {env_name} already exists.")


def main():
    import gdown
    import os
    pcf = PIPELINEConfig()
    for key in pcf.envs:
        if key not in "" and not os.path.exists(list(pcf.envs[key])[0]):
            gdown.download(list(pcf.envs[key])[1], list(pcf.envs[key])[0], quiet=False)
    for key in pcf.envs:
        if key not in "":
            create_conda_environment(key, list(pcf.envs[key])[0])
    window = Tk()
    # Calling the App class function
    object1 = gui.App(window, pcf.pipeline_params, pcf.dapiseg_steps, pcf.merge_channels_steps, pcf.bg_steps,
                      pcf.cropping_experimental_steps, pcf.fast_button_step, pcf.subfolders_list,
                      pcf.realignment_subfolder_list, pcf.dapiseg_subfolder_list, pcf.command_arguments,
                      pcf.packages, pcf.envs, pcf.main_work_dir, pcf.main_py_PATH, pcf.macro_py_PATH, pcf.csv_ext, pcf.metadata_file)
    window.title("Running the Steps of Multiplex Pipeline")
    window.geometry('880x510')
    window.config(background="black")
    window.mainloop()
