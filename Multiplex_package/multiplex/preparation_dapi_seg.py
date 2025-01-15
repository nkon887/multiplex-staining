# multiplex.preparation_dapi_seg.py
import os
import cv2
import numpy as np
import multiplex.setup_logger
import logging
import multiplex.helpertools as ht
from PIL import Image as Img
import tkinter
from tkinter import N, S, E, W
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

# multiplex.preparation_dapi_seg.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.main.preparation_dapiSeg')


class PreparationDapiSeg:
    def __init__(self, input_dir, output_dir, dapi_str, tiff_ext, working_dir, forceSave):
        self.input_folder = input_dir
        self.output_folder = output_dir
        self.dapi_str = dapi_str
        self.tiff_ext = tiff_ext
        self.tempfile_dapiseg = os.path.join(working_dir, "temp_dapiseg.csv")
        self.force_save = int(forceSave[0])

    # def getting_input_parameters(self, dapi_files):
    #     data_together = []
    #     window = tkinter.Tk()
    #     window.title("Segmentation Parameters Form")
    #     frame = tkinter.Frame(window)
    #     frame.pack()
    #     # Saving Dapi Info
    #     dapi_info_frame = tkinter.LabelFrame(frame, text="Choose DAPI image for each patient you want to use for "
    #                                                      "segmentation")
    #     dapi_info_frame.grid(row=0, column=0, padx=20, pady=10, sticky=N + S + E + W)
    #     dapi_text = ScrolledText(dapi_info_frame, width=100, height=10)
    #     dapi_text.grid(row=1, column=0)
    #     dapi_filenames = dapi_files.keys()
    #     dapi_selected = []
    #     patientIDs = []
    #     no_selection = "Not Selected"
    #     for dapi_filename in dapi_filenames:
    #         if not dapi_files[dapi_filename]:
    #             dapi_selected.append(tkinter.StringVar(value=no_selection))
    #         else:
    #             dapi_selected.append(tkinter.StringVar(value=dapi_files.get(dapi_filename)[0]))
    #     for i, subfolder in enumerate(dapi_filenames):
    #         patientID = os.path.basename(subfolder)
    #         patientIDs.append(patientID)
    #         dapi_channels = dapi_files.get(subfolder)
    #         dapi_label = tkinter.Label(dapi_text, text=patientID)
    #         dapi_combobox = ttk.Combobox(dapi_text, values=dapi_channels, textvariable=dapi_selected[i], width=70)
    #         dapi_label.grid(row=0, column=0)
    #         dapi_combobox.grid(row=0, column=1)
    #         dapi_text.window_create('end', window=dapi_label)
    #         dapi_text.insert('end', '   ')
    #         dapi_text.window_create('end', window=dapi_combobox)
    #         dapi_text.insert('end', '\n\n')
    #
    #     for widget in dapi_info_frame.winfo_children():
    #         widget.grid_configure(padx=10, pady=5)
    #
    #     # Buttons
    #     buttons_frame = tkinter.Frame(frame)
    #     buttons_frame.grid(row=4, column=0, sticky="", padx=20, pady=10)
    #
    #     def Stop():
    #         # declare variable as nonlocal variable
    #         nonlocal data_together
    #
    #         # get the value of the entry box before destroying window
    #         for i, patientID in enumerate(patientIDs):
    #             data = {}
    #             # Dapi info
    #             selected_dapi_value = dapi_selected[i].get()
    #             if selected_dapi_value != no_selection:
    #                 data['dapiseq_patientID'] = patientID
    #                 data['dapiseq_selected_dapi_file'] = selected_dapi_value
    #             data_together.append(data)
    #         window.destroy()
    #
    #     OKbutton = tkinter.Button(buttons_frame, text="OK", command=Stop)
    #     OKbutton.grid(row=0, column=0)
    #     Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window.destroy)
    #     Cbutton.grid(row=0, column=1)
    #     for widget in buttons_frame.winfo_children():
    #         widget.grid_configure(ipadx=15, padx=10, pady=5)
    #     buttons_frame.grid_rowconfigure(0, weight=1)
    #     buttons_frame.grid_columnconfigure(0, weight=1)
    #     window.mainloop()
    #     return data_together

    def process(self):
        input_dir = self.input_folder
        subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
        subfolders.pop(0)
        if not subfolders:
            logger.warning(input_dir + " is empty. Doing nothing")
            return
        if not os.path.exists(self.tempfile_dapiseg):
            logger.warning("No csv file was found. Something went wrong when setting the parameters in the the "
                           "dialog for setting the parameters for channel merging. The user may have cancelled it or "
                           "deleted it. Repeat the step if you want to merge the channel image "
                           "with the DAPI image and set the parameters. Doing nothing.")
            return
        dapi_files_dict = {}
        for subfolder in subfolders:
            dapi_files = ht.dapi_tiff_image_filenames(subfolder, self.dapi_str, self.tiff_ext)
            dapi_files_dict[subfolder] = dapi_files
            if not dapi_files:
                logger.warning("Image file of dapi channel isn't found. Please check the filename and change  it if "
                               "needed")

        dapis_selected = {}
        # for subdir in [x[0] for x in os.walk(self.input_folder) if not x[0] in self.input_folder]:
        #      dapis = []
        #      for filename in os.listdir(subdir):
        #          if f"0{self.dapi_str}" in str(filename) and "_backgroundSub" in str(filename):
        #              dapis.append(filename)
        #          dapis.sort()
        #      dapis_selected = dapis[1]
        try:
            data = self.read_data_from_csv(self.tempfile_dapiseg)
        except:
            logger.exception("Could not get the input parameters. Exiting")
            return
        dapis_selected = data
        # dapis_selected = self.getting_input_parameters(dapi_files_dict)
        # get all files of directory
        for case in dapis_selected:
            # adjust contrast of each file (substract 5 from intensity)
            # subtract 5 from all pixels in our image and make it darker
            subdir = case["dapiseg_patientID"]
            filename = case["dapiseg_selected_dapi_file"]
            file_folder_name = os.path.splitext(os.path.basename(filename))[0]
            input_image_path = ht.correct_path(self.input_folder, subdir, filename)
            if os.path.exists(input_image_path):
                # create folders with files
                filefolder_path = ht.correct_path(self.output_folder, file_folder_name)
                if not os.path.exists(filefolder_path):
                    os.mkdir(filefolder_path)
                output_path = ht.correct_path(filefolder_path, filename)
                image = cv2.imread(ht.correct_path(self.input_folder, subdir, filename))
                width, height, _ = image.shape
                if width < 801 and height < 801:
                    pil_image = self.refomat_image(input_image_path)
                    open_cv_image = np.array(pil_image)
                    # Convert RGB to BGR
                    image = open_cv_image[:, :, ::-1].copy()
                m = np.ones(image.shape, dtype="uint8") * 5
                subtracted = cv2.subtract(image, m)
                # create folder input
                gray = cv2.cvtColor(subtracted, cv2.COLOR_BGR2GRAY)
                sub = Img.fromarray(gray.astype(np.uint8))
                if not os.path.exists(output_path) or self.force_save == 1:
                    sub.save(output_path)
                textfile_path = ht.correct_path(self.output_folder, "channelNames_" + file_folder_name + ".txt")
                if not os.path.exists(textfile_path) or self.force_save == 1:
                    f = open(textfile_path, "w+")
                    f.write(filename)
                    f.close()
            else:
                logger.warning(f"The file {input_image_path} cannot be found. Please check it")
        logger.info('Preparation of input for dapi segmentation is finished')

        # # get all files of directory
        # for subdir in [x[0] for x in os.walk(self.input_folder)]:
        #     for filename in os.listdir(subdir):
        #         if f"0{self.dapi_str}" in str(filename):
        #             # adjust contrast of each file (substract 5 from intensity)
        #             # subtract 5 from all pixels in our image and make it darker
        #             image = cv2.imread(ht.correct_path(self.input_folder, subdir, filename))
        #             m = np.ones(image.shape, dtype="uint8") * 5
        #             subtracted = cv2.subtract(image, m)
        #             file_folder_name = os.path.splitext(os.path.basename(filename))[0]
        #             # create folders with files
        #             filefolder_path = ht.correct_path(self.output_folder, file_folder_name)
        #             if not os.path.exists(filefolder_path):
        #                 os.mkdir(filefolder_path)
        #             output_path = ht.correct_path(filefolder_path, filename)
        #             # create folder input
        #             gray = cv2.cvtColor(subtracted, cv2.COLOR_BGR2GRAY)
        #             sub = Image.fromarray(gray.astype(np.uint8))
        #             sub.save(output_path)
        #             f = open(ht.correct_path(self.output_folder, "channelNames_" + file_folder_name + ".txt"), "w+")
        #             f.write(filename)
        #             f.close()
        # logger.info('Preparation of input for dapi segmentation is finished')

    def read_data_from_csv(self, tempfile):
        with open(tempfile) as f:
            headers = next(f).rstrip().split(',')
            data = [dict(zip(headers, line.rstrip().split(','))) for line in f]
        return data

    def refomat_image(self, ImageFilePath):
        from PIL import Image
        image = Image.open(ImageFilePath, 'r')
        image_size = image.size
        width = image_size[0]
        height = image_size[1]

        bigside = 801
        if width < height:
            background = Image.new('RGBA', (bigside, height), color='black')
            offset = (0, 0)
        else:
            background = Image.new('RGBA', (width, bigside), color='black')
            offset = (0, 0)

        background.paste(image, offset)
        background = background.convert('RGB')
        logger.info("Image has been resized !")
        return background
