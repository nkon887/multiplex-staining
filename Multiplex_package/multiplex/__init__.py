# multiplex.__init__.py
import sys

import multiplex.gui as gui
from multiplex.ppconfig import PIPELINEConfig
from tkinter import *
from multiplex.setup_logger import logger

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import getopt
    try:
        opts, args = getopt.getopt(args, 'hmote:', ['help', 'path='])
    except getopt.GetoptError:
        print('usage: python -m multiplex --path=<envpath>, where tar envs are')
        sys.exit(2)
    tar_envs_path = ''
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('usage: python -m multiplex --path=<envpath>, where tar envs are')
            sys.exit()
        elif opt in ('-p', '--path'):
            tar_envs_path = arg
    print("tar_envs_path")
    print(tar_envs_path)
    pcf = PIPELINEConfig()
    window = Tk()
    # Calling the App class function
    object1 = gui.App(window, pcf.pipeline_params, pcf.stitching_steps, pcf.alignment_steps, pcf.dapiseg_steps, pcf.merge_channels_steps, pcf.bg_steps,
                      pcf.cropping_experimental_steps, pcf.fast_button_step, pcf.subfolders_list,
                      pcf.realignment_subfolder_list, pcf.dapiseg_subfolder_list, pcf.command_arguments,
                      pcf.packages, pcf.envs, pcf.main_work_dir, pcf.main_py_PATH, pcf.macro_py_PATH, pcf.csv_ext, pcf.metadata_file, tar_envs_path)
    window.title("Running the Steps of Multiplex Pipeline")
    window.geometry('1100x540')
    window.config(background="black")
    window.mainloop()
