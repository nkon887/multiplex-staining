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
logger = logging.getLogger('multiplex.SettingBGParams')


class SettingBGParams:
    def __init__(self, input_dir, tiff_ext, dapi_str, metadata_csv_file, working_dir, csv_ext):
        self.input_dir = input_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str
        self.working_dir = working_dir
        self.tempfile_bg = os.path.join(self.working_dir, "temp_bg.csv")
        self.metadata_csv_file = metadata_csv_file
        self.metadata_csv_file_path = ht.correct_path(working_dir, metadata_csv_file)
        self.csv_ext = csv_ext

    def get_dapis_and_markers_from_csv_file(self):
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
                channel_list_markers = [key for key in channel_list]
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
        # input_dir = self.input_dir
        if os.path.exists(self.tempfile_bg):
            os.remove(self.tempfile_bg)
        _, markers = self.get_dapis_and_markers_from_csv_file()
        # subfolders = [x[0].replace("\\", "/") for x in os.walk(input_dir)]
        # subfolders.pop(0)
        # if not subfolders:
        #    logger.warning(input_dir + " is empty. Doing nothing")
        #    return
        self.getting_input_parameters(markers)

    def getting_input_parameters(self, markers):
        window_form = tkinter.Tk()
        window_form.title("BG Form")
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
        markers_bg = list(set([sstr.split("_")[0] for sstr in marker_filenames_bg]))
        for _ in markers_bg:
            if not markers_bg:
                marker_selected_bg.append(tkinter.StringVar(value="0"))
            else:
                marker_selected_bg.append(tkinter.StringVar(value="50"))
        values_ = [str(i) for i in list(range(100 + 1))]
        for i, marker in enumerate(markers_bg):
            marker_label_bg = tkinter.Label(marker_text_bg, text=marker)
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
        # Force Save Merge
        no_selection = "Not Selected"
        force_save_frame_bg = tkinter.LabelFrame(frame, text="Force Save Option BG")
        force_save_frame_bg.grid(row=4, column=0, sticky="news", padx=20, pady=10)

        accept_var_bg = tkinter.StringVar(value=no_selection)
        terms_check_bg = tkinter.Checkbutton(force_save_frame_bg, text="forceSave",
                                                variable=accept_var_bg, onvalue="Selected", offvalue=no_selection)
        terms_check_bg.grid(row=1, column=0)
        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=6, column=0, sticky="", padx=20, pady=10)

        def Stop():
            # declare variable as nonlocal variable
            nonlocal data_together_bg
            forcedsave = accept_var_bg.get()
            for i, marker in enumerate(markers_bg):
                data_bg = {}
                # bg info
                selected_bg_value = marker_selected_bg[i].get()
                data_bg['bg_marker'] = marker
                data_bg['bg_selected_bg_value'] = selected_bg_value
                data_bg['bg_forceSave'] = forcedsave
                data_together_bg.append(data_bg)
            # Create Table
            self.write_temp_csv(self.tempfile_bg, data_together_bg)
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

    def write_temp_csv(self, temp, data):
        fields = []
        if data:
            fields = list(data[0].keys())
        with open(temp, "w+", newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        f.close()
