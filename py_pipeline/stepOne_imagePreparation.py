import config
import re
from pathlib import Path
import PySimpleGUI as sG


def text_over_input(text, input_size, dates_length):
    return sG.Column(
        [[sG.Text(text, pad=(0, 3))]] + [[sG.Input(key=text + str(counter), size=(input_size, 1), pad=(0, 3))] for
                                         counter in range(dates_length)], pad=(5, 5))


def rename_files_recursively(root_path, dapi_ch, dapi, inputs):
    # change directory
    config.os.chdir(root_path)
    search_input_terms = [dapi_ch]
    input_replacements = [dapi]

    count = 0
    cwd = Path.cwd()
    for subdir in config.os.listdir(cwd):
        if not config.os.path.isfile(subdir):
            new_subdir_name = subdir
            for counter, term in enumerate(config.standard_search_terms):
                if term in subdir:
                    new_subdir_name = new_subdir_name.replace(term, config.standard_replacements[counter])
            pattern = r'-Stitching-\d.*'
            if re.match(r'.*' + pattern, new_subdir_name):
                new_subdir_name = re.sub(pattern, '', new_subdir_name)
            if not config.os.path.exists(new_subdir_name):
                config.os.rename(config.os.path.join(cwd, subdir), config.os.path.join(cwd, new_subdir_name))
    for dir_path, subdirs, file_names in config.os.walk(cwd):
        for filename in file_names:
            if filename.endswith('.tif'):
                name, extension = config.os.path.splitext(filename)
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
                new_file_path = config.os.path.join(dir_path, new_name + extension)
                if name != new_name and not config.os.path.exists(new_file_path):
                    config.os.rename(config.os.path.join(dir_path, filename),
                                     new_file_path)
                    count += 1
    print(f"{count} files were renamed recursively from root {cwd}")


def main():

    empty_text = ""
    submit_button = 'Submit'
    exit_button = 'Exit'
    cancel_button = 'Cancel'
    font = ('Courier New', 11)
    size = 15
    input_dir = "-IN2-"
    cols = ((config.input_dates, size), (config.channel_list[0], size),
            (config.channel_list[1], size), (config.channel_list[2], size))
    sG.set_options(font=font)
    layout = [
        [sG.T(empty_text)],
        [sG.Text("Choose a folder: "),
         sG.Input(config.inputDir, key=input_dir, change_submits=True, enable_events=True),
         sG.FolderBrowse(key="-IN-")],
        [sG.T(empty_text)],
        [sG.Text(config.table_dapi_title, size=(15, 1)), sG.InputText(config.table_dapi_entry, key=config.dapi_channel,
                                                                      size=(15, 1))],
        [sG.T(empty_text)],
        [*[text_over_input(*col, config.dates_number) for col in cols]],
        [sG.Button(submit_button), sG.Button(cancel_button)]
    ]

    # Building Window
    window = sG.Window('My File Browser', layout, keep_on_top=True, element_justification='c')
    while True:
        event, values = window.read()
        if event == sG.WIN_CLOSED or event == exit_button or event == cancel_button:
            break
        elif event == input_dir:
            folder = values[input_dir]
            try:
                # Get list of files in folder
                file_list = config.os.listdir(folder)
            except:
                file_list = []
            fnames = [
                f
                for f in file_list
                if config.os.path.isfile(config.os.path.join(folder, f)) and f.lower().endswith(config.info_txt_file)
            ]

            input_dates_channels = {}
            if len(fnames) == 1:
                with open(config.os.path.join(folder, fnames[0])) as f:
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
                if len(values) == 2:
                    window[idates].update(ivalues[0])
                    for ch in range(len(config.channel_list[:1])):
                        window[config.channel_list[ch] + str(i)].update(ivalues[ch + 1])
                if len(ivalues) == 1:
                    window[idates].update(ivalues[0])
                else:
                    continue

        elif event == submit_button:
            if values[input_dir] == "":
                sG.popup_error("Please choose a directory")
            if values[config.dapi_channel] == "":
                sG.popup_error("Please give at least channel 0")
            try:
                input_dates_channels_updated = {}
                for i in range(config.dates_number):
                    input_dates_channels_updated[values[config.input_dates + str(i)]] = [
                        values[config.channel_list[0] + str(i)],
                        values[config.channel_list[1] + str(i)],
                        values[config.channel_list[2] + str(i)]]
                rename_files_recursively(values[input_dir], config.dapi_channel, values[config.dapi_channel],
                                         input_dates_channels_updated)
            except:
                values[input_dir] = ""
                values[config.dapi_channel] = ""
                pass


if __name__ == "__main__":
    main()
