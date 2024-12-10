import csv
import logging
import os
import tkinter
from functools import partial
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import helpertools as ht

# im-jy-package.merging_channels.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.SettingMergeParams')


class SettingMergeParams:
    def __init__(self, input_dir, tiff_ext, dapi_str, metadata_csv_file, working_dir, csv_ext):
        self.input_dir = input_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str
        self.working_dir = working_dir
        self.tempfile = os.path.join(self.working_dir, "temp_merge.csv")
        self.metadata_csv_file = metadata_csv_file
        self.metadata_csv_file_path = ht.correct_path(working_dir, metadata_csv_file)
        self.csv_ext = csv_ext

    def get_channels(self, subfolder, exc_channel):
        channels = []
        for subfolder_file in os.listdir(subfolder):
            filename = os.path.basename(subfolder_file)
            if filename.endswith(self.tiff_ext) and not (exc_channel in filename):
                channel = '_'.join(filename.split('.')[0].split('_')[2:])
                channels.append(channel)
        return sorted(list(set(channels)))

    def get_dapis_and_markers_from_csv_file(self, exc_channel):
        folder = self.working_dir
        # logger.info(folder)
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
        # logger.info(ht.correct_path(folder, fnames[0]))
        dates_patients_channels_markers_dict = {}
        channels_markers_out = []
        patientIDs = []
        dates_patients_channels_markers_together = []
        if len(fnames) == 1:
            data = ht.read_data_from_csv(ht.correct_path(folder, self.metadata_csv_file))
            for dic in data:
                channels = {}
                channels_markers = {}
                channel_list = [key for key in dic.keys() if
                                "channel" in key and "marker" not in key and dic[
                                    key] != ""]
                channel_list_markers = [key for key in channel_list if exc_channel not in (dic[key]).lower()]
                for ch in channel_list:
                    channels[ch] = dic[ch]
                for ch in channel_list_markers:
                    channels_markers[ch] = dic[ch]
                dapi_marker = [ch for ch in channels if self.dapi_str in (dic[ch].lower())][0]
                patientIDs.append(dic["expID"])
                dates_patients_channels_markers_together = dates_patients_channels_markers_together + [dic["date"] + "_" + dic["expID"] + "_" + dic[
                    "marker for " + dapi_marker] + "_" + "backgroundSub" + self.tiff_ext,
                                                                      dic["date"] + "_" + dic["expID"] + "_" + dic[
                                                                          "marker for " + dapi_marker] + "_" + "noBackgroundSub" + self.tiff_ext]
                # dates_patients_channels_markers_dict[dic["expID"]] = [dic["date"] + "_" + dic["expID"] + "_" + dic[
                #    "marker for " + dapi_marker] + "_" + "backgroundSub" + self.tiff_ext,
                #                                                      dic["date"] + "_" + dic["expID"] + "_" + dic[
                #                                                          "marker for " + dapi_marker] + "_" + "noBackgroundSub" + self.tiff_ext]
                for ch in channels_markers:
                    channels_markers_out = channels_markers_out + [dic["marker for " + ch] + "_" + "backgroundSub",
                                                                   dic["marker for " + ch] + "_" + "noBackgroundSub"]
        patientIDs = dict.fromkeys(patientIDs)
        for patientID in patientIDs:
            dates_patients_channels_markers_help_list = []
            for date_patient_channel_marker in dates_patients_channels_markers_together:
                if patientID in date_patient_channel_marker:
                    dates_patients_channels_markers_help_list.append(date_patient_channel_marker)
            dates_patients_channels_markers_dict[patientID] = dates_patients_channels_markers_help_list

        channels_markers_out = list(set(channels_markers_out))

        return dates_patients_channels_markers_dict, channels_markers_out

    def processing(self):
        # input_dir = self.input_dir
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        dapi_files_dict, channels = self.get_dapis_and_markers_from_csv_file(self.dapi_str)
        # subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
        # subfolders.pop(0)
        # if not subfolders:
        #    logger.warning(input_dir + " is empty. Doing nothing")
        #    return
        # channels = []
        # dapi_files_dict = {}
        # for subfolder in subfolders:
        # dapi_files = ht.dapi_tiff_image_filenames(subfolder, self.dapi_str, self.tiff_ext)
        # dapi_files_dict[subfolder] = dapi_files
        #    channels = channels + self.get_channels(subfolder, self.dapi_str)
        #   channels = channels + self.read_markers_from_csv_file(self.dapi_str)
        # if not dapi_files:
        #    logger.warning("Image file of dapi channel isn't found. Please check the filename and change  it if "
        #                   "needed")
        #    if not channels:
        #        logger.warning("Channels could not be identified. Please check the filenames")
        #        return
        # channels = self.read_markers_from_csv_file(self.dapi_str)
        # logger.info(channels)
        # channels = list(set(channels))
        self.getting_input_parameters(dapi_files_dict, channels)

    def getting_input_parameters(self, dapi_files, markers):
        window_form = tkinter.Tk()
        window_form.title("Merge Channels Form")
        frame = tkinter.Frame(window_form)
        frame.pack()
        # Saving Dapi Info
        dapi_info_frame = tkinter.LabelFrame(frame, text="Choose DAPI image for each patient you want to use for merge")
        dapi_info_frame.grid(row=0, column=0, padx=20, pady=10, sticky=N + S + E + W)
        dapi_text = ScrolledText(dapi_info_frame, width=100, height=10)
        dapi_text.grid(row=1, column=0)
        dapi_filenames = dapi_files.keys()
        dapi_selected = []
        patientIDs = []
        for dapi_filename in dapi_filenames:
            if not dapi_files[dapi_filename]:
                dapi_selected.append(tkinter.StringVar(value="Not Selected"))
            else:
                dapi_selected.append(tkinter.StringVar(value=dapi_files.get(dapi_filename)[0]))
        for i, subfolder in enumerate(dapi_filenames):
            patientID = os.path.basename(subfolder)
            patientIDs.append(patientID)
            dapi_channels = dapi_files.get(subfolder)
            dapi_label = tkinter.Label(dapi_text, text=patientID)
            dapi_combobox = ttk.Combobox(dapi_text, values=dapi_channels, textvariable=dapi_selected[i], width=70)
            dapi_label.grid(row=0, column=0)
            dapi_combobox.grid(row=0, column=1)
            dapi_text.window_create('end', window=dapi_label)
            dapi_text.insert('end', '   ')
            dapi_text.window_create('end', window=dapi_combobox)
            dapi_text.insert('end', '\n\n')

        for widget in dapi_info_frame.winfo_children():
            widget.grid_configure(padx=10, pady=5)
        # Saving Channels Info
        channels_frame = tkinter.LabelFrame(frame, text="Choose channels of images you want to merge with DAPI")
        channels_frame.grid(row=1, column=0, sticky="news", padx=20, pady=10)
        text = ScrolledText(channels_frame, width=100, height=10)
        text.grid(row=2, column=0)
        channel_selected = []
        for i in range(len(markers)):
            channel_selected.append(tkinter.StringVar(value="Not Selected"))
        for i in range(len(markers)):
            cb = tkinter.Checkbutton(text, text=markers[i], bg='white', anchor='w', variable=channel_selected[i],
                                     onvalue="Selected",
                                     offvalue="Not Selected")
            text.window_create('end', window=cb)
            text.insert('end', '\n')
        for widget in channels_frame.winfo_children():
            widget.grid_configure(padx=10, pady=5)
        # Force Save
        force_save_frame = tkinter.LabelFrame(frame, text="Force Save Option")
        force_save_frame.grid(row=3, column=0, sticky="news", padx=20, pady=10)

        accept_var = tkinter.StringVar(value="Not Selected")
        terms_check = tkinter.Checkbutton(force_save_frame, text="forceSave",
                                          variable=accept_var, onvalue="Selected", offvalue="Not Selected")
        terms_check.grid(row=0, column=0)

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=4, column=0, sticky="", padx=20, pady=10)
        OKbutton = tkinter.Button(buttons_frame, text="OK",
                                  command=partial(self.enter_data, patientIDs, dapi_selected, markers, channel_selected,
                                                  accept_var, window_form)
                                  )
        OKbutton.grid(row=0, column=0)
        Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window_form.destroy)
        Cbutton.grid(row=0, column=1)
        for widget in buttons_frame.winfo_children():
            widget.grid_configure(ipadx=15, padx=10, pady=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        window_form.mainloop()

    def enter_data(self, patientIDs, dapi_selected, markers, channel_selected, accept_var, window_form):
        data_together = []
        forcedsave = accept_var.get()
        for i, patientID in enumerate(patientIDs):
            data = {}
            # Dapi info
            selected_dapi_value = dapi_selected[i].get()
            if selected_dapi_value != 'Not Selected':
                data['merge_patientID'] = patientID
                data['merge_selected_dapi_file'] = selected_dapi_value
            # Channels info
            selected_channels = []
            for j, marker in enumerate(markers):
                if channel_selected[j].get() == 'Selected':
                    selected_channels.append(marker)
            if selected_channels:
                data['merge_selected_channels'] = ';'.join([str(ele) for ele in selected_channels])
            else:
                data['merge_selected_channels'] = ''
            data['merge_forceSave'] = forcedsave
            data_together.append(data)
        # Create Table
        fields = []
        if data_together:
            fields = list(data_together[0].keys())
        with open(self.tempfile, "w+", newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data_together)
        f.close()

        # else:
        #    tkinter.messagebox.showwarning(title="Error", message="You have not all selections")
        window_form.destroy()
