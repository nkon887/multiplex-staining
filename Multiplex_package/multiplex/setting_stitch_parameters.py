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

# im-jy-package.merging_channels.py creates its own logger, as a sub logger to 'multiplex.macro.im-jy-package.main'
logger = logging.getLogger('multiplex.SettingStitchParams')


class SettingStitchParams:
    def __init__(self, input_dir, working_dir):
        self.input_dir = input_dir
        self.working_dir = working_dir
        if not os.path.exists(working_dir):
            os.mkdir(working_dir)
        self.tempfile = os.path.join(self.working_dir, "temp_stitch.csv")
        self.no_shading_file = "No_shading_file"
        self.shading_word = "shading"
        self.czi_ext = ".czi"
        # self.forceSave = forceSave

    def processing(self):
        self.getting_input_parameters()

    def getting_input_parameters(self):
        window_form = tkinter.Tk()
        window_form.title("STITCH Form")
        frame = tkinter.Frame(window_form)
        frame.pack()
        dates = []
        czifiles = [self.no_shading_file]
        dir = os.walk(self.input_dir)
        selected_files = []
        not_selected_files = []
        if dir:
            for path, subdirs, files in dir:
                for filename in files:
                    file_path = ht.correct_path(path, filename)
                    if re.match(r'^\d{6}_[^_]+$', os.path.splitext(filename)[0]) and filename.endswith(
                            self.czi_ext) or self.shading_word in os.path.splitext(filename)[0].lower() and \
                            os.path.splitext(filename)[0] != self.no_shading_file and re.match(r'^\d{6}.*$', os.path.splitext(filename)[0]):
                        selected_files.append(file_path)
                    else:
                        not_selected_files.append(file_path)
        # create a list box
        selected = tuple(selected_files)
        selected_var = Variable(value=selected)
        selected_info_frame = tkinter.LabelFrame(frame, text="Selected czi files:")
        selected_info_frame.grid(row=0, column=0, padx=20, pady=10, sticky=N + S + E + W)
        selected_listbox = Listbox(selected_info_frame, listvariable=selected_var, width=50, height=6,
                                   selectmode=EXTENDED)
        selected_listbox.pack(expand=True, fill=BOTH, side=LEFT)

        # link a scrollbar to a list
        selected_scrollbar = ttk.Scrollbar(
            selected_info_frame,
            orient=VERTICAL,
            command=selected_listbox.yview
        )
        selected_listbox['yscrollcommand'] = selected_scrollbar.set

        selected_scrollbar.pack(side=LEFT, expand=False, fill=Y)

        not_selected = tuple(not_selected_files)
        not_selected_var = Variable(value=not_selected)
        not_selected_info_frame = tkinter.LabelFrame(frame, text="Not selected czi files:")
        not_selected_info_frame.grid(row=1, column=0, padx=20, pady=10, sticky=N + S + E + W)
        not_selected_listbox = Listbox(not_selected_info_frame, listvariable=not_selected_var, width=50, height=6,
                                       selectmode=EXTENDED)
        not_selected_listbox.pack(expand=True, fill=BOTH, side=LEFT)

        # link a scrollbar to a list
        not_selected_scrollbar = ttk.Scrollbar(
            not_selected_info_frame,
            orient=VERTICAL,
            command=not_selected_listbox.yview
        )
        not_selected_listbox['yscrollcommand'] = not_selected_scrollbar.set

        not_selected_scrollbar.pack(side=LEFT, expand=False, fill=Y)

        for file_path in selected_files:
            czifiles.append(os.path.basename(file_path))
        for czifile in czifiles:
            date = czifile[0:6]
            if re.match(r'^\d{6}$', date):
                dates.append(date)
        dates = list(set(dates))
        czifiles_filtered_by_date = {}
        shading_selected = []
        if dates:
            for date, i in zip(dates, range(0, len(dates))):
                date_filtered_czifiles = [x for x in czifiles if date in x]
                date_filtered_czifiles.insert(0, self.no_shading_file)
                shading_consisting_date_filtered_czifiles = [x for x in date_filtered_czifiles if
                                                             self.shading_word in x.lower() and x != self.no_shading_file]
                if shading_consisting_date_filtered_czifiles:
                    shading_selected.append(tkinter.StringVar(value=shading_consisting_date_filtered_czifiles[0]))
                else:
                    shading_selected.append(tkinter.StringVar(value=date_filtered_czifiles[0]))
                czifiles_filtered_by_date[date] = date_filtered_czifiles
        # Saving Shading Info
        shading_info_frame = tkinter.LabelFrame(frame,
                                                text="Choose shading czi for each date you want to use for stitch")
        shading_info_frame.grid(row=2, column=0, padx=20, pady=10, sticky=N + S + E + W)
        shading_text = ScrolledText(shading_info_frame, width=70, height=10)
        shading_text.grid(row=3, column=0)
        for i, date in enumerate(dates):
            shading_channels = czifiles_filtered_by_date.get(date)
            shading_label = tkinter.Label(shading_text, text=date)
            shading_combobox = ttk.Combobox(shading_text, values=shading_channels, textvariable=shading_selected[i],
                                            width=50)
            shading_label.grid(row=0, column=0)
            shading_combobox.grid(row=0, column=1)
            shading_text.window_create('end', window=shading_label)
            shading_text.insert('end', '   ')
            shading_text.window_create('end', window=shading_combobox)
            shading_text.insert('end', '\n\n')

        # for widget in shading_info_frame.winfo_children():
        #    widget.grid_configure(padx=10, pady=5)
        # Resolution Parameter
        resolution_frame = tkinter.LabelFrame(frame, text="Resolution")
        resolution_frame.grid(row=5, column=0, sticky="news", padx=20, pady=10)

        resolution_label = Label(resolution_frame, text="Select the Resolution : ")
        resolution_label.grid(column=0, row=5, padx=10, pady=25)
        # Combobox creation
        n = tkinter.StringVar()
        resolutionchoosen = ttk.Combobox(resolution_frame, width=27, textvariable=n)
        # Adding combobox drop down list
        resolutionchoosen['values'] = ("8-bit", "16-bit", "32-bit", "original")

        resolutionchoosen.grid(column=1, row=5)
        resolutionchoosen.current(0)

        # Buttons
        buttons_frame = tkinter.Frame(frame)
        buttons_frame.grid(row=7, column=0, sticky="", padx=20, pady=10)
        OKbutton = tkinter.Button(buttons_frame, text="OK",
                                  command=partial(self.enter_data, dates, shading_selected, resolutionchoosen,
                                                  selected_files,
                                                  window_form)
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

    def enter_data(self, dates, shading_selected, resolution_selected, selected_files, window_form):
        data_together = []
        # forcedsave = self.forceSave  # accept_var.get()
        for i, date in enumerate(dates):
            data = {}
            # Shading File Selected Info
            data['date'] = date
            data['selected_shading_file'] = shading_selected[i].get()
            data['resolution'] = resolution_selected.get()
            data['selected_files'] = ";".join(selected_files)
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
