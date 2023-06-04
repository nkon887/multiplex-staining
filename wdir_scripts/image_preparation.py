import os
import sys
import config
import re
from pathlib import Path
import PySimpleGUI as sG
import time
import pythontools as pt
from PIL import Image, UnidentifiedImageError


class ImagePreparation:
    def __init__(self, input_dir, info_txt_file, input_dates, channel_list, standard_search_terms,
                 standard_replacements, tiff_ext, dates_number, dapi_str):
        self.input_dir = input_dir
        self.info_txt_file = info_txt_file
        self.input_dates = input_dates
        self.channel_list = channel_list
        self.standard_search_terms = standard_search_terms
        self.standard_replacements = standard_replacements
        self.tiff_ext = tiff_ext
        self.dates_number = dates_number
        self.dapi_str = dapi_str

    def read_and_fill_channel_for_table_update_from_txt_file(self):
        folder = self.input_dir
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []
        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(self.info_txt_file)
        ]

        input_dates_channels_markers = {}
        if len(fnames) == 1:
            with open(os.path.join(folder, fnames[0])) as f:
                # read all lines in a list
                lines = f.readlines()
                for i, line in enumerate(lines):
                    # check if string present on a current line
                    if re.match(r'^\d{6}$', line):
                        channel_marker = {}
                        for j in range(i + 1, len(lines), 1):
                            if re.match(r'^\d{6}$', lines[j]):
                                break
                            for channel in self.channel_list:
                                if lines[j].find(channel) != -1:  # if re.match(r'^c\d.*\w*$', lines[j]):
                                    channel_marker_str = lines[j].strip()
                                    channel_marker_list = channel_marker_str.split(" ")
                                    check_length = len(channel_marker_list)
                                    if check_length == 2:
                                        channel_marker[channel_marker_list[0]] = channel_marker_list[1]
                                    elif check_length == 1:
                                        channel_marker[channel_marker_list[0]] = ""
                                        if channel_marker_list[0] == self.dapi_str.upper():
                                            channel_marker[channel_marker_list[0]] = f"0{self.dapi_str}"
                                    else:
                                        print("No channels. Something went wrong with the images")
                        date = line.strip()
                        input_dates_channels_markers[date] = channel_marker
        return input_dates_channels_markers

    def prepareDefaultValues(self):
        date_channels_markers = self.read_and_fill_channel_for_table_update_from_txt_file()
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

            return date_channels_markers, dfdata

    def text_over_input(self, text, input_size, dates_length, col):
        return sG.Column(
            [[sG.Input(col[counter], key=text + str(counter), size=(input_size, 1), pad=(0, 3))] for
             counter in range(dates_length)], pad=(5, 5), scrollable=True,
            vertical_scroll_only=True)

    def rename_files_recursively(self, root_path, txt_inputs, inputs, progress_bar, MAX_ROWS):
        # change directory
        os.chdir(root_path)
        search_input_terms = []
        input_replacements = []

        count = 0
        cwd = Path.cwd()
        for subdir in os.listdir(cwd):
            if not os.path.isfile(subdir):
                new_subdir_name = subdir
                index = 6
                for counter, term in enumerate(self.standard_search_terms):
                    if term in new_subdir_name:
                        indices = self.find(new_subdir_name, term)
                        indices_number = len(indices)
                        if indices_number == 1 and term == " " and new_subdir_name.find(term) == index:
                            new_subdir_name = new_subdir_name[:index] + self.standard_replacements[
                                counter] + new_subdir_name[index + 1:]
                        elif indices_number == 1 and term == " " and new_subdir_name.find(term) != index:
                            new_subdir_name = new_subdir_name.replace(term, "-")
                        elif indices_number > 1 and term == " " and new_subdir_name.find(term) == index:
                            new_subdir_name = new_subdir_name[:index] + self.standard_replacements[
                                counter] + new_subdir_name[index + 1:]
                            new_subdir_name = new_subdir_name.replace(term, "-")
                pattern = r'-Stitching[^c]*|(?<=c\d)(.*)'
                if re.match(r'.*' + pattern, new_subdir_name):
                    new_subdir_name = re.sub(pattern, '', new_subdir_name)
                if not os.path.exists(new_subdir_name):
                    os.rename(os.path.join(cwd, subdir), os.path.join(cwd, new_subdir_name))
        for dir_path, subdirs, file_names in os.walk(cwd):
            for filename in file_names:
                if filename.endswith(self.tiff_ext):
                    name, extension = os.path.splitext(filename)
                    new_name = name
                    pattern = r'-Stitching[^c]*|(?<=c\d)(.*)'
                    if re.match(r'.*' + pattern, new_name):
                        new_name = re.sub(pattern, ' ', new_name).strip(' ')
                    for i in range(MAX_ROWS):
                        date = inputs[(i, 1)]
                        if date in new_name and date in txt_inputs:
                            for def_ch in txt_inputs[date]:
                                j = 2 + self.channel_list.index(def_ch)
                                cur_ch = inputs[(i, j)]
                                if cur_ch != "":
                                    if def_ch in new_name and cur_ch != def_ch:
                                        new_name = new_name.replace(def_ch, cur_ch)
                                    elif txt_inputs[date][def_ch] in new_name and cur_ch != txt_inputs[date][def_ch] and \
                                            txt_inputs[date][def_ch] != "":
                                        new_name = new_name.replace(txt_inputs[date][def_ch], cur_ch)
                    search_terms = self.standard_search_terms + search_input_terms
                    replacements = self.standard_replacements + input_replacements
                    index = 6
                    for counter, term in enumerate(search_terms):
                        if term in name:
                            indices = self.find(name, term)
                            indices_number = len(indices)
                            if indices_number == 1 and term == " " and new_name.find(term) == index:
                                new_name = new_name[:index] + replacements[counter] + new_name[index + 1:]
                            elif indices_number == 1 and term == " " and new_name.find(term) != index:
                                new_name = new_name.replace(term, "-")
                            elif indices_number > 1 and term == " " and new_name.find(term) == index:
                                new_name = new_name[:index] + replacements[counter] + new_name[index + 1:]
                                new_name = new_name.replace(term, "-")

                    new_file_path = os.path.join(dir_path, new_name + extension)
                    if name != new_name and not os.path.exists(new_file_path):
                        os.rename(os.path.join(dir_path, filename),
                                  new_file_path)
                        count += 1
        print(f"{count} files were renamed recursively from root {cwd}")

        sys.stdout.flush()
        for i in range(MAX_ROWS):
            date = inputs[(i, 1)]
            if date in txt_inputs:
                for def_ch in txt_inputs[date]:
                    j = 2 + self.channel_list.index(def_ch)
                    cur_ch = inputs[(i, j)]
                    txt_inputs[date][def_ch] = cur_ch
        self.evaluation(root_path, inputs, txt_inputs, progress_bar)
        self.rewrite_infos_txt_file(txt_inputs)

    def rewrite_infos_txt_file(self, txt_inputs):
        write_file = open(self.info_txt_file, "w")
        for date in txt_inputs:
            write_file.write(date + "\n")
            for chn in txt_inputs[date]:
                write_file.write(chn + " " + txt_inputs[date][chn] + "\n")
        write_file.close()

    def find(self, s, ch):
        return [i for i, ltr in enumerate(s) if ltr == ch]

    # inputs: date & markers read from the table
    def evaluation(self, root_path, inputs, txt_inputs, progress_bar):
        dict_eval = {}
        patients = []
        if not os.path.exists(root_path):
            print("The input directory doesn't exist. Doing nothing.Exiting")
            return
        pattern = r'^\d{6}\_[^\_]*'
        subdirs = [x[0] for x in os.walk(root_path) if re.match(pattern, os.path.basename(x[0]))]
        if not subdirs:
            print(self.input_dir + " is empty. Doing nothing")
            progress_bar.update_bar(100)
            return
        subfolder_patients = []
        for folder in subdirs:
            subfolder_patients.append(os.path.basename(folder).split("_")[1])
        patients = list(set(subfolder_patients))
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
                    patient_files_list = patient_files_list + [os.path.join(folder, x).replace("\\", "/") for x in
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
        print("Evaluation:")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        for patient in dict_eval:
            print("ID: " + patient)
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

    def processing(self):
        sG.set_options(dpi_awareness=True)

        empty_text, submit_button, cancel_button, font, size, key_dir = "", 'Submit', 'Exit', ('Courier New',
                                                                                               11), 15, "-IN2-"
        sG.set_options(font=font)
        if self.prepareDefaultValues():
            read_input_dict, read_input = self.prepareDefaultValues()
        else:
            print("Problem while reading the csv file in the workingDir")
        progressbar = [
            [sG.ProgressBar(50, orientation='h', size=(51, 10), key='progressbar')]
        ]
        outputwin = [
            [sG.Output(size=(78, 10))]
        ]
        default_date_channels = ["Nr", self.input_dates] + self.channel_list
        MAX_COL = len(default_date_channels)
        MAX_ROWS = 1000
        col_width = 10
        layout = [
            [sG.T(empty_text)],
            [sG.Text("Choose a folder: "),
             sG.Input(self.input_dir, key=key_dir, change_submits=True, enable_events=True),
             sG.FolderBrowse(key="-IN-")],
            [sG.T(empty_text)],
            [sG.Text(col.center(col_width), pad=(0, 0)) for col in default_date_channels],
            [sG.Column([[sG.Input(size=(10, 1), pad=(1, 1), justification='right', key=(i, j)) for j in range(MAX_COL)]
                        for i in range(MAX_ROWS)], size=(700, 300), scrollable=True,
                       vertical_scroll_only=True)],
            [sG.Frame('Progress', layout=progressbar)],
            [sG.Frame('Output', layout=outputwin)],
            [sG.Button(submit_button), sG.Button(cancel_button)],
        ]
        # Building Window
        window = sG.Window('My File Browser', layout, keep_on_top=True,  # element_justification='c',
                           enable_close_attempted_event=True, finalize=True)
        progress_bar = window['progressbar']
        while True:
            event, values = window.read(timeout=10)
            if event in (sG.WINDOW_CLOSE_ATTEMPTED_EVENT, sG.WIN_CLOSED, cancel_button, 'Exit', '-ESCAPE-'):
                event, values = sG.Window('Yes/No?', [[sG.Text('Do you want to continue with the next step?')],
                                                      [sG.Button('Yes'), sG.Button('No')]],
                                          modal=True, element_justification='c', keep_on_top=True).read(close=True)
                if event == 'Yes':
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
                    print("submitting done")
                    self.rename_files_recursively(values[key_dir], read_input_dict, input_dates_channels_updated,
                                                  progress_bar, MAX_ROWS)
                    event, values = sG.Window('Output', [[sG.Text('Renaming is successfully finished. Do you want to '
                                                                  'rename from the other source?')], [sG.Button('Yes'),
                                                                                                      sG.Button('No')]],
                                              modal=True, element_justification='c', keep_on_top=True).read(close=True)
                    if event == 'Yes':
                        progress_bar.update_bar(0)
                    if event == 'No':
                        break


def main():
    ImagePreparation(config.input_dir, config.info_txt_file, config.input_dates, config.default_channels,
                     config.standard_search_terms, config.standard_replacements, config.tiff_ext,
                     config.dates_number, config.dapi_str).processing()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
