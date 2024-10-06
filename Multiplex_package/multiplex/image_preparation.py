# multiplex.image_preparation.py
import csv
import os
import re
import sys
from pathlib import Path

import PySimpleGUI as sG
from PIL import Image, UnidentifiedImageError
import multiplex.setup_logger
import logging
import multiplex.helpertools as ht
from collections import defaultdict

# multiplex.image_preparation.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.main.imagecheck')


class ImagePreparation:
    def __init__(self, working_dir, input_dir, info_txt_file, metadata_csv_file, input_dates, channel_list,
                 standard_search_terms,
                 standard_replacements, tiff_ext, dates_number, dapi_str, csv_ext):
        self.working_dir = working_dir
        self.input_dir = input_dir
        self.info_txt_file = info_txt_file
        self.metadata_csv_file = metadata_csv_file
        self.input_dates = input_dates
        self.channel_list = channel_list
        self.standard_search_terms = standard_search_terms
        self.standard_replacements = standard_replacements
        self.tiff_ext = tiff_ext
        self.dates_number = dates_number
        self.dapi_str = dapi_str
        self.csv_ext = csv_ext
        self.metadata_csv_file_path = ht.correct_path(working_dir, metadata_csv_file)

    #    def read_and_fill_channel_for_table_update_from_txt_file(self):
    #        folder = self.input_dir
    #       try:
    #           # Get list of files in folder
    #           file_list = os.listdir(folder)
    #       except:
    #           file_list = []
    #       fnames = [
    #           f
    #           for f in file_list
    #           if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(self.info_txt_file)
    #       ]
    #
    #       input_dates_channels_markers = {}
    #       if len(fnames) == 1:
    #           with open(ht.correct_path(folder, fnames[0])) as f:
    #               # read all lines in a list
    #               lines = f.readlines()
    #               for i, line in enumerate(lines):
    #                   # check if string present on a current line
    #                   if re.match(r'^\d{6}$', line):
    #                       channel_marker = {}
    #                       for j in range(i + 1, len(lines), 1):
    #                           if re.match(r'^\d{6}$', lines[j]):
    #                               break
    #                           for channel in self.channel_list:
    #                               if lines[j].find(channel) != -1:  # if re.match(r'^c\d.*\w*$', lines[j]):
    #                                   channel_marker_str = lines[j].strip()
    #                                   channel_marker_list = channel_marker_str.split(" ")
    #                                   check_length = len(channel_marker_list)
    #                                   if check_length == 2:
    #                                       channel_marker[channel_marker_list[0]] = channel_marker_list[1]
    #                                   elif check_length == 1:
    #                                       channel_marker[channel_marker_list[0]] = ""
    #                                       if channel_marker_list[0] == self.dapi_str.upper():
    #                                           channel_marker[channel_marker_list[0]] = f"0{self.dapi_str}"
    #                                   else:
    #                                       logger.warning("No channels. Something went wrong with the images")
    #                       date = line.strip()
    #                       input_dates_channels_markers[date] = channel_marker
    #       return input_dates_channels_markers

    def get_dict_from_csv_file(self):
        folder = self.working_dir
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
        data = {}
        if len(fnames) == 1:
            with open(self.metadata_csv_file_path) as f:
                headers = next(f).rstrip().split(',')
                data = [dict(zip(headers, line.rstrip().split(','))) for line in f]
        return data

    def read_data_and_fill_channel_for_table_update_from_csv_file(self):
        data = self.get_dict_from_csv_file()
        input_dates_channels_markers = defaultdict(dict)
        channel_list = []
        for dic in data:
            channel_list_dic = []
            for key in dic.keys():
                if "channel" in key and "marker" not in key and dic[key] != "":
                    channel_list_dic.append(key)
            channel_list = channel_list + channel_list_dic
        channel_list = list(dict.fromkeys(channel_list))
        for dic in data:
            for ch in channel_list:
                input_dates_channels_markers[dic["date"]][dic[ch]] = dic["marker for " + ch]

        return input_dates_channels_markers

    def prepareDefaultValues(self):
        # date_channels_markers = self.read_and_fill_channel_for_table_update_from_txt_file()
        date_channels_markers = self.read_data_and_fill_channel_for_table_update_from_csv_file()
        if date_channels_markers:
            dfdata = {}
            for i, date in enumerate(date_channels_markers):
                value_length = len(date_channels_markers[date])
                dfdata.setdefault((i, 0), []).append(i)
                if re.match(r'^\d{6}$', date):
                    dfdata.setdefault((i, 1), []).append(date)
                if value_length:
                    for j, channel in enumerate(date_channels_markers[date]):
                        if channel in self.channel_list and date_channels_markers[date][channel] != '':
                            dfdata.setdefault((i, self.channel_list.index(channel) + 2), []).append(
                                date_channels_markers[date][channel])
                        elif channel in self.channel_list and date_channels_markers[date][channel] == '':
                            dfdata.setdefault((i, self.channel_list.index(channel) + 2), []).append('')

            return dfdata

    def text_over_input(self, text, input_size, dates_length, col):
        return sG.Column(
            [[sG.Input(col[counter], key=text + str(counter), size=(input_size, 1), pad=(0, 3))] for
             counter in range(dates_length)], pad=(5, 5), scrollable=True,
            vertical_scroll_only=True)

    def rename_files_recursively(self, root_path, txt_inputs, inputs, progress_bar, MAX_ROWS):
        # change directory
        os.chdir(root_path)

        count = 0
        cwd = Path.cwd()
        new_date_patient_ids = []
        for subdir in os.listdir(cwd):
            if not os.path.isfile(subdir):
                new_subdir_name = str(subdir)
                for counter, term in enumerate(self.standard_search_terms):
                    if term in new_subdir_name:
                        new_subdir_name = new_subdir_name.replace(term, self.standard_replacements[counter])
                if new_subdir_name[7:].count("_") > 1:
                    new_subdir_name = new_subdir_name[0:7] + new_subdir_name[7:].replace("_", "-")
                if new_subdir_name[6] != "_":
                    new_subdir_name = new_subdir_name[:6] + "_" + new_subdir_name[6:]
                new_date_patient_ids.append(new_subdir_name)
                # pattern = r'-Stitching[^c]*|(?<=c\d)(.*)'
                # if re.match(r'.*' + pattern, new_subdir_name):
                #    new_subdir_name = re.sub(pattern, '', new_subdir_name)
                if not os.path.exists(new_subdir_name):
                    os.rename(ht.correct_path(cwd, subdir), ht.correct_path(cwd, new_subdir_name))
        for dir_path, subdirs, file_names in os.walk(cwd):
            for filename in file_names:
                if filename.endswith(self.tiff_ext):
                    name, extension = os.path.splitext(filename)
                    new_name = name
                    # pattern = r'-Stitching[^c]*|(?<=c\d)(.*)'
                    # if re.match(r'.*' + pattern, new_name):
                    #    new_name = re.sub(pattern, ' ', new_name).replace(" ", "")
                    search_terms = self.standard_search_terms
                    found_new_name = ""
                    for counter, term in enumerate(search_terms):
                        if term in name:
                            new_name = new_name.replace(term, self.standard_replacements[counter])
                    for i in range(MAX_ROWS):
                        date = inputs[(i, 1)].replace(" ", "")
                        if date in new_name and date in txt_inputs:
                            for new_date_patient_id in new_date_patient_ids:
                                if date in new_date_patient_id:
                                    new_date_patient_id_ = new_date_patient_id.replace("_", "").replace("-", "")
                                    new_name_ = new_name.replace("_", "").replace("-", "")
                                    if new_date_patient_id_ in new_name_:
                                        found_new_name = new_date_patient_id
                            for def_ch in txt_inputs[date]:
                                j = 2 + self.channel_list.index(def_ch)
                                cur_ch = inputs[(i, j)].replace(" ", "")
                                if cur_ch != "":
                                    if def_ch in new_name and cur_ch != def_ch:
                                        new_name = new_name.replace(def_ch, cur_ch)
                                        found_new_name = found_new_name + "_" + cur_ch
                                    elif txt_inputs[date][def_ch] in new_name and cur_ch != txt_inputs[date][def_ch] \
                                            and txt_inputs[date][def_ch] != "":
                                        new_name = new_name.replace(txt_inputs[date][def_ch], cur_ch)
                                        found_new_name = found_new_name + "_" + cur_ch
                                else:
                                    end_index = new_name.rfind('_')
                                    found_new_name = found_new_name + "_" + new_name[end_index + 1:]
                    new_file_path = ht.correct_path(dir_path, found_new_name + extension)
                    if name != new_name and not os.path.exists(new_file_path):
                        os.rename(ht.correct_path(dir_path, filename),
                                  new_file_path)
                        count += 1
        logger.info(f"{count} files were renamed recursively from root {cwd}")

        sys.stdout.flush()
        for i in range(MAX_ROWS):
            date = inputs[(i, 1)].replace(" ", "")
            if date in txt_inputs:
                for def_ch in txt_inputs[date]:
                    j = 2 + self.channel_list.index(def_ch)
                    cur_ch = inputs[(i, j)].replace(" ", "")
                    txt_inputs[date][def_ch] = cur_ch
        self.evaluation(root_path, inputs, txt_inputs, progress_bar)
        # self.rewrite_infos_txt_file(txt_inputs)
        self.rewrite_metadata_csv_file(txt_inputs)

    def rewrite_infos_txt_file(self, txt_inputs):
        write_file = open(self.info_txt_file, "w")
        for date in txt_inputs:
            write_file.write(date + "\n")
            for chn in txt_inputs[date]:
                write_file.write(chn + " " + txt_inputs[date][chn] + "\n")
        write_file.close()

    def rewrite_metadata_csv_file(self, txt_inputs):
        old_data = self.get_dict_from_csv_file()
        new_data = []
        for dic in old_data:
            for k, v in dic.items():
                for date in txt_inputs:
                    if dic["date"] == date:
                        for chn in txt_inputs[date]:
                            if chn == v and "marker for" not in k and "DefaultChannel" not in k:
                                # logger.info(k)
                                # logger.info(txt_inputs[date][chn])
                                dic["marker for " + k] = txt_inputs[date][chn]
            new_data.append(dic)
        # Create Table
        self.delete_old_tempfile(self.metadata_csv_file_path)
        fields = []
        if new_data:
            fields = list(new_data[0].keys())
        # logger.info(self.metadata_csv_file_path)
        # logger.info(fields)
        # logger.info(new_data)
        with open(self.metadata_csv_file_path, "w+", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(new_data)
        f.close()

    def delete_old_tempfile(self, temp):
        if os.path.exists(temp):
            os.remove(temp)

    def find(self, s, ch):
        return [i for i, ltr in enumerate(s) if ltr == ch]

    # inputs: date & markers read from the table
    def evaluation(self, root_path, inputs, txt_inputs, progress_bar):
        dict_eval = {}
        patients = []
        if not os.path.exists(root_path):
            logger.warning("The input directory doesn't exist. Doing nothing.Exiting")
            return
        pattern = r'^\d{6}\_[^\_]*'
        subdirs = [x[0] for x in os.walk(root_path) if re.match(pattern, os.path.basename(x[0]))]
        if not subdirs:
            logger.warning(self.input_dir + " is empty. Doing nothing")
            progress_bar.update_bar(100)
            return
        subfolder_patients = []
        for folder in subdirs:
            subfolder_patients.append(os.path.basename(folder).split("_")[1])
        patients = list(set(subfolder_patients))
        counts = []
        for patient in patients:
            counts.append(self.get_patient_subfolder_number(subfolder_patients, patient))
        selected_patients = []
        not_selected_patients = []
        for count, patient in zip(counts, patients):
            if count > 1:
                selected_patients.append(patient)
            else:
                not_selected_patients.append(patient)
        markers = []
        for idate in inputs.keys():
            (i, j) = idate
            if j > 1:
                chn = self.channel_list[j - 2]
                if not inputs[i, 1] == '' and (inputs[idate]) == '' and chn in txt_inputs[inputs[i, 1]]:
                    markers.append(chn)
                elif not (inputs[idate]) == '':
                    markers.append(inputs[idate])
        markers = [x for x in markers if x != '']
        patient_files = {}
        for patient in patients:
            patient_files_list = []
            for folder in subdirs:
                if patient in os.path.basename(folder):
                    patient_files_list = patient_files_list + [ht.correct_path(folder, x).replace("\\", "/") for x in
                                                               os.listdir(folder)]
            patient_files[patient] = patient_files_list

        val = 0
        problem_files = []
        for i, patient in enumerate(patients):
            dict_eval[patient] = {}
            for marker in markers:
                marker_files = []
                shape_size_files = []
                for patient_file_path in patient_files[patient]:
                    if "_" + marker + self.tiff_ext in os.path.basename(patient_file_path):
                        Image.MAX_IMAGE_PIXELS = None
                        try:
                            im = Image.open(patient_file_path)
                            if im:
                                w, h = im.size
                                marker_files.append(os.path.basename(patient_file_path))
                                shape_size_files.append([w, h])
                        except UnidentifiedImageError:
                            problem_files.append(patient_file_path)
                dict_eval[patient][marker] = [marker_files, shape_size_files]
            val = val + 100 / (len(patients) - i)
        progress_bar.update_bar(val)
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Selected patient IDs and counts of batches:")
        for patientID, i in zip(patients, counts):
            if patientID in selected_patients:
                print(patientID + ": " + str(i))
        print("Not selected patient IDs and counts of batches:")
        for patientID, i in zip(patients, counts):
            if patientID in not_selected_patients:
                print(patientID + ": " + str(i))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        for patient in dict_eval:
            print("ID: " + patient)
            print("")
            headers = ['Marker', 'Filename', 'Size']
            for marker in dict_eval[patient]:
                print("--------------------------------------------------------------------")
                print(headers[0] + ": " + marker)
                for i, it in enumerate(dict_eval[patient][marker][0]):
                    print("{:<50}{:<8}".format(headers[1] + ": " + str(it),
                                               headers[2] + ": " + str(dict_eval[patient][marker][1][i])))
            print("**************************************************************************")
        print("Problem files: " + str(problem_files))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    def get_patient_subfolder_number(self, patients, item):
        # folder path
        count = 0
        # Iterate directory
        for curr_item in patients:
            if curr_item == item:
                count += 1
        return count

    def processing(self):
        sG.set_options(dpi_awareness=True)

        empty_text, submit_button, cancel_button, font, key_dir = "", 'Submit', 'Exit', ('Courier New',
                                                                                         11), "-IN2-"
        sG.set_options(font=font)
        read_input_dict = {}
        read_input = {}
        # if self.read_and_fill_channel_for_table_update_from_txt_file() and self.prepareDefaultValues():
        #    read_input_dict = self.read_and_fill_channel_for_table_update_from_txt_file()
        if self.read_data_and_fill_channel_for_table_update_from_csv_file() and self.prepareDefaultValues():
            read_input_dict = self.read_data_and_fill_channel_for_table_update_from_csv_file()
            read_input = self.prepareDefaultValues()
        else:
            logger.warning("Problem while reading the csv file in the workingDir")
        default_date_channels = ["Nr", self.input_dates] + self.channel_list
        MAX_COL = len(default_date_channels)
        MAX_ROWS = 500
        col_width = 13
        progressbar = [
            [sG.ProgressBar(50, orientation='h', size=(int(MAX_COL * 80 / 7), 10), key='progressbar')]
        ]
        outputwin = [
            [sG.Output(size=(int(MAX_COL * 96 / 7), 10))]
        ]

        layout = [
            [sG.T(empty_text)],
            [sG.Text("Input Folder:"),
             # sG.Text("Choose a folder: "),
             sG.Input(self.input_dir, key=key_dir, change_submits=True, enable_events=True, size=(84, 5))  # ,
             # sG.FolderBrowse(key="-IN-")
             ],
            [sG.T(empty_text)],
            [sG.Text(col.center(col_width), pad=(0, 0)) for col in default_date_channels],
            [sG.Column(
                [[sG.Input(size=(col_width, 1), pad=(1, 1), justification='right', key=(i, j), tooltip=None) for j in
                  range(MAX_COL)]
                 for i in range(MAX_ROWS)], size=(int(MAX_COL * 870 / 7), 300), scrollable=True,
                vertical_scroll_only=True, )],
            [sG.Button(submit_button, )],
            [sG.Frame('Progress', layout=progressbar)],
            [sG.Frame('Output', layout=outputwin)],
            [sG.Button(cancel_button)],
        ]
        # Building Window
        window = sG.Window('My File Browser', layout, keep_on_top=True,  # element_justification='c',
                           enable_close_attempted_event=True, finalize=True)
        for cell in read_input:
            cell_input = read_input[cell][0]
            if read_input[cell][0] == '':
                window[cell].update(cell_input, background_color='red')
            else:
                window[cell].update(cell_input)
            window[cell].set_tooltip("Please enter your specific markers for each channel initially marked in red "
                                     "\nhaving no '\_' and no ' '. Check to have batches with different markes for each"
                                     "\n date")

        progress_bar = window['progressbar']
        while True:
            event, values = window.read(timeout=10)
            if event in (sG.WINDOW_CLOSE_ATTEMPTED_EVENT, sG.WIN_CLOSED, cancel_button, 'Exit', '-ESCAPE-'):
                # event, values = sG.Window('Yes/No?', [[sG.Text('Do you want to continue with the next step?')],
                #                                      [sG.Button('Yes'), sG.Button('No')]],
                #                          modal=True, element_justification='c', keep_on_top=True).read(close=True)
                # if event == 'Yes':
                #    break
                break
            elif event == key_dir:
                for cell in read_input:
                    cell_input = read_input[cell][0]
                    if read_input[cell][0] == '':
                        window[cell].update(cell_input, background_color='red')
                    else:
                        window[cell].update(cell_input)
            elif event == submit_button:
                if values[key_dir] == "":
                    sG.popup_error("Please choose a directory", keep_on_top=True)
                else:
                    input_dates_channels_updated = {}
                    for i in range(MAX_ROWS):
                        for j in range(MAX_COL):
                            input_dates_channels_updated[(i, j)] = values[(i, j)]
                    logger.info("submitting done")
                    self.rename_files_recursively(values[key_dir], read_input_dict, input_dates_channels_updated,
                                                  progress_bar, MAX_ROWS)
                    # event, values = sG.Window('Output', [[sG.Text('Renaming is successfully finished. Do you want to '
                    #                                              'rename from the other source?')], [sG.Button('Yes'),
                    #                                                                                  sG.Button('No')]],
                    #                          modal=True, element_justification='c', keep_on_top=True).read(close=True)
                    # if event == 'Yes':
                    #    progress_bar.update_bar(0)
                    # if event == 'No':
                    #    break
