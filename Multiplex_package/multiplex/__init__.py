# multiplex/__init__.py
import sys

import multiplex.gui as gui
from multiplex.ppconfig import PIPELINEConfig
from tkinter import *

# --- logger -------------------------------------------------
try:
    from multiplex.setup_logger import logger  # configured logger
except Exception:  # minimal fallback logger
    import logging
    logger = logging.getLogger("multiplex")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

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

    pcf = PIPELINEConfig()
    window = Tk()
    # Calling the App class function
    object1 = gui.App(window, pcf.pipeline_params, pcf.stitching_steps, pcf.alignment_steps, pcf.dapiseg_steps, pcf.merge_channels_steps, pcf.bg_steps,
                      pcf.cropping_experimental_steps, pcf.fast_button_step, pcf.subfolders_list,
                      pcf.realignment_subfolder_list, pcf.dapiseg_subfolder_list, pcf.command_arguments,
                      pcf.packages, pcf.envs, pcf.main_work_dir, pcf.main_py_PATH, pcf.macro_py_PATH, pcf.csv_ext, pcf.metadata_file, tar_envs_path)
    window.title("CytoPrixm")
    window.configure(bg="#121212")
    window.minsize(1200, 750)
    window.geometry('1500x900')
    window.mainloop()
