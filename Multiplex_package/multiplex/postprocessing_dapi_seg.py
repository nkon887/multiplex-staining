# multiplex.postprocessing_dapi_seg.py
import os.path
import PIL
from PIL import Image as Img
import cv2
import numpy as np
import multiplex.helpertools as ht
from skimage import exposure

PIL.Image.MAX_IMAGE_PIXELS = 933120000
import multiplex.setup_logger
import logging
import tkinter
from tkinter import *

# multiplex.postprocessing_dapi_seg.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.main.postprocessing_dapiSeg')


class PostProcessingDapiSeg:
    def __init__(self, input_dir, output_dir, tiff_ext):
        self.input_folder = input_dir
        self.output_folder = output_dir
        self.tiff_ext = tiff_ext
        self.no_selection = "Not Selected"
        self.selection = "Selected"

    def getting_forceSave_parameter(self):
        force_Save = ""
        window = tkinter.Tk()
        window.title("Segmentation Postprocessing Form")
        frame = tkinter.Frame(window)
        frame.pack()
        # Force Save
        force_save_frame = tkinter.LabelFrame(frame, text="Force Save Option")
        force_save_frame.grid(row=3, column=0, sticky="news", padx=20, pady=10)

        accept_var = tkinter.StringVar(value=self.no_selection)
        terms_check = tkinter.Checkbutton(force_save_frame, text="forceSave",
                                          variable=accept_var, onvalue=self.selection, offvalue=self.no_selection)
        terms_check.grid(row=0, column=0)

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=4, column=0, sticky="", padx=20, pady=10)

        def Stop():
            # declare variable as nonlocal variable
            nonlocal force_Save

            # get the value of the entry box before destroying window
            force_Save = accept_var.get()
            window.destroy()

        OKbutton = tkinter.Button(buttons_frame, text="OK",
                                  command=Stop
                                  )
        OKbutton.grid(row=0, column=0)
        Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window.destroy)
        Cbutton.grid(row=0, column=1)
        for widget in buttons_frame.winfo_children():
            widget.grid_configure(ipadx=15, padx=10, pady=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        window.mainloop()
        return force_Save

    def process(self):
        forceSave = self.getting_forceSave_parameter()
        logger.info(forceSave)
        output_paths = []
        for im in os.listdir(self.input_folder):
            output_path = ht.correct_path(self.output_folder, im)
            output_paths.append(output_path)
        if (not all(os.path.exists(output_path) for output_path in
                    output_paths)) or forceSave != self.selection:
            # Load with PIL
            for im in os.listdir(self.input_folder):
                image_file_path = ht.correct_path(self.input_folder, im)
                output_path = ht.correct_path(self.output_folder, im)
                if im.endswith(self.tiff_ext) and not (os.path.isdir(im)):
                    image_file = Img.open(image_file_path)

                    # Make into Numpy array and normalise
                    na = np.array(image_file, dtype=np.uint8)
                    threshold = 0
                    na[na > threshold] = 1
                    contour, hier = cv2.findContours(na, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

                    for cnt in contour:
                        cv2.drawContours(na, [cnt], 0, 1, -1)

                    se1 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                    se2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

                    mask = cv2.morphologyEx(na, cv2.MORPH_CLOSE, se1)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, se2)

                    out = na * mask
                    threshold = 0
                    out[out > threshold] = 1
                    # Save
                    intimg = exposure.rescale_intensity(out, in_range=(0, 1))
                    cv2.imwrite(output_path, intimg)
        else:
            logger.warning("The files of " + self.output_folder + " exists. Skipping")
        logger.info("Postprocessing is finished")
