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
logger = logging.getLogger('multiplex.SettingDapisegParams')


class SettingDapisegParams:
    def __init__(self, input_dir, tiff_ext, dapi_str, metadata_csv_file, working_dir, csv_ext):
        self.input_dir = input_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str
        self.working_dir = working_dir
        self.tempfile = os.path.join(self.working_dir, "temp_dapiseg.csv")
        self.metadata_csv_file = metadata_csv_file
        self.metadata_csv_file_path = ht.correct_path(working_dir, metadata_csv_file)
        self.csv_ext = csv_ext

    def get_dapis_and_markers_from_csv_file(self, exc_channel):
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
        dates_patients_channels_markers_dict = {}
        channels_markers_out = []
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
                dates_patients_channels_markers_dict[dic["expID"]] = [dic["date"] + "_" + dic["expID"] + "_" + dic[
                    "marker for " + dapi_marker] + "_" + "backgroundSub" + "." + self.tiff_ext,
                                                                      dic["date"] + "_" + dic["expID"] + "_" + dic[
                                                                          "marker for " + dapi_marker] + "_" + "noBackgroundSub" + self.tiff_ext]
                for ch in channels_markers:
                    channels_markers_out = channels_markers_out + [dic["marker for " + ch] + "_" + "backgroundSub",
                                                                   dic["marker for " + ch] + "_" + "noBackgroundSub"]
        channels_markers_out = list(set(channels_markers_out))

        return dates_patients_channels_markers_dict, channels_markers_out

    def processing(self):
        input_dir = self.input_dir
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        dapi_files_dict, _ = self.get_dapis_and_markers_from_csv_file(self.dapi_str)
        subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
        subfolders.pop(0)
        if not subfolders:
            logger.warning(input_dir + " is empty. Doing nothing")
            return
        self.getting_input_parameters(dapi_files_dict)

    def getting_input_parameters(self, dapi_files):
        window_form = tkinter.Tk()
        window_form.title("Dapiseg Form")
        frame = tkinter.Frame(window_form)
        frame.pack()
        # Saving Dapi Info
        dapi_info_frame = tkinter.LabelFrame(frame,
                                             text="Choose DAPI image for each patient you want to use for dapiseg")
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

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=4, column=0, sticky="", padx=20, pady=10)
        OKbutton = tkinter.Button(buttons_frame, text="OK",
                                  command=partial(self.enter_data, patientIDs, dapi_selected, window_form)
                                  )
        OKbutton.grid(row=0, column=0)
        Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=window_form.destroy)
        Cbutton.grid(row=0, column=1)
        for widget in buttons_frame.winfo_children():
            widget.grid_configure(ipadx=15, padx=10, pady=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        window_form.mainloop()

    def enter_data(self, patientIDs, dapi_selected, window_form):
        data_together = []
        for i, patientID in enumerate(patientIDs):
            data = {}
            # Dapi info
            selected_dapi_value = dapi_selected[i].get()
            if selected_dapi_value != 'Not Selected':
                data['dapiseg_patientID'] = patientID
                data['dapiseg_selected_dapi_file'] = selected_dapi_value
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
