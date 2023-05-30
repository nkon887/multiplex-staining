# Importing necessary packages
import os
import shutil
import subprocess
from functools import partial
import tkinter as tk
from tkinter import *
from tkinter import messagebox, filedialog

# Defining App to
# create necessary tkinter widgets
class App:
    def __init__(self, master):
        self.files_list = []
        left_frame = Frame(master, background="black")
        right_frame = Frame(master, background="black")
        line = Frame(master, height=400, width=1, bg="grey80", relief='groove')
        self.button = Button(left_frame,
                             text="QUIT", fg="red",
                             command=left_frame.quit, width=30)
        self.button.pack(side=tk.TOP, pady=10, padx=20)
        self.create_conda_environment("multiplex", "env_multiplex.yml")
        self.main_input_Label = Label(right_frame, text="INPUT/OUTPUT ", bg="black", fg="white", width=20, height=1)
        self.main_input_Label.grid(row=0, column=2, pady=5, padx=5, columnspan=2)

        self.link_Label = Label(right_frame, text="Select The File(s) To Copy : ", bg="#E8D579", width=20,
                                height=1)
        self.link_Label.grid(row=1, column=1, pady=5, padx=5)
        self.sourceText = Entry(right_frame, width=50, textvariable=sourceLocation)
        self.sourceText.grid(row=1, column=2, pady=5, padx=5, columnspan=2)
        self.source_browseButton = Button(right_frame, text="Browse",
                                          command=partial(self.SourceBrowse, right_frame), width=15)
        self.source_browseButton.grid(row=1, column=4, pady=5, padx=5)

        self.destinationLabel = Label(right_frame, text="Select The Destination : ", bg="#E8D579", width=20,
                                      height=1)
        self.destinationLabel.grid(row=2, column=1, pady=5, padx=5)
        self.destinationText = Entry(right_frame, width=50, textvariable=destinationLocation)
        self.destinationText.grid(row=2, column=2, pady=5, padx=5, columnspan=2)
        self.dest_browseButton = Button(right_frame, text="Browse",
                                        command=partial(self.DestinationBrowse, right_frame), width=15)
        self.dest_browseButton.grid(row=2, column=4, pady=5, padx=5)
        self.copyButton = Button(right_frame, text="Copy File(s)",
                                 command=partial(self.CopyFile, right_frame), width=15)
        self.copyButton.grid(row=3, column=2, pady=5, padx=5)
        self.moveButton = Button(right_frame, text="Move File(s)",
                                 command=partial(self.MoveFile, right_frame), width=15)
        self.moveButton.grid(row=3, column=3, pady=5, padx=5)

        self.process = Button(left_frame, text="STITCHING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "STITCHING"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(left_frame,
                              text="IMAGE PREPARATION".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex",
                                                                        "image_preparation.py"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(left_frame,
                              text="ALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "ALIGNMENT"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(left_frame,
                              text="REALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [['fiji', "", "REALIGNMENT"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(left_frame,
                              text="CROPPING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "CROPPING AFTER ALIGNMENT"]]),
                              width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)

        self.process = Button(left_frame,
                              text="BACKGROUNDADJUSTMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "BACKGROUNDADJUSTMENT"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(left_frame,
                              text="MERGING CHANNELS".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "MERGING CHANNELS"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.create_conda_environment("cellsegsegmenter", "env_cellsegsegmenter.yml")
        self.process = Button(left_frame,
                              text="DapiSeg Segmentation".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex", "preparation_dapi_seg"
                                                                                               ".py"],
                                                                       ["python", "cellsegsegmenter", "dapi_seg_main"
                                                                                                      ".py"],
                                                                       ["python", "multiplex",
                                                                        "postprocessing_dapi_seg"
                                                                        ".py"], ["fiji", '', "DAPISEG_RESIZER"]]),
                              width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        left_frame.pack(side=tk.LEFT)
        line.pack(side=tk.LEFT, padx=10)
        right_frame.pack(side=tk.LEFT)

    def run_shell_command(self, parametersets):
        for parameterset in parametersets:
            package, env, command = parameterset
            if package == "python" and env != '':
                subprocess.run('conda activate ' + env + ' && ' + package + ' ' + command + ' && conda deactivate',
                               shell=True, check=True)
            elif package == "fiji":
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
            filedialog.askopenfilenames(initialdir=os.path.join(base_dir, "workingDir")))

        # Displaying the selected files in the root.sourceText
        self.sourceText.delete(0, tk.END)  # Remove current text in entry
        # Entry using root.sourceText.insert()
        self.sourceText.insert(0, self.files_list)

    def DestinationBrowse(self, frame):
        # Opening the file-dialog directory prompting
        # the user to select destination folder to
        # which files are to be copied using the
        # filedialog.askopendirectory() method.
        # Setting initialdir argument is optional
        destinationdirectory = filedialog.askdirectory(
            initialdir=os.path.join(base_dir, "workingDir"))
        # Displaying the selected directory in the
        # root.destinationText Entry using
        # root.destinationText.insert()
        self.destinationText.insert(0, destinationdirectory)

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
        # Remove current text in entry
        self.sourceText.delete(0, tk.END)
        self.destinationText.delete(0, tk.END)

    def MoveFile(self, frame):
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
            # Moving the file to the destination using
            # the move() of shutil module copy take the
            # source file and the destination folder as
            # the arguments
            shutil.move(f, destination_location)

        messagebox.showinfo("SUCCESSFUL")
        # Remove current text in entry
        self.sourceText.delete(0, tk.END)
        self.destinationText.delete(0, tk.END)


window = Tk()
# Creating tkinter variable
sourceLocation = StringVar()
destinationLocation = StringVar()
# Creating global variable
base_dir = os.getcwd()
# Calling the App class function
app = App(window)
window.title("Running the Steps of Multiplex Pipeline")
window.geometry('880x450')
window.config(background="black")
window.mainloop()
