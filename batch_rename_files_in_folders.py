import os
import re
# import Path class from pathlib
from pathlib import Path

import PySimpleGUI as sg
import regex


# import glob
def rename_files_recursively(root_path, ch0, ch1, ch2, ch3):
    # change directory
    os.chdir(root_path)
    # display the current directory
    # cwd = os.getcwd()
    input_replacements = []
    search_input_terms = []
    channels = [ch0, ch1, ch2, ch3]
    #    print(len(channels))
    count = 0
    for channel in channels:
        if channel != "":
            search_input_terms.append("c" + str(count))
            input_replacements.append(channel)
            print(count)
            print(channel)
        count += 1

    standard_search_terms = ["stitching-Image Export", "-Stitching", "-Image Export", " - Copy",
                             "-Background subtraction", "_alpha-SMA-555_CD177-647", "_ORG", "stitching", "-", ".txt",
                             " - Copy"]
    standard_replacements = ["", "", "", "", "", "", "", "", "_", ".csv", "_autobrightctrst"]

    count = 0
    cwd = Path.cwd()
    # create new directory if does not exist
    # if not os.path.isdir(dest_dir):
    #    os.mkdir(dest_dir)
    for dir_path, subdirs, file_names in os.walk(cwd):
        # for filenames in glob.iglob('Path.cwd() / '**' / '*.jpg', recursive=True):
        # print(file_names)
        for filename in file_names:
            if filename.endswith('.tif'):
                name, extension = os.path.splitext(filename)
                substrings = name.split("_")
                #print(substrings[0])
                for i in range(len(substrings)):
                    if re.match(".*c\d.*", substrings[i]):
                        substrings[i] = substrings[i].replace(substrings[i],
                                                              'c' + substrings[i][substrings[i].index('c') + 1])
                        print(substrings[i])
                new_name = '_'.join(substrings)
                #print(new_name)
                search_terms = standard_search_terms + search_input_terms
                replacements = standard_replacements + input_replacements
                for i, term in enumerate(search_terms):
                    if term in name:
                        # prefix = str.name[:11]
                        new_name = new_name.replace(term, replacements[i])
                        # print(new_name)
                        continue
                if name != new_name:
                    os.rename(os.path.join(dir_path, filename),
                              os.path.join(dir_path, new_name + extension))
                    count += 1

    print(f"{count} files were renamed recursively from root {cwd}")


if __name__ == "__main__":
    sg.theme("DarkTeal2")
    layout = [
        [sg.T("")],
        [sg.Text("Choose a folder: "), sg.Input(key="-IN2-", change_submits=True), sg.FolderBrowse(key="-IN-")],
        [sg.Text("Channel0", size=(12, 1)), sg.InputText("0dapi", key="ch0")],
        [sg.Text("Channel1", size=(12, 1)), sg.InputText(key="ch1")],
        [sg.Text("Channel2", size=(12, 1)), sg.InputText(key="ch2")],
        [sg.Text("Channel3", size=(12, 1)), sg.InputText(key="ch3")],
        [sg.Button("Submit"), sg.Button("Cancel")],
    ]

    ###Building Window
    window = sg.Window('My File Browser', layout, size=(600, 200))

    while True:
        event, values = window.read()
        # print(values["-IN2-"])
        if event == sg.WIN_CLOSED or event == "Exit" or event == "Cancel":
            break
        elif event == "Submit":
            if values["-IN2-"] == "":
                sg.popup_error("Please choose a directory")
            if values["ch0"] == "":
                sg.popup_error("Please give at least channel 0")
            try:
                # print(values["-IN-"])
                rename_files_recursively(values["-IN2-"], values["ch0"], values["ch1"], values["ch2"], values["ch3"])
            except:
                values["-IN2-"] = ""
                values["ch0"] = ""
                pass

    window.close()
