import os
import re
# import Path class from pathlib
from pathlib import Path

import PySimpleGUI as sG


def text_over_input(text, input_size, dates_length):
    return sG.Column(
        [[sG.Text(text, pad=(0, 3))]] + [[sG.Input(key=text + str(counter), size=(input_size, 1), pad=(0, 3))] for
                                         counter in range(dates_length)], pad=(5, 5))


def rename_files_recursively(root_path, dapi, inputs):
    # change directory
    os.chdir(root_path)
    input_replacements = []
    search_input_terms = ["c0"]
    input_replacements.append(dapi)

    standard_search_terms = ["stitching-Image Export", "-Stitching", "-Image Export", " - Copy",
                             "-Background subtraction", "_alpha-SMA-555_CD177-647", "_ORG", "stitching", "-"]
    standard_replacements = ["", "", "", "", "", "", "", "", "_"]

    count = 0
    cwd = Path.cwd()
    base_dir = os.path.basename(cwd)
    new_base_dir_name = base_dir
    new_basepath = ""
    for counter, term in enumerate(standard_search_terms):
        if term in base_dir:
            new_base_dir_name = new_base_dir_name.replace(term, standard_replacements[counter])
            back_dir = os.path.dirname(os.path.dirname(cwd))
            new_basepath = os.path.join(back_dir, new_base_dir_name)
    if new_base_dir_name != base_dir and not os.path.exists(new_basepath):
        os.rename(cwd, new_basepath)
    for subdir in os.listdir(cwd):
        new_subdir_name = subdir
        for counter, term in enumerate(standard_search_terms):
            if term in subdir:
                new_subdir_name = new_subdir_name.replace(term, standard_replacements[counter])
        if not os.path.exists(new_subdir_name):
            os.rename(os.path.join(cwd, subdir), os.path.join(cwd, new_subdir_name))
    for dir_path, subdirs, file_names in os.walk(cwd):
        for filename in file_names:
            if filename.endswith('.tif'):
                name, extension = os.path.splitext(filename)
                substrings = name.split("_")
                for counter in range(len(substrings)):
                    if re.match(r'.*c\d.*', substrings[counter]):
                        substrings[counter] = substrings[counter].replace(substrings[counter],
                                                                          'c' + substrings[counter][
                                                                              substrings[counter].index('c') + 1])
                new_name = '_'.join(substrings)
                for idate in inputs.keys():
                    if idate != "" and idate in new_name:
                        if "c1" in name:
                            new_name = new_name.replace("c1", inputs.get(idate)[0])
                        if "c2" in new_name:
                            new_name = new_name.replace("c2", inputs.get(idate)[1])
                        if "c3" in new_name:
                            new_name = new_name.replace("c3", inputs.get(idate)[2])
                search_terms = standard_search_terms + search_input_terms
                replacements = standard_replacements + input_replacements
                for counter, term in enumerate(search_terms):
                    if term in name:
                        new_name = new_name.replace(term, replacements[counter])
                new_file_path = os.path.join(dir_path, new_name + extension)
                if name != new_name and not os.path.exists(new_file_path):
                    os.rename(os.path.join(dir_path, filename),
                              new_file_path)
                    count += 1

    print(f"{count} files were renamed recursively from root {cwd}")


if __name__ == "__main__":
    font = ('Courier New', 11)
    sG.set_options(font=font)
    size = 15
    dates_number = 10
    cols = (('dates', size), ('channel 1', size), ('channel 2', size), ('channel 3', size))
    layout = [
        [sG.T("")],
        [sG.Text("Choose a folder: "), sG.Input(key="-IN2-", change_submits=True, enable_events=True),
         sG.FolderBrowse(key="-IN-")],
        [sG.T("")],
        [sG.Text("Dapi Channel", size=(15, 1)), sG.InputText("0dapi", key="ch0", size=(15, 1))],
        [sG.T("")],
        [*[text_over_input(*col, dates_number) for col in cols]],
        [sG.Button("Submit"), sG.Button("Cancel")]
    ]

    # Building Window
    window = sG.Window('My File Browser', layout, keep_on_top=True, element_justification='c')

    while True:
        event, values = window.read()
        if event == sG.WIN_CLOSED or event == "Exit" or event == "Cancel":
            break
        elif event == "-IN2-":
            folder = values["-IN2-"]
            try:
                # Get list of files in folder
                file_list = os.listdir(folder)
            except:
                file_list = []
            fnames = [
                f
                for f in file_list
                if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith('infos.txt')
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

            for i in range(len(date_channels_to_edit)):
                idates = "dates" + str(i)
                ichOne = "channel 1" + str(i)
                ichTwo = "channel 2" + str(i)
                ichThree = "channel 3" + str(i)
                ivalues = date_channels_to_edit[i].split(" ")
                if len(ivalues) == 4:
                    window[idates].update(ivalues[0])
                    window[ichOne].update(ivalues[1])
                    window[ichTwo].update(ivalues[2])
                    window[ichThree].update(ivalues[3])
                if len(ivalues) == 3:
                    window[idates].update(ivalues[0])
                    window[ichOne].update(ivalues[1])
                    window[ichTwo].update(ivalues[2])
                if len(values) == 2:
                    window[idates].update(ivalues[0])
                    window[ichOne].update(ivalues[1])
                if len(ivalues) == 1:
                    window[idates].update(ivalues[0])
                else:
                    continue

        elif event == "Submit":
            if values["-IN2-"] == "":
                sG.popup_error("Please choose a directory")
            if values["ch0"] == "":
                sG.popup_error("Please give at least channel 0")
            try:
                input_dates_channels_updated = {}
                for i in range(dates_number):
                    input_dates_channels_updated[values["dates" + str(i)]] = [values["channel 1" + str(i)],
                                                                              values["channel 2" + str(i)],
                                                                              values["channel 3" + str(i)]]
                rename_files_recursively(values["-IN2-"], values["ch0"], input_dates_channels_updated)
            except:
                values["-IN2-"] = ""
                values["ch0"] = ""
                pass
