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
                 working_dir, csv_ext, forceSave):
        self.bg_input_dir = bg_input_dir
        self.txt_dir = txt_dir
        self.infos_txt = infos_txt
        self.merge_dapiseg_input_dir = merge_dapiseg_input_dir
        self.tiff_ext = tiff_ext
        self.dapi_str = dapi_str
        self.tempfile_bg = os.path.join(working_dir, "temp_bg.csv")
        self.tempfile_dapiseg = os.path.join(working_dir, "temp_dapiseg.csv")
        self.tempfile_merge = os.path.join(working_dir, "temp_merge.csv")
        self.working_dir = working_dir
        self.csv_ext = csv_ext
        self.metadata_csv_file = metadata_csv_file
        self.force_save = int(forceSave[0])

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
        # logger.info(folder)
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
        # logger.info(ht.correct_path(folder, fnames[0]))
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

    def get_dapis_and_markers_from_csv_file(self):
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
                channel_list_markers = [key for key in channel_list]
                for ch in channel_list:
                    channels[ch] = dic[ch]
                for ch in channel_list_markers:
                    channels_markers[ch] = dic[ch]
                dapi_marker = [ch for ch in channels if self.dapi_str in (dic[ch].lower())][0]
                patientIDs.append(dic["expID"])
                dates_patients_channels_markers_together = dates_patients_channels_markers_together + [
                    dic["date"] + "_" + dic["expID"] + "_" + dic[
                        "marker for " + dapi_marker] + "_" + "backgroundSub" + self.tiff_ext,
                    dic["date"] + "_" + dic["expID"] + "_" + dic[
                        "marker for " + dapi_marker] + "_" + "noBackgroundSub" + self.tiff_ext]
                # dates_patients_channels_markers_dict[dic["expID"]] = [dic["date"] + "_" + dic["expID"] + "_" + dic[
                #    "marker for " + dapi_marker] + "_" + "backgroundSub" + self.tiff_ext,
                #                                                      dic["date"] + "_" + dic["expID"] + "_" + dic[
                #                                                          "marker for " + dapi_marker] + "_" + "noBackgroundSub" + self.tiff_ext]
                for ch in channels_markers:
                    if self.dapi_str not in dic["marker for " + ch]:
                        channels_markers_out = channels_markers_out + [dic["marker for " + ch] + "_" + "backgroundSub",
                                                                       dic[
                                                                           "marker for " + ch] + "_" + "noBackgroundSub"]
        patientIDs = dict.fromkeys(patientIDs)
        for patientID in patientIDs:
            dates_patients_channels_markers_help_list = []
            for date_patient_channel_marker in dates_patients_channels_markers_together:
                if "_" + patientID + "_" in date_patient_channel_marker:
                    dates_patients_channels_markers_help_list.append(date_patient_channel_marker)
            dates_patients_channels_markers_dict[patientID] = dates_patients_channels_markers_help_list
        channels_markers_out = list(set(channels_markers_out))

        return dates_patients_channels_markers_dict, channels_markers_out

    def getting_input_parameters(self, dapi_files, markers):
        window_form = tkinter.Tk()
        SVBar = tkinter.Scrollbar(window_form)
        SVBar.pack(side=tkinter.RIGHT, fill="y")
        SHBar = tkinter.Scrollbar(window_form, orient=tkinter.HORIZONTAL)
        SHBar.pack(side=tkinter.BOTTOM, fill="x")
        window_form.title("BG MERGE DAPISEG Form")
        frame = tkinter.Frame(window_form)
        frame.pack()
        data_together = []
        # Saving Marker BG Info
        data_together_bg = []
        marker_info_frame_bg = tkinter.LabelFrame(frame,
                                                  text="BACKGROUND SUBSTRACTION. Choose Radius values for each marker")
        marker_info_frame_bg.grid(row=0, column=0, padx=20, pady=5, sticky=N + S + E + W)
        marker_text_bg = ScrolledText(marker_info_frame_bg, width=100, height=10)
        marker_text_bg.grid(row=1, column=0)

        marker_filenames_bg = markers
        marker_selected_bg = []
        no_selection = "Not Selected"
        markers_bg = list(set([sstr.split("_")[0] for sstr in marker_filenames_bg])) + ["0" + self.dapi_str]
        # default_values = [tkinter.StringVar(value="50")] * len(markers_bg)
        for _ in markers_bg:
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
        ## Force Save Merge
        # force_save_frame_bg = tkinter.LabelFrame(frame, text="Force Save Option")
        # force_save_frame_bg.grid(row=1, column=0, sticky="news", padx=20, pady=5)

        # accept_var_bg = tkinter.StringVar(value=no_selection)
        # terms_check_bg = tkinter.Checkbutton(force_save_frame_bg, text="forceSave",
        #                                     variable=accept_var_bg, onvalue="Selected", offvalue=no_selection)
        # terms_check_bg.grid(row=1, column=0)
        # Saving Dapi Merge Info
        data_together_merge = []
        dapi_info_frame_merge = tkinter.LabelFrame(frame,
                                                   text="MERGE. Choose DAPI image for each patient you want to use for merge")
        dapi_info_frame_merge.grid(row=2, column=0, padx=20, pady=5, sticky=N + S + E + W)
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
        channels_frame_merge = tkinter.LabelFrame(frame,
                                                  text="MERGE. Choose channels of images you want to merge with DAPI")
        channels_frame_merge.grid(row=3, column=0, sticky="news", padx=20, pady=5)
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
        # force_save_frame_merge = tkinter.LabelFrame(frame, text="Force Save Option")
        # force_save_frame_merge.grid(row=4, column=0, sticky="news", padx=20, pady=5)

        # accept_var_merge = tkinter.StringVar(value=no_selection)
        # terms_check_merge = tkinter.Checkbutton(force_save_frame_merge, text="forceSave",
        #                                        variable=accept_var_merge, onvalue="Selected", offvalue=no_selection)
        # terms_check_merge.grid(row=1, column=0)

        # Saving Dapi Seg Info
        data_together_dapiseg = []
        dapi_info_frame_dapiseg = tkinter.LabelFrame(frame,
                                                     text="DAPISEG. Choose DAPI image for each patient you want to use for "
                                                          "dapi segmentation")
        dapi_info_frame_dapiseg.grid(row=5, column=0, padx=20, pady=5, sticky=N + S + E + W)
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
            nonlocal data_together
            # forcesave_bg = self.forceSave  # accept_var_bg.get()
            # forcesave_merge = self.forceSave  # accept_var_merge.get()
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
                    data_merge['merge_selected_channels'] = ';'.join([str(item) for item in selected_channels_merge])
                else:
                    data_merge['merge_selected_channels'] = ''
                # data_merge['merge_forceSave'] = forcesave_merge
                data_together_merge.append(data_merge)
            # get the value of the entry box before destroying window
            for i, patientID in enumerate(patientIDs_dapiseg):
                data_dapiseg = {}
                # Dapi info
                selected_dapi_value = dapi_selected_dapiseg[i].get()
                if selected_dapi_value != no_selection:
                    data_dapiseg['dapiseg_patientID'] = patientID
                    data_dapiseg['dapiseg_selected_dapi_file'] = selected_dapi_value
                data_together_dapiseg.append(data_dapiseg)
            for i, marker in enumerate(markers_bg):
                data_bg = {}
                # bg info
                selected_bg_value = marker_selected_bg[i].get()
                data_bg['bg_marker'] = marker
                data_bg['bg_selected_bg_value'] = selected_bg_value
                # data_bg['bg_forceSave'] = forcesave_bg
                data_together_bg.append(data_bg)
            # Create Table
            self.write_temp_csv(self.tempfile_dapiseg, data_together_dapiseg)
            self.write_temp_csv(self.tempfile_merge, data_together_merge)
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

    # def enter_data(self, patientIDs, dapi_selected, markers, channel_selected, accept_var, window_form):
    #     data_together = []
    #     forcedsave = accept_var.get()
    #     for i, patientID in enumerate(patientIDs):
    #         data = {}
    #         # Dapi info
    #         selected_dapi_value = dapi_selected[i].get()
    #         if selected_dapi_value != 'Not Selected':
    #             data['merge_patientID'] = patientID
    #             data['merge_selected_dapi_file'] = selected_dapi_value
    #         # Channels info
    #         selected_channels = []
    #         for j, marker in enumerate(markers):
    #             if channel_selected[j].get() == 'Selected':
    #                 selected_channels.append(marker)
    #         if selected_channels:
    #             data['merge_selected_channels'] = ';'.join([str(ele) for ele in selected_channels])
    #         else:
    #             data['merge_selected_channels'] = ''
    #         data['merge_forceSave'] = forcedsave
    #         data_together.append(data)
    #
    #     # print(data_together)
    #     # Create Table
    #     fields = []
    #     if data_together:
    #         fields = list(data_together[0].keys())
    #     with open(self.tempfile_bg, "w") as f:
    #         w = csv.DictWriter(f, fieldnames=fields)
    #         w.writeheader()
    #         w.writerows(data_together)
    #     f.close()
    #
    #     # else:
    #     #    tkinter.messagebox.showwarning(title="Error", message="You have not all selections")
    #     window_form.destroy()

    def write_temp_csv(self, temp, data):
        fields = []
        if data:
            fields = list(data[0].keys())
        with open(temp, "w+", newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        f.close()

    def delete_old_tempfile(self, temp):
        if os.path.exists(temp):
            os.remove(temp)

    def processing(self):
        # merge_dapiseg_input_dir = self.merge_dapiseg_input_dir
        self.delete_old_tempfile(self.tempfile_bg)
        self.delete_old_tempfile(self.tempfile_dapiseg)
        self.delete_old_tempfile(self.tempfile_merge)
        dapi_channels, markers = self.get_dapis_and_markers_from_csv_file()
        # real_subfolders = [x[0].replace("\\", "/") for x in os.walk(merge_dapiseg_input_dir)]
        # real_subfolders.pop(0)
        # subfolders.sort()
        # real_subfolders.sort()
        # if subfolders == real_subfolders:
        #    print("The lists are identical")
        # else:
        #    print("The lists are not identical")
        # if not real_subfolders:
        #    logger.warning(merge_dapiseg_input_dir + " is empty. Doing nothing")
        #    return
        # channels = []
        # dapi_files_dict = {}
        # for subfolder in real_subfolders:
        #    dapi_files = ht.dapi_tiff_image_filenames(subfolder, self.dapi_str, self.tiff_ext)
        #    dapi_files_dict[subfolder] = dapi_files
        # channels = channels + self.get_channels(subfolder, self.dapi_str)
        #    if not dapi_files:
        #        logger.warning("Image file of dapi channel isn't found. Please check the filename and change  it if "
        #                       "needed")
        # if not channels:
        #    logger.warning("Channels could not be identified. Please check the filenames")
        #    return
        # channels = list(set(channels))
        self.getting_input_parameters(dapi_channels, markers)
