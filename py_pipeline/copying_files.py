import PySimpleGUI as sG
import pythontools as pt
import config


def main():
    font = ('Courier New', 11)
    source_dir = "-IN2-"
    submit_button = 'Submit'
    exit_button = 'Exit'
    cancel_button = 'Cancel'

    sG.set_options(font=font)
    layout = [
        [sG.T("")],
        [sG.Text("Choose a folder: "), sG.Input(key=source_dir, change_submits=True, enable_events=True),
         sG.FolderBrowse(key="-IN-")],
        [sG.T("")],
        [sG.Button(submit_button), sG.Button(cancel_button)]
    ]
    # Building Window
    window = sG.Window('My File Browser', layout, keep_on_top=True, element_justification='c')
    while True:
        event, values = window.read()
        if event == sG.WIN_CLOSED or event == exit_button or event == cancel_button:
            break
        elif event == submit_button:
            folder = values[source_dir]
            pt.parse_dir(folder, config.inputDir)


if __name__ == "__main__":
    main()
