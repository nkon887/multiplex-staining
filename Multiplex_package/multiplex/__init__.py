# multiplex.__init__.py
import multiplex.gui as gui
from multiplex.ppconfig import PIPELINEConfig
from tkinter import *
from multiplex.setup_logger import logger


def main():
    window = Tk()
    pcf = PIPELINEConfig()
    # Calling the App class function
    object1 = gui.App(window, pcf.pipeline_params, pcf.dapiseg_steps, pcf.merge_channels_steps, pcf.subfolders_list,
                      pcf.realignment_subfolder_list, pcf.dapiseg_subfolder_list, pcf.command_arguments,
                      pcf.packages, pcf.envs, pcf.main_work_dir, pcf.main_py_PATH, pcf.macro_py_PATH)
    window.title("Running the Steps of Multiplex Pipeline")
    window.geometry('880x510')
    window.config(background="black")
    window.mainloop()
