# multiplex.__init__.py
import multiplex.gui as gui
from multiplex.ppconfig import PIPELINEConfig
from tkinter import *
from multiplex.setup_logger import logger


def main():
    pcf = PIPELINEConfig()
    window = Tk()
    # Calling the App class function
    object1 = gui.App(window, pcf.pipeline_params, pcf.stitching_steps, pcf.alignment_steps, pcf.dapiseg_steps, pcf.merge_channels_steps, pcf.bg_steps,
                      pcf.cropping_experimental_steps, pcf.fast_button_step, pcf.subfolders_list,
                      pcf.realignment_subfolder_list, pcf.dapiseg_subfolder_list, pcf.command_arguments,
                      pcf.packages, pcf.envs, pcf.main_work_dir, pcf.main_py_PATH, pcf.macro_py_PATH, pcf.csv_ext, pcf.metadata_file)
    window.title("Running the Steps of Multiplex Pipeline")
    window.geometry('1100x540')
    window.config(background="black")
    window.mainloop()
