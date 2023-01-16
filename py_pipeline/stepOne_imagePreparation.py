import os
import sys

import numpy
import pandas as pd

import config
import re
from pathlib import Path
import PySimpleGUI as sG
import time
import pythontools as pt
import PIL
from PIL import Image


def read_and_fill_channel_for_table_update(folder):
    try:
        # Get list of files in folder
        file_list = os.listdir(folder)
    except:
        file_list = []
    fnames = [
        f
        for f in file_list
        if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(config.info_txt_file)
    ]

    input_dates_channels = {}
    if len(fnames) == 1:
        with open(os.path.join(folder, fnames[0])) as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if re.match(r'^\d{6}$', line):
                    channels = []
                    for j in range(i + 1, len(lines), 1):
                        if re.match(r'^c\d.*\w*$', lines[j]):
                            channels.append(lines[j].strip())
                        else:
                            break
                        input_dates_channels[line.strip()] = channels
    date_channels_to_edit = []
    for date in input_dates_channels.keys():
        date_channels_string = date
        channels = ""
        for channel in input_dates_channels.get(date):
            channels = channels + channel.split(" ")[1] + " "
        date_channels_string = date_channels_string + " " + channels.strip()
        date_channels_to_edit.append(date_channels_string)
    return date_channels_to_edit


def prepareDefaultValues(dates_length):
    date_channels_to_edit = read_and_fill_channel_for_table_update(config.inputDir)
    if date_channels_to_edit:
        dfdata = {}
        idates = config.input_dates
        for i in range(len(date_channels_to_edit)):
            ivalues = date_channels_to_edit[i].split(" ")
            value_length = len(ivalues)
            if value_length == 4:
                dfdata.setdefault(idates, []).append(ivalues[0])
                for ch in range(len(config.channel_list)):
                    dfdata.setdefault(config.channel_list[ch], []).append(ivalues[ch + 1])
            elif value_length == 3:
                dfdata.setdefault(idates, []).append(ivalues[0])
                for ch in range(len(config.channel_list[:2])):
                    dfdata.setdefault(config.channel_list[ch], []).append(ivalues[ch + 1])
                for ch in range(2, len(config.channel_list)):
                    dfdata.setdefault(config.channel_list[ch], []).append("")

            elif value_length == 2:
                dfdata.setdefault(idates, []).append(ivalues[0])
                for ch in range(len(config.channel_list[:1])):
                    dfdata.setdefault(config.channel_list[ch], []).append(ivalues[ch + 1])
                for ch in range(1, len(config.channel_list)):
                    dfdata.setdefault(config.channel_list[ch], []).append("")
            elif value_length == 1:
                dfdata.setdefault(idates, []).append(ivalues[0])
                for ch in range(len(config.channel_list)):
                    dfdata.setdefault(config.channel_list[ch], []).append("")
            else:
                print("More than 4 channels will be skipped")
                continue

        length = dates_length - len(dfdata[idates])
        for key in dfdata.keys():
            dfdata[key] = dfdata.get(key) + length * ['']
        return [dfdata.get(key) for key in dfdata.keys()]
    else:
        return [[''] * dates_length, [''] * dates_length, [''] * dates_length, [''] * dates_length]


def text_over_input(text, input_size, dates_length, col):
    return sG.Column(
        [[sG.Text(text, pad=(0, 3))]] + [
            [sG.Input(col[counter], key=text + str(counter), size=(input_size, 1), pad=(0, 3))] for
            counter in range(dates_length)], pad=(5, 5))


def rename_files_recursively(root_path, dapi_ch, dapi, inputs, progress_bar):
    # change directory
    os.chdir(root_path)
    search_input_terms = [dapi_ch]
    input_replacements = [dapi]

    count = 0
    cwd = Path.cwd()
    for subdir in os.listdir(cwd):
        if not os.path.isfile(subdir):
            new_subdir_name = subdir
            for counter, term in enumerate(config.standard_search_terms):
                if term in subdir:
                    new_subdir_name = new_subdir_name.replace(term, config.standard_replacements[counter])
            pattern = r'-Stitching[^c]*|(?<=c\d)(.*)'
            if re.match(r'.*' + pattern, new_subdir_name):
                new_subdir_name = re.sub(pattern, '', new_subdir_name)
            if not os.path.exists(new_subdir_name):
                os.rename(os.path.join(cwd, subdir), os.path.join(cwd, new_subdir_name))
    for dir_path, subdirs, file_names in os.walk(cwd):
        for filename in file_names:
            if filename.endswith('.tif'):
                name, extension = os.path.splitext(filename)
                new_name = name
                pattern = r'-Stitching[^c]*|(?<=c\d)(.*)'
                if re.match(r'.*' + pattern, new_name):
                    new_name = re.sub(pattern, ' ', new_name).strip(' ')
                for idate in inputs.keys():
                    if idate != "" and idate in new_name:
                        for pat in range(len(config.channel_patterns)):
                            if config.channel_patterns[pat] in name:
                                new_name = new_name.replace(config.channel_patterns[pat], inputs.get(idate)[pat])
                search_terms = config.standard_search_terms + search_input_terms
                replacements = config.standard_replacements + input_replacements
                for counter, term in enumerate(search_terms):
                    if term in name:
                        new_name = new_name.replace(term, replacements[counter])
                new_file_path = os.path.join(dir_path, new_name + extension)
                if name != new_name and not os.path.exists(new_file_path):
                    os.rename(os.path.join(dir_path, filename),
                              new_file_path)
                    count += 1
    print(f"{count} files were renamed recursively from root {cwd}")

    sys.stdout.flush()
    evaluation(root_path, dapi, inputs, progress_bar)


def evaluation(root_path, dapi, inputs, progress_bar):
    dict_eval = {}
    patients = []
    if not os.path.exists(root_path):
        print("The input directory doesn't exist. Doing nothing.Exiting")
        return
    pattern = r'^\d{6}\_[^\_]*'
    subdirs = [x[0] for x in os.walk(root_path) if re.match(pattern, os.path.basename(x[0]))]
    if not subdirs:
        print(config.inputDir + " is empty. Doing nothing")
        return
    subfolder_patients = []
    for folder in subdirs:
        # print(os.path.basename(folder).split("_")[1])
        subfolder_patients.append(os.path.basename(folder).split("_")[1])
    patients = list(set(subfolder_patients))
    # print(patients)
    markers = [dapi]
    for idate in inputs.keys():
        for pat in range(len(config.channel_patterns)):
            markers.append(inputs.get(idate)[pat])
    markers = [x for x in markers if x != '']
    # print(markers)
    patient_files = {}
    for patient in patients:
        patient_files_list = []
        for folder in subdirs:
            # print(folder)
            # print(patient)
            if patient in os.path.basename(folder):
                patient_files_list = patient_files_list + [os.path.join(folder, x).replace("\\", "/") for x in
                                                           os.listdir(folder)]

        patient_files[patient] = patient_files_list

    val=0
    for i,patient in enumerate(patients):
        dict_eval[patient] = {}
        for marker in markers:
            marker_files = []
            shape_size_files = []
            for patient_file in patient_files[patient]:
                # print(patient_file)
                if "_" + marker + config.tiff_ext in os.path.basename(patient_file):
                    marker_files.append(patient_file)
                    # print(patient_file)
                    Image.MAX_IMAGE_PIXELS = None
                    im = Image.open(patient_file)
                    imarray = numpy.array(im)
                    w, h = im.size
                    shape_size_files.append([w, h])
            dict_eval[patient][marker] = [marker_files, shape_size_files]
    val = val+100/(len(patients)-i)
    progress_bar.update_bar(val)
    # print(dict_eval)
    print("Evaluation:")
    for patient in dict_eval:
        print("**********************************")
        print("ID: " + patient)
        headers = ['Marker', 'Filename(s)', 'Size(s)']
        print(f'{headers[0]: <50}{headers[1]: <50}{headers[2]: <50}')
        for marker in dict_eval[patient]:
            # print(marker, ':', dict_eval[patient][marker])
            print(f'{marker: <50}{str(dict_eval[patient][marker][0]):<50}{str(dict_eval[patient][marker][1]): <50}')
        print("**********************************")


def main():
    empty_text, submit_button, cancel_button, font, size, input_dir = "", 'Submit', 'Exit', ('Courier New',
                                                                                             11), 15, "-IN2-"
    cols = ((config.input_dates, size), (config.channel_list[0], size),
            (config.channel_list[1], size), (config.channel_list[2], size))
    sG.set_options(font=font)
    input_default = prepareDefaultValues(config.dates_number)
    progressbar = [
        [sG.ProgressBar(50, orientation='h', size=(51, 10), key='progressbar')]
    ]
    outputwin = [
        [sG.Output(size=(78, 10))]
    ]
    layout = [
        [sG.T(empty_text)],
        [sG.Text("Choose a folder: "),
         sG.Input(config.inputDir, key=input_dir, change_submits=True, enable_events=True),
         sG.FolderBrowse(key="-IN-")],
        [sG.T(empty_text)],
        [sG.Text(config.table_dapi_title, size=(15, 1)), sG.InputText(config.table_dapi_entry, key=config.dapi_channel,
                                                                      size=(15, 1))],
        [sG.T(empty_text)],
        [*[text_over_input(*col, config.dates_number, dv) for col, dv in zip(cols, input_default)]],
        [sG.Frame('Progress', layout=progressbar)],
        [sG.Frame('Output', layout = outputwin)],
        [sG.Button(submit_button), sG.Button(cancel_button)]
    ]
    # Building Window
    window = sG.Window('My File Browser', layout, keep_on_top=True, element_justification='c',
                       enable_close_attempted_event=True)
    progress_bar = window['progressbar']
    while True:
        event, values = window.read(timeout=10)
        if event in (sG.WINDOW_CLOSE_ATTEMPTED_EVENT, sG.WIN_CLOSED, cancel_button, 'Exit', '-ESCAPE-'):
            event, values = sG.Window('Yes/No?', [[sG.Text('Do you really want cancel/exit?')],
                                                  [sG.Button('Yes'), sG.Button('No')]],
                                      modal=True, element_justification='c', keep_on_top=True).read(close=True)
            if event == 'Yes':
                break
        elif event == input_dir:
            folder = values[input_dir]
            date_channels_to_edit = read_and_fill_channel_for_table_update(folder)
            for i in range(len(date_channels_to_edit)):
                idates = config.input_dates + str(i)
                ivalues = date_channels_to_edit[i].split(" ")
                if len(ivalues) == 4:
                    window[idates].update(ivalues[0])
                    for ch in range(len(config.channel_list)):
                        window[config.channel_list[ch] + str(i)].update(ivalues[ch + 1])
                if len(ivalues) == 3:
                    window[idates].update(ivalues[0])
                    for ch in range(len(config.channel_list[:2])):
                        window[config.channel_list[ch] + str(i)].update(ivalues[ch + 1])
                if len(ivalues) == 2:
                    window[idates].update(ivalues[0])
                    for ch in range(len(config.channel_list[:1])):
                        window[config.channel_list[ch] + str(i)].update(ivalues[ch + 1])
                if len(ivalues) == 1:
                    window[idates].update(ivalues[0])
                else:
                    continue

        elif event == submit_button:
            if values[input_dir] == "":
                sG.popup_error("Please choose a directory", keep_on_top=True)
            elif values[config.dapi_channel] == "":
                sG.popup_error("Please give at least channel 0", keep_on_top=True)
            else:
                input_dates_channels_updated = {}
                for i in range(config.dates_number):
                    input_dates_channels_updated[values[config.input_dates + str(i)]] = [
                        values[config.channel_list[0] + str(i)],
                        values[config.channel_list[1] + str(i)],
                        values[config.channel_list[2] + str(i)]]
                rename_files_recursively(values[input_dir], config.dapi_channel, values[config.dapi_channel],
                                         input_dates_channels_updated, progress_bar)
                event, values = sG.Window('Output', [[sG.Text('Renaming is successfully finished. Do you want to '
                                                              'rename from the other source?')], [sG.Button('Yes'),
                                                                                                  sG.Button('No')]],
                                          modal=True, element_justification='c', keep_on_top=True).read(close=True)
                if event == 'No':
                    break


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
