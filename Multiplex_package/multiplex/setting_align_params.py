import csv
import logging
import os
import tkinter
from functools import partial
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import helpertools as ht

# multiplex.setting_align_params.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.SettingALIGNParams')


class SettingAlignParams:
    def __init__(self, input_dir, working_dir, metadata_csv_file, csv_ext, dapi_str, tiff_ext):
        self.input_dir = input_dir
        self.working_dir = working_dir
        self.tempfile = os.path.join(self.working_dir, "temp_align.csv")
        self.metadata = os.path.join(self.working_dir, metadata_csv_file)
        self.csv_ext = csv_ext
        self.metadata_csv_file = metadata_csv_file
        self.metadata_csv_file_path = ht.correct_path(working_dir, metadata_csv_file)
        self.dapi_str = dapi_str
        self.tiff_ext = tiff_ext
        # self.forceSave = forceSave

    def processing(self):
        dates_patients_dict = self.get_dapis_dates_from_csv()
        self.getting_input_parameters(dates_patients_dict)

    def get_dapis_dates_from_csv(self):
        try:
            # Get list of files in working_dir
            file_list = os.listdir(self.working_dir)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(ht.correct_path(self.working_dir, f)) and f.lower().endswith(
                self.csv_ext) and f.lower() == self.metadata_csv_file
        ]
        # logger.info(ht.correct_path(self.working_dir, fnames[0]))
        dates_patients_dict = {}
        patientIDs = []
        dates_patients_together = []
        if len(fnames) == 1:
            data = ht.read_data_from_csv(ht.correct_path(self.working_dir, self.metadata_csv_file))
            for dic in data:
                channels = {}
                # channels_markers = {}
                channel_list = [key for key in dic.keys() if
                                "channel" in key and "marker" not in key and dic[
                                    key] != ""]
                # channel_list_markers = [key for key in channel_list if exc_channel not in (dic[key]).lower()]
                for ch in channel_list:
                    channels[ch] = dic[ch]
                dapi_marker = [ch for ch in channels if self.dapi_str in (dic[ch].lower())][0]
                patientIDs.append(dic["expID"])
                dates_patients_together = dates_patients_together + [dic["date"] + "_" + dic["expID"] + "_" + dic[
                    "marker for " + dapi_marker] + self.tiff_ext]

        patientIDs = dict.fromkeys(patientIDs)
        for patientID in patientIDs:
            dates_patients_channels_markers_help_list = []
            for date_patient_channel_marker in dates_patients_together:
                if "_" + patientID + "_" in date_patient_channel_marker:
                    dates_patients_channels_markers_help_list.append(date_patient_channel_marker)
            dates_patients_dict[patientID] = dates_patients_channels_markers_help_list

        return dates_patients_dict

    def getting_input_parameters(self, dapi_files):
        window_form = tkinter.Tk()
        window_form.title("ALIGN Form")
        frame = tkinter.Frame(window_form)
        frame.pack()
        dapi_info_frame = tkinter.LabelFrame(frame,
                                             text="Choose DAPI image for each patient you want to use as Reference for alignment")
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
                values=dapi_files.get(dapi_filename)
                values.sort()
                dapi_selected.append(tkinter.StringVar(value=values[0]))
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
        # featureextractionmodeltype Parameter
        featureextractionmodeltype_frame = tkinter.LabelFrame(frame, text="FeatureExtractionModelType")
        featureextractionmodeltype_frame.grid(row=5, column=0, sticky="news", padx=20, pady=10)

        featureextractionmodeltype_label = Label(featureextractionmodeltype_frame,
                                                 text="Select the FeatureExtractionModelType : ")
        featureextractionmodeltype_label.grid(column=0, row=6, padx=10, pady=25)
        # Combobox creation
        a = tkinter.StringVar()
        featureextractionmodeltypechoosen = ttk.Combobox(featureextractionmodeltype_frame, width=27, textvariable=a)
        # Adding combobox drop down list
        featureextractionmodeltypechoosen['values'] = ("Translation", "Rigid", "Similarity", "Affine")

        featureextractionmodeltypechoosen.grid(column=1, row=6)
        featureextractionmodeltypechoosen.current(1)  # rigidBody is default here

        # RegistrationModelType Parameter
        registrationmodeltype_frame = tkinter.LabelFrame(frame, text="Registration Model Type")
        registrationmodeltype_frame.grid(row=7, column=0, sticky="news", padx=20, pady=10)

        registrationmodeltype_label = Label(registrationmodeltype_frame, text="Select the Registration Model Type : ")
        registrationmodeltype_label.grid(column=0, row=8, padx=10, pady=25)
        # Combobox creation
        b = tkinter.StringVar()
        registrationmodeltypechoosen = ttk.Combobox(registrationmodeltype_frame, width=27, textvariable=b)
        # Adding combobox drop down list
        registrationmodeltypechoosen['values'] = ("Translate --no deformation", "Rigid --translate + rotate",
                                                  "Similarity --translate + rotate + isotropic scale",
                                                  "Affine --free affine transform", "Elastic --bUnwarpJ splines",
                                                  "Moving least squares -- maximal warping")

        registrationmodeltypechoosen.grid(column=1, row=8)
        registrationmodeltypechoosen.current(1)  # Rigid --translate + rotate is default here

        # Background Parameter for Dapi Images
        backgroundparameters_info_frame = tkinter.LabelFrame(frame,
                                                             text="Background Parameters for DAPI channel images")
        backgroundparameters_info_frame.grid(row=9, column=0, sticky="news", padx=20, pady=10)
        dapi_text_bg = ScrolledText(backgroundparameters_info_frame, width=100, height=10)
        dapi_text_bg.grid(row=1, column=0)
        dapi_selected_bg = []
        dapi_bg = self.dapi_str
        dapi_selected_bg.append(tkinter.StringVar(value="50"))
        values_ = [str(i) for i in list(range(100 + 1))]
        dapi_label_bg = tkinter.Label(dapi_text_bg, text=dapi_bg)
        dapi_combobox_bg = ttk.Spinbox(dapi_text_bg, values=values_, textvariable=dapi_selected_bg[0])
        dapi_label_bg.grid(row=0, column=0)
        dapi_combobox_bg.grid(row=0, column=1)
        dapi_text_bg.window_create('end', window=dapi_label_bg)
        dapi_text_bg.insert('end', '   ')
        dapi_text_bg.window_create('end', window=dapi_combobox_bg)
        dapi_text_bg.insert('end', '\n')
        for widget in backgroundparameters_info_frame.winfo_children():
            widget.grid_configure(padx=10, pady=5)
        # AutoContrast
        auto_contrast_frame = tkinter.LabelFrame(frame, text="Auto Contrast Option")
        auto_contrast_frame.grid(row=11, column=0, sticky="news", padx=20, pady=10)

        accept_var = tkinter.StringVar(value="Not Selected")
        terms_check = tkinter.Checkbutton(auto_contrast_frame, text="autoContrast",
                                          variable=accept_var, onvalue="Selected", offvalue="Not Selected")
        terms_check.grid(row=0, column=0)

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=13, column=0, sticky="", padx=20, pady=10)
        OKbutton = tkinter.Button(buttons_frame, text="OK",
                                  command=partial(self.enter_data, patientIDs, dapi_selected,
                                                  featureextractionmodeltypechoosen,
                                                  registrationmodeltypechoosen, dapi_selected_bg,
                                                  window_form, accept_var)
                                  )
        # accept_var, window_form)
        OKbutton.grid(row=0, column=0)
        Cbutton = tkinter.Button(buttons_frame, text="Cancel", command=partial(self.cancel, window_form))
        Cbutton.grid(row=0, column=1)
        for widget in buttons_frame.winfo_children():
            widget.grid_configure(ipadx=15, padx=10, pady=5)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        window_form.mainloop()

    def cancel(self, window_form):
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        window_form.destroy()

    def enter_data(self, patientIDs, dapi_selected, featureextractionmodeltypechoosen, registrationmodeltypechoosen,
                   dapi_selected_bg, window_form, accept_var):
        data_together = []
        # forcedsave = self.forceSave  # accept_var.get()
        autoContrast = accept_var.get()
        for i, patientID in enumerate(patientIDs):
            data = {}
            # Shading File Selected Info
            data['patientID'] = patientID
            data['selected_dapi_file'] = dapi_selected[i].get()
            data['selected_featureextractionmodeltype'] = featureextractionmodeltypechoosen.get()
            data['selected_registrationmodeltype'] = registrationmodeltypechoosen.get()
            data['dapi_selected_bg'] = dapi_selected_bg[0].get()
            data['selected_autoContrast'] = autoContrast
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
