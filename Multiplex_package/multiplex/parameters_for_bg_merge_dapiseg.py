import csv
import logging
import os
import re
import tkinter
from functools import partial
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import helpertools as ht
from ppconfig import PIPELINEConfig

# im-jy-package.merging_channels.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.SettingParams_BGMergeDapiseg')


class SettingParams:
    def __init__(self, bg_input_dir, txt_dir, infos_txt, merge_dapiseg_input_dir, tiff_ext, dapi_str, metadata_csv_file,
                 working_dir, csv_ext):
        self.bg_input_dir = bg_input_dir
        self.txt_dir = txt_dir
        self.infos_txt = infos_txt
        self.merge_dapiseg_input_dir = merge_dapiseg_input_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str
        self.tempfile = os.path.join(self.merge_dapiseg_input_dir, "temp.csv")
        self.working_dir = working_dir
        self.csv_ext = csv_ext
        self.metadata_csv_file = metadata_csv_file

    def get_channels(self, subfolder, exc_channel):
        # for merge
        channels = []
        for subfolder_file in os.listdir(subfolder):
            filename = os.path.basename(subfolder_file)
            if filename.endswith(self.tiff_ext) and not (exc_channel in filename):
                channel = '_'.join(filename.split('.')[0].split('_')[2:])
                channels.append(channel)
        return sorted(list(set(channels)))

    def read_markers_from_txt_file(self):
        channel_markers = []
        folder = self.txt_dir
        logger.info(folder)
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(self.infos_txt)
        ]
        logger.info(ht.correct_path(folder, fnames[0]))
        if len(fnames) == 1:
            with open(ht.correct_path(folder, fnames[0])) as f:
                # read all lines in a list
                lines = f.readlines()
                for i, line in enumerate(lines):
                    # check if string present on a current line
                    if not re.match(r'^\d{6}$', line):
                        channel_marker_str = lines[i].strip()
                        channel_marker_list = channel_marker_str.split(" ")
                        check_length = len(channel_marker_list)
                        if check_length == 2:
                            channel_markers.append(channel_marker_list[1])
        channel_markers = list(set(channel_markers))
        return channel_markers

    def read_markers_from_csv_file(self, exc_channel):
        channel_markers = []
        folder = self.working_dir
        logger.info(folder)
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(
                self.csv_ext) and f.lower() == self.metadata_csv_file
        ]
        logger.info(ht.correct_path(folder, fnames[0]))
        data = {}
        channel_list = [i for dic in data for i in dic.keys() if
                        "channel" in i and "marker" not in i and dic[i] != "" and exc_channel not in dic[i]]
        channels = {}
        if len(fnames) == 1:
            data = ht.read_data_from_csv(ht.correct_path(folder, self.metadata_csv_file))
            for dic in data:
                for ch in channel_list:
                    channels[ch] = dic[ch]
            for dic in data:
                for ch in channels:
                    channel_markers.append(dic["marker for " + ch])
        channel_markers = list(set(channel_markers))
        return channel_markers

    def get_dapis_and_subfolders_from_csv_file(self, input_dir):
        folder = self.working_dir
        logger.info(folder)
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(
                self.csv_ext) and f.lower() == self.metadata_csv_file
        ]
        logger.info(ht.correct_path(folder, fnames[0]))
        data = {}
        channel_list = [i for dic in data for i in dic.keys() if
                        "channel" in i and "marker" not in i and dic[i] != "" and self.dapi_str in dic[i]]
        channels = {}
        dates = [dic[i] for dic in data for i in dic.keys() if "date" in i]
        patientIDs = [dic[i] for dic in data for i in dic.keys() if "expID" in i]
        dapi_marker_list = []
        dapi_files_list = []
        input_dir_subfolders = []
        if len(fnames) == 1:
            data = ht.read_data_from_csv(ht.correct_path(folder, self.metadata_csv_file))
            for dic in data:
                for ch in channel_list:
                    channels[ch] = dic[ch]
            for dic in data:
                for ch in channels:
                    if self.dapi_str in dic[ch]:
                        dapi_marker_list.append(dic["marker for " + ch])
        dapi_marker_list = list(set(dapi_marker_list))
        for date, dapi, patientID in zip(dates, patientIDs, dapi_marker_list):
            dapi_files_list.append(
                os.path.join(input_dir, patientID, date + "_" + patientID + "_" + dapi + ".tif"))
            input_dir_subfolders.append(os.path.join(input_dir, patientID))
        return dapi_files_list, input_dir_subfolders

    def getting_input_parameters(self, dapi_files, markers):
        window_form = tkinter.Tk()
        window_form.title("Merge BG DapiSeg Form")
        frame = tkinter.Frame(window_form)
        frame.pack()
        # Saving Marker BG Info
        data_together_bg = []
        marker_info_frame_bg = tkinter.LabelFrame(frame,
                                                  text="Choose Radius values for each marker")
        marker_info_frame_bg.grid(row=0, column=0, padx=20, pady=10, sticky=N + S + E + W)
        marker_text_bg = ScrolledText(marker_info_frame_bg, width=100, height=10)
        marker_text_bg.grid(row=1, column=0)

        marker_filenames_bg = markers
        marker_selected_bg = []
        no_selection = "Not Selected"
        markers_bg = list(set([sstr.split("_")[0] for sstr in marker_filenames_bg]))
        # default_values = [tkinter.StringVar(value="50")] * len(markers_bg)
        for marker in markers_bg:
            if not markers_bg:
                marker_selected_bg.append(tkinter.StringVar(value="0"))
            else:
                marker_selected_bg.append(tkinter.StringVar(value="50"))
        values_ = [str(i) for i in list(range(100 + 1))]
        for i, marker in enumerate(markers_bg):
            marker_label_bg = tkinter.Label(marker_text_bg, text=marker)
            # var = StringVar(marker_text_bg)
            # var.set("50")
            marker_combobox_bg = ttk.Spinbox(marker_text_bg, values=values_, textvariable=marker_selected_bg[i],
                                             )
            marker_label_bg.grid(row=0, column=0)
            marker_combobox_bg.grid(row=0, column=1)
            marker_text_bg.window_create('end', window=marker_label_bg)
            marker_text_bg.insert('end', '   ')
            marker_text_bg.window_create('end', window=marker_combobox_bg)
            marker_text_bg.insert('end', '\n')
        for widget in marker_info_frame_bg.winfo_children():
            widget.grid_configure(padx=10, pady=5)

        # Saving Dapi Merge Info
        data_together_merge = []
        dapi_info_frame_merge = tkinter.LabelFrame(frame,
                                                   text="Choose DAPI image for each patient you want to use for merge")
        dapi_info_frame_merge.grid(row=1, column=0, padx=20, pady=10, sticky=N + S + E + W)
        dapi_text_merge = ScrolledText(dapi_info_frame_merge, width=100, height=10)
        dapi_text_merge.grid(row=2, column=0)

        dapi_filenames_merge = dapi_files.keys()
        dapi_selected_merge = []
        no_selection = "Not Selected"
        patientIDs_merge = []
        for dapi_filename in dapi_filenames_merge:
            if not dapi_files[dapi_filename]:
                dapi_selected_merge.append(tkinter.StringVar(value=no_selection))
            else:
                dapi_selected_merge.append(tkinter.StringVar(value=dapi_files.get(dapi_filename)[0]))
        for i, subfolder in enumerate(dapi_filenames_merge):
            patientID = os.path.basename(subfolder)
            patientIDs_merge.append(patientID)
            dapi_channels_merge = dapi_files.get(subfolder)
            dapi_label_merge = tkinter.Label(dapi_text_merge, text=patientID)
            dapi_combobox_merge = ttk.Combobox(dapi_text_merge, values=dapi_channels_merge,
                                               textvariable=dapi_selected_merge[i], width=70)
            dapi_label_merge.grid(row=0, column=0)
            dapi_combobox_merge.grid(row=0, column=1)
            dapi_text_merge.window_create('end', window=dapi_label_merge)
            dapi_text_merge.insert('end', '   ')
            dapi_text_merge.window_create('end', window=dapi_combobox_merge)
            dapi_text_merge.insert('end', '\n\n')

        for widget in dapi_info_frame_merge.winfo_children():
            widget.grid_configure(padx=10, pady=5)
        # Saving Channels Merge Info
        channels_frame_merge = tkinter.LabelFrame(frame, text="Choose channels of images you want to merge with DAPI")
        channels_frame_merge.grid(row=2, column=0, sticky="news", padx=20, pady=10)
        text_merge = ScrolledText(channels_frame_merge, width=100, height=10)
        text_merge.grid(row=3, column=0)
        channel_selected_merge = []
        for i in range(len(markers)):
            channel_selected_merge.append(tkinter.StringVar(value=no_selection))
        for i in range(len(markers)):
            cb_merge = tkinter.Checkbutton(text_merge, text=markers[i], bg='white', anchor='w',
                                           variable=channel_selected_merge[i],
                                           onvalue="Selected",
                                           offvalue=no_selection)
            text_merge.window_create('end', window=cb_merge)
            text_merge.insert('end', '\n')
        for widget in channels_frame_merge.winfo_children():
            widget.grid_configure(padx=10, pady=5)
        # Force Save Merge
        force_save_frame_merge = tkinter.LabelFrame(frame, text="Force Save Option")
        force_save_frame_merge.grid(row=4, column=0, sticky="news", padx=20, pady=10)

        accept_var_merge = tkinter.StringVar(value=no_selection)
        terms_check_merge = tkinter.Checkbutton(force_save_frame_merge, text="forceSave",
                                                variable=accept_var_merge, onvalue="Selected", offvalue=no_selection)
        terms_check_merge.grid(row=1, column=0)

        # Saving Dapi Seg Info
        data_together_dapiseg = []
        dapi_info_frame_dapiseg = tkinter.LabelFrame(frame,
                                                     text="Choose DAPI image for each patient you want to use for "
                                                          "segmentation")
        dapi_info_frame_dapiseg.grid(row=5, column=0, padx=20, pady=10, sticky=N + S + E + W)
        dapi_text_dapiseg = ScrolledText(dapi_info_frame_dapiseg, width=100, height=10)
        dapi_text_dapiseg.grid(row=6, column=0)
        dapi_filenames_dapiseg = dapi_files.keys()
        dapi_selected_dapiseg = []
        patientIDs_dapiseg = []
        for dapi_filename in dapi_filenames_dapiseg:
            if not dapi_files[dapi_filename]:
                dapi_selected_dapiseg.append(tkinter.StringVar(value=no_selection))
            else:
                dapi_selected_dapiseg.append(tkinter.StringVar(value=dapi_files.get(dapi_filename)[0]))
        for i, subfolder in enumerate(dapi_filenames_dapiseg):
            patientID = os.path.basename(subfolder)
            patientIDs_dapiseg.append(patientID)
            dapi_channels_dapiseg = dapi_files.get(subfolder)
            dapi_label_dapiseg = tkinter.Label(dapi_text_dapiseg, text=patientID)
            dapi_combobox_dapiseg = ttk.Combobox(dapi_text_dapiseg, values=dapi_channels_dapiseg,
                                                 textvariable=dapi_selected_dapiseg[i],
                                                 width=70)
            dapi_label_dapiseg.grid(row=0, column=0)
            dapi_combobox_dapiseg.grid(row=0, column=1)
            dapi_text_dapiseg.window_create('end', window=dapi_label_dapiseg)
            dapi_text_dapiseg.insert('end', '   ')
            dapi_text_dapiseg.window_create('end', window=dapi_combobox_dapiseg)
            dapi_text_dapiseg.insert('end', '\n\n')

        for widget in dapi_info_frame_dapiseg.winfo_children():
            widget.grid_configure(padx=10, pady=5)

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=6, column=0, sticky="", padx=20, pady=10)

        def Stop():
            # declare variable as nonlocal variable
            nonlocal data_together_bg
            nonlocal data_together_merge
            nonlocal data_together_dapiseg
            forcedsave = accept_var_merge.get()
            for i, patientID in enumerate(patientIDs_merge):
                data_merge = {}
                # Dapi info
                selected_dapi_value_merge = dapi_selected_merge[i].get()
                if selected_dapi_value_merge != no_selection:
                    data_merge['merge_patientID'] = patientID
                    data_merge['merge_selected_dapi_file'] = selected_dapi_value_merge
                # Channels info
                selected_channels_merge = []
                for j, marker in enumerate(markers):
                    if channel_selected_merge[j].get() == 'Selected':
                        selected_channels_merge.append(marker)
                if selected_channels_merge:
                    data_merge['merge_selected_channels'] = ';'.join([str(ele) for ele in selected_channels_merge])
                else:
                    data_merge['merge_selected_channels'] = ''
                data_merge['merge_forceSave'] = forcedsave
                data_together_merge.append(data_merge)
            # get the value of the entry box before destroying window
            for i, patientID in enumerate(patientIDs_dapiseg):
                data_dapiseg = {}
                # Dapi info
                selected_dapi_value = dapi_selected_dapiseg[i].get()
                if selected_dapi_value != no_selection:
                    data_dapiseg['dapiseq_patientID'] = patientID
                    data_dapiseg['dapiseg_selected_dapi_file'] = selected_dapi_value
                data_together_dapiseg.append(data_dapiseg)
            # Create Table
            fields = []
            if data_together_merge:
                fields = list(data_together_merge[0].keys())
            with open(self.tempfile, "w") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                w.writerows(data_together_merge)
            f.close()
            window_form.destroy()

        OKbutton = tkinter.Button(buttons_frame, text="OK", command=Stop)
        OKbutton.grid(row=0, column=0)
        Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window_form.destroy)
        Cbutton.grid(row=0, column=1)
        for widget in buttons_frame.winfo_children():
            widget.grid_configure(ipadx=15, padx=10, pady=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        window_form.mainloop()

    def processing(self):
        merge_dapiseg_input_dir = self.merge_dapiseg_input_dir
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        dapi_channels, subfolders = self.get_dapis_and_subfolders_from_csv_file(merge_dapiseg_input_dir)
        real_subfolders = [x[0].replace("\\", "/") for x in os.walk(merge_dapiseg_input_dir)]
        real_subfolders.pop(0)
        subfolders.sort()
        real_subfolders.sort()
        if subfolders == real_subfolders:
            print("The lists are identical")
        else:
            print("The lists are not identical")
        if not real_subfolders:
            logger.warning(merge_dapiseg_input_dir + " is empty. Doing nothing")
            return
        channels = []
        dapi_files_dict = {}
        for subfolder in real_subfolders:
            dapi_files = ht.dapi_tiff_image_filenames(subfolder, self.dapi_str, self.tiff_ext)
            dapi_files_dict[subfolder] = dapi_files
            # channels = channels + self.get_channels(subfolder, self.dapi_str)
            if not dapi_files:
                logger.warning("Image file of dapi channel isn't found. Please check the filename and change  it if "
                               "needed")
            if not channels:
                logger.warning("Channels could not be identified. Please check the filenames")
                return
        # channels = list(set(channels))
        channels = self.read_markers_from_csv_file(self.dapi_str)

        self.getting_input_parameters(dapi_files_dict, channels)
