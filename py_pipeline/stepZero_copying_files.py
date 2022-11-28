import os
import time

import PySimpleGUI as sG

import config
import pythontools as pt


def main():
    font = ('Courier New', 11)
    source_dir = "-IN2-"
    submit_button = 'Submit'
    cancel_button = 'Cancel'

    sG.set_options(font=font)
    layout = [
        [sG.T("")],
        [sG.Text("Choose a folder with the stitched files you want to process: "),
         sG.Input(config.baseDir, key=source_dir, change_submits=True, enable_events=True),
         sG.FolderBrowse(key="-IN-")],
        [sG.T("")],
        [sG.Button(submit_button), sG.Button(cancel_button)]
    ]
    # Building Window
    window = sG.Window('My File Browser', layout, keep_on_top=True, element_justification='c', finalize=True,
                       enable_close_attempted_event=True)
    while True:
        event, values = window.read()
        if event in (sG.WINDOW_CLOSE_ATTEMPTED_EVENT, sG.WIN_CLOSED, cancel_button, 'Exit', '-ESCAPE-'):
            event, values = sG.Window('Yes/No?', [[sG.Text('Do you really want cancel/exit?')],
                                                  [sG.Button('Yes'), sG.Button('No')]],
                                      modal=True, element_justification='c', keep_on_top=True).read(close=True)
            if event == 'Yes':
                break

        elif event == submit_button:
            src = values[source_dir]
            des = config.inputDir
            for dir_path, dir_names, file_names in os.walk(src):
                for file_name in (sorted(file_names)):
                    target_dir = dir_path.replace(src, des, 1).replace("\\", "/")
                    if not os.path.exists(target_dir):
                        os.mkdir(target_dir)
                    src_file = os.path.join(dir_path, file_name).replace("\\", "/")
                    dest_file = os.path.join(target_dir, file_name).replace("\\", "/")
                    pt.copy_with_progress(src_file, dest_file)

            event, values = sG.Window('Output', [[sG.Text('Successfully copied. Do you want to copy from the '
                                                          'other source?')], [sG.Button('Yes'), sG.Button('No')]],
                                      modal=True, element_justification='c', keep_on_top=True).read(close=True)
            if event == 'No':
                break


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("Duration of the program execution:", )
    print(end_time - start_time)
