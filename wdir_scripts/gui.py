# Importing necessary packages
import shutil
import subprocess
from functools import partial
import tkinter
from tkinter import *
from tkinter import messagebox, filedialog
import os


# import imagej

# ij = imagej.init("C:/Fiji/fiji-win64/Fiji.app")
# print(ij.getVersion())
# macro = """
# text= "Hello World";
# print(text);
# """
# result = ij.py_run_macro(macro)
# print(result)

# Defining App to
# create necessary tkinter widgets
class App:
    def __init__(self, master):
        self.files_list = []
        frame = Frame(master, background="black")
        frame.grid(column=0, row=1, rowspan=9)

        self.button = Button(frame,
                             text="QUIT", fg="red",
                             command=frame.quit, width=30)
        self.button.grid(row=1, column=0, pady=10, padx=20)
        self.create_conda_environment("multiplex", "env_multiplex.yml")
        self.link_Label = Label(frame, text="Select The File(s) To Copy : ", bg="#E8D579")
        self.link_Label.grid(row=1, column=1, pady=5, padx=5)

        self.sourceText = Entry(frame, width=50, textvariable=sourceLocation)
        self.sourceText.grid(row=1, column=2, pady=5, padx=5, columnspan=2)

        self.source_browseButton = Button(frame, text="Browse", command=partial(self.SourceBrowse, frame), width=15)
        self.source_browseButton.grid(row=1, column=4, pady=5, padx=5)

        self.destinationLabel = Label(frame, text="Select The Destination : ", bg="#E8D579")
        self.destinationLabel.grid(row=2, column=1, pady=5, padx=5)

        self.destinationText = Entry(frame, width=50, textvariable=destinationLocation)
        self.destinationText.grid(row=2, column=2, pady=5, padx=5, columnspan=2)

        self.dest_browseButton = Button(frame, text="Browse", command=partial(self.DestinationBrowse, frame), width=15)
        self.dest_browseButton.grid(row=2, column=4, pady=5, padx=5)

        self.copyButton = Button(frame, text="Copy File(s)", command=partial(self.CopyFile, frame), width=15)
        self.copyButton.grid(row=3, column=2, pady=5, padx=5)

        self.moveButton = Button(frame, text="Move File(s)", command=partial(self.MoveFile, frame), width=15)
        self.moveButton.grid(row=3, column=3, pady=5, padx=5)

        self.process = Button(frame, text="STITCHING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "STITCHING"]]), width=30)
        self.process.grid(row=2, column=0, pady=10, padx=20)
        self.process = Button(frame,
                              text="IMAGE PREPARATION".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex",
                                                                        "image_preparation.py"]]), width=30)
        self.process.grid(row=3, column=0, pady=10, padx=20)
        self.process = Button(frame,
                              text="ALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "ALIGNMENT"]]), width=30)
        self.process.grid(row=4, column=0, pady=10, padx=20)
        self.process = Button(frame,
                              text="REALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [['fiji', "", "REALIGNMENT"]]), width=30)
        self.process.grid(row=5, column=0, pady=10, padx=20)
        self.process = Button(frame,
                              text="CROPPING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "CROPPING AFTER ALIGNMENT"]]),
                              width=30)
        self.process.grid(row=6, column=0, pady=10, padx=20)

        self.process = Button(frame,
                              text="BACKGROUNDADJUSTMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "BACKGROUNDADJUSTMENT"]]), width=30)
        self.process.grid(row=7, column=0, pady=10, padx=20)
        self.process = Button(frame,
                              text="MERGING CHANNELS".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "MERGING CHANNELS"]]), width=30)
        self.process.grid(row=8, column=0, pady=10, padx=20)
        self.create_conda_environment("cellsegsegmenter", "env_cellsegsegmenter.yml")
        self.process = Button(frame,
                              text="DapiSeg Segmentation".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex", "preparation_dapi_seg"
                                                                                               ".py"],
                                                                       ["python", "cellsegsegmenter", "dapi_seg_main"
                                                                                                      ".py"],
                                                                       ["python", "multiplex",
                                                                        "postprocessing_dapi_seg"
                                                                        ".py"], ["fiji", '', "DAPISEG_RESIZER"]]),
                              width=30)
        self.process.grid(row=9, column=0, pady=10, padx=20)

    def run_shell_command(self, parametersets):
        for parameterset in parametersets:
            package, env, command = parameterset
            if package == "python" and env != '':
                subprocess.run('conda activate ' + env + ' && ' + package + ' ' + command + ' && conda deactivate',
                               shell=True, check=True)
            elif package == "fiji":
                base_dir = os.getcwd()
                subprocess.Popen(
                    "%FIJIPATH% --ij2 --run macro.py \"base_dir='" + base_dir + "' , step = '" + command + "'\"",
                    shell=True,
                    stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            else:
                "Not correct shell command. Please check it"

    def create_conda_environment(self, env_name, requirements_file):
        env_exists = False
        try:
            subprocess.run(f"conda activate {env_name}", shell=True, check=True)
            env_exists = True
        except subprocess.CalledProcessError as e:
            pass

        if not env_exists:
            subprocess.run(f"conda env create -f {requirements_file}", shell=True)
            print(f"Conda environment {env_name} created.")
        else:
            print(f"Conda environment {env_name} already exists.")

    def SourceBrowse(self, frame):
        # Opening the file-dialog directory prompting
        # the user to select files to copy using
        # filedialog.askopenfilenames() method. Setting
        # initialdir argument is optional Since multiple
        # files may be selected, converting the selection
        # to list using list()
        self.files_list = list(
            filedialog.askopenfilenames(initialdir="dir:/"))

        # Displaying the selected files in the root.sourceText
        # Entry using root.sourceText.insert()
        self.sourceText.insert('1', self.files_list)

    def DestinationBrowse(self, frame):
        # Opening the file-dialog directory prompting
        # the user to select destination folder to
        # which files are to be copied using the
        # filedialog.askopendirectory() method.
        # Setting initialdir argument is optional
        destinationdirectory = filedialog.askdirectory(
            initialdir="dir:/")
        # Displaying the selected directory in the
        # root.destinationText Entry using
        # root.destinationText.insert()
        self.destinationText.insert('1', destinationdirectory)

    def CopyFile(self, frame):
        # Retrieving the source file selected by the
        # user in the SourceBrowse() and storing it in a
        # variable named files_list
        files_list = self.files_list

        # Retrieving the destination location from the
        # textvariable using destinationLocation.get() and
        # storing in destination_location
        destination_location = destinationLocation.get()

        # Looping through the files present in the list
        for f in files_list:
            # Copying the file to the destination using
            # the copy() of shutil module copy take the
            # source file and the destination folder as
            # the arguments
            shutil.copy(f, destination_location)

        messagebox.showinfo("SUCCESSFUL")

    def MoveFile(self, frame):
        # Retrieving the source file selected by the
        # user in the SourceBrowse() and storing it in a
        # variable named files_list'''
        files_list = self.files_list

        # Retrieving the destination location from the
        # textvariable using destinationLocation.get() and
        # storing in destination_location
        destination_location = destinationLocation.get()

        # Looping through the files present in the list
        for f in files_list:
            # Moving the file to the destination using
            # the move() of shutil module copy take the
            # source file and the destination folder as
            # the arguments
            shutil.move(f, destination_location)

        messagebox.showinfo("SUCCESSFUL")


window = Tk()
# Creating tkinter variable
sourceLocation = StringVar()
destinationLocation = StringVar()
# Calling the App class function
app = App(window)
window.title("Running the Steps of Multiplex Pipeline")
window.geometry('870x450')
window.config(background="black")
window.mainloop()
