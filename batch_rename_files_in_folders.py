import os
import re
# import Path class from pathlib
from pathlib import Path

import PySimpleGUI as sg


# import glob
def rename_files_recursively(root_path, date1, date2, date3, date4, date5, date6, date7, date8, date9, date10):
    # change directory
    os.chdir(root_path)
    # display the current directory
    # cwd = os.getcwd()
    input_replacements = []
    search_input_terms = []
    dicti = {}
    for i in range(10):
        dicti[date1[i].split(" ")[0]] = date1[i].split(" ")[1:]
    print(dicti)
    channels = []
    #    print(len(channels))
    count = 0
    for channel in channels:
        if channel != "":
            search_input_terms.append("c" + str(count))
            input_replacements.append(channel)
            # print(count)
            # print(channel)
        count += 1

    standard_search_terms = ["stitching-Image Export", "-Stitching", "-Image Export", " - Copy",
                             "-Background subtraction", "_alpha-SMA-555_CD177-647", "_ORG", "stitching", "-",
                             " - Copy"]
    standard_replacements = ["", "", "", "", "", "", "", "", "_", "_autobrightctrst"]

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
                # print(substrings[0])
                for i in range(len(substrings)):
                    if re.match(".*c\d.*", substrings[i]):
                        substrings[i] = substrings[i].replace(substrings[i],
                                                              'c' + substrings[i][substrings[i].index('c') + 1])
                        # print(substrings[i])
                new_name = '_'.join(substrings)
                # print(new_name)
                search_terms = standard_search_terms + search_input_terms
                replacements = standard_replacements + input_replacements
                for i, term in enumerate(search_terms):
                    if term in name:
                        new_name = new_name.replace(term, replacements[i])
                        continue
                if name != new_name:
                    os.rename(os.path.join(dir_path, filename),
                              os.path.join(dir_path, new_name + extension))
                    count += 1

    print(f"{count} files were renamed recursively from root {cwd}")


if __name__ == "__main__":
    #    for root, dirs, files in os.walk("/mydir"):
    #        for file in files:
    #            if file.endswith(".txt") and file.__contains__("shading missing use automatic"):
    #                print(os.path.join(root, file))
    sg.theme("DarkTeal2")
    layout = [
        [sg.T("")],
        [sg.Text("Choose a folder: "), sg.Input(key="-IN2-", change_submits=True, enable_events=True),
         sg.FolderBrowse(key="-IN-")],
        # [sg.Listbox(
        #   values=[], enable_events=True, size=(50, 5), key="-DatesChannels LIST-"
        # )
        # ],

        [sg.Text("Channel0", size=(5, 1)), sg.InputText("0dapi", key="ch0")],
        [sg.Text("date1", size=(5, 1)), sg.InputText(key="date1")],
        [sg.Text("date2", size=(5, 1)), sg.InputText(key="date2")],
        [sg.Text("date3", size=(5, 1)), sg.InputText(key="date3")],
        [sg.Text("date4", size=(5, 1)), sg.InputText(key="date4")],
        [sg.Text("date5", size=(5, 1)), sg.InputText(key="date5")],
        [sg.Text("date6", size=(5, 1)), sg.InputText(key="date6")],
        [sg.Text("date7", size=(5, 1)), sg.InputText(key="date7")],
        [sg.Text("date8", size=(5, 1)), sg.InputText(key="date8")],
        [sg.Text("date9", size=(5, 1)), sg.InputText(key="date9")],
        [sg.Text("date10", size=(5, 1)), sg.InputText(key="date10")],
        [sg.Button("Submit"), sg.Button("Cancel")],
    ]

    ###Building Window
    window = sg.Window('My File Browser', layout, size=(600, 500))

    while True:
        event, values = window.read()
        # print(values["-IN2-"])
        if event == sg.WIN_CLOSED or event == "Exit" or event == "Cancel":
            break
        elif event == "-IN2-":
            folder = values["-IN2-"]
            try:
                # Get list of files in folder
                file_list = os.listdir(folder)
                # print(file_list)
            except:
                file_list = []
            fnames = [
                f
                for f in file_list
                if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith('infos.txt')
                # and not f.__contains__(                    'shading missing use automatic')
            ]

            myDict = {}
            if len(fnames) == 1:
                with open(os.path.join(folder, fnames[0])) as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if re.match("^\d{6}$", line):
                            channels = []
                            for j in range(i + 1, len(lines), 1):
                                # print(lines[j])
                                if re.match("^c\d.*\w*$", lines[j]):
                                    channels.append(lines[j].strip())
                                    # print(channels[0])
                                else:
                                    break
                                myDict[line.strip()] = channels
                    #          print(myDict)
            datech = []
            for key in myDict.keys():
                strin = key
                stri = ""
                for value in myDict.get(key):
                    stri = stri + value.split(" ")[1] + " "
                strin = strin + " " + stri + " "
                datech.append(strin)
            for i in range(len(datech)):
                chan = "date" + str(i + 1)
                window[chan].update(datech[i])
        elif event == "Submit":
            if values["-IN2-"] == "":
                sg.popup_error("Please choose a directory")
            if values["ch0"] == "":
                sg.popup_error("Please give at least channel 0")
            try:
                # print(values["-IN-"])
                rename_files_recursively(values["-IN2-"], values["ch0"], values["date1"], values["date2"],
                                         values["date3"], values["date4"], values["date5"], values["date6"],
                                         values["date7"], values["date8"], values["date9"], values["date10"])
            except:
                values["-IN2-"] = ""
                values["ch0"] = ""
                pass

# TDo: cover the case if the same files as have to be saved are already in the folder
