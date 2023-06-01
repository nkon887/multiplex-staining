# Importing necessary packages
import errno
import os
import shutil
import subprocess
import time
import tkinter as tk
from functools import partial
from tkinter import *
from tkinter import messagebox, filedialog

import pythontools as pt


# Defining App to
# create necessary tkinter widgets
class App:
    def __init__(self, master):
        # Creating tkinter variable
        self.sourceLocation = StringVar()
        self.destinationLocation = StringVar()
        self.patterns = StringVar()
        # Creating the loc variable
        self.base_dir = os.getcwd()
        self.left_frame = Frame(master, background="black")
        self.line = Frame(master, height=400, width=1, bg="grey80", relief='groove')
        self.right_frame = Frame(master, background="black")
        self.files_dir = ''
        self.create_conda_environment("multiplex", "env_multiplex.yml")
        self.button = Button(self.left_frame,
                             text="QUIT", fg="red",
                             command=self.left_frame.quit, width=30)
        self.button.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame, text="STITCHING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "STITCHING"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame,
                              text="IMAGE PREPARATION".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex",
                                                                        "image_preparation.py"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame,
                              text="ALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "ALIGNMENT"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame,
                              text="REALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [['fiji', "", "REALIGNMENT"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame,
                              text="CROPPING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "CROPPING AFTER ALIGNMENT"]]),
                              width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)

        self.process = Button(self.left_frame,
                              text="BACKGROUNDADJUSTMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "BACKGROUNDADJUSTMENT"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame,
                              text="MERGING CHANNELS".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "MERGING CHANNELS"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.create_conda_environment("cellsegsegmenter", "env_cellsegsegmenter.yml")
        self.process = Button(self.left_frame,
                              text="DapiSeg Segmentation".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex", "preparation_dapi_seg.py"
                                                                        ],
                                                                       ["python", "cellsegsegmenter", "dapi_seg_main.py"
                                                                        ],
                                                                       ["python", "multiplex",
                                                                        "postprocessing_dapi_seg.py"],
                                                                       ["fiji", "", "DAPISEG_RESIZER"]]), width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.process = Button(self.left_frame, text="Results Output".upper(), command=partial(self.run_shell_command,
                                                                                              [["python", "multiplex",
                                                                                                "results_output.py"]]),
                              width=30)
        self.process.pack(side=tk.TOP, pady=10, padx=20)
        self.main_input_Label = Label(self.right_frame, text="INPUT/OUTPUT ", bg="black", fg="white", width=20,
                                      height=1)
        self.main_input_Label.grid(row=0, column=2, pady=5, padx=5, columnspan=2)
        self.patterns_Label = Label(self.right_frame, text="Name Pattern Exceptions: ",
                                    bg="#E8D579", width=20, height=1)
        self.patterns_Label.grid(row=1, column=1, pady=5, padx=5)
        self.patterns_Text = Entry(self.right_frame, width=50, textvariable=self.patterns)
        self.patterns_Text.grid(row=1, column=2, pady=5, padx=5, columnspan=2)
        self.link_Label = Label(self.right_frame, text="Select The Dir To Copy: ", bg="#E8D579", width=20,
                                height=1)
        self.link_Label.grid(row=2, column=1, pady=5, padx=5)
        self.sourceText = Entry(self.right_frame, width=50, textvariable=self.sourceLocation)
        self.sourceText.grid(row=2, column=2, pady=5, padx=5, columnspan=2)
        self.source_browseButton = Button(self.right_frame, text="Browse",
                                          command=self.SourceBrowse, width=15)
        self.source_browseButton.grid(row=2, column=4, pady=5, padx=5)
        self.destinationLabel = Label(self.right_frame, text="Select The Destination: ", bg="#E8D579", width=20,
                                      height=1)
        self.destinationLabel.grid(row=3, column=1, pady=5, padx=5)
        self.destinationText = Entry(self.right_frame, width=50, textvariable=self.destinationLocation)
        self.destinationText.grid(row=3, column=2, pady=5, padx=5, columnspan=2)
        self.dest_browseButton = Button(self.right_frame, text="Browse",
                                        command=self.DestinationBrowse, width=15)
        self.dest_browseButton.grid(row=3, column=4, pady=5, padx=5)
        self.copyButton = Button(self.right_frame, text="Copy File(s)",
                                 command=self.CopyFile, width=15)
        self.copyButton.grid(row=4, column=2, pady=5, padx=5)
        self.moveButton = Button(self.right_frame, text="Move File(s)",
                                 command=self.MoveFile, width=15)
        self.moveButton.grid(row=4, column=3, pady=5, padx=5)
        self.left_frame.pack(side=tk.LEFT)
        self.line.pack(side=tk.LEFT, padx=10)
        self.right_frame.pack(side=tk.LEFT)

    def run_shell_command(self, parametersets):
        command = []
        for parameterset in parametersets:
            package, env, script = parameterset
            if package == "python" and env != "":
                command.append(f"conda activate {env} && {package} {script} && conda deactivate")
            elif package == "fiji":
                command.append(f"%FIJIPATH% --ij2 --run macro.py \"base_dir='{self.base_dir}' , step = '{script}'\"")
            else:
                "Not correct shell command. Please check it"
        if command:
            command_string = ' && '.join(command)
        subprocess.Popen(command_string, shell=True)

    def create_conda_environment(self, env_name, requirements_file):
        env_exists = False
        try:
            subprocess.run(f"conda activate {env_name}", shell=True, capture_output=True)
            env_exists = True
        except subprocess.CalledProcessError as e:
            pass
        if not env_exists:
            subprocess.Popen(f"conda env create -f {requirements_file}", shell=True)
            print(f"Conda environment {env_name} created.")
        else:
            print(f"Conda environment {env_name} already exists.")

    def SourceBrowse(self):
        # Opening the file-dialog directory prompting
        # the user to select files to copy using
        # filedialog.askopenfilenames() method. Setting
        # initialdir argument is optional Since multiple
        # files may be selected, converting the selection
        # to list using list()
        # self.files_list = list(
        #    filedialog.askopenfilenames(initialdir=os.path.join(base_dir, "workingDir")))

        self.files_dir = filedialog.askdirectory(initialdir=os.path.join(self.base_dir, "workingDir"))

        # Displaying the selected files in the root.sourceText
        self.sourceText.delete(0, tk.END)  # Remove current text in entry
        # Entry using root.sourceText.insert()
        self.sourceText.insert(0, self.files_dir)

    def DestinationBrowse(self):
        # Opening the file-dialog directory prompting
        # the user to select destination folder to
        # which files are to be copied using the
        # filedialog.askopendirectory() method
        # Setting initialdir argument is optional
        destinationdirectory = filedialog.askdirectory(
            initialdir=os.path.join(self.base_dir, "workingDir", "00_raw_input"))
        # Displaying the selected files in the root.sourceText
        self.destinationText.delete(0, tk.END)  # Remove current text in entry
        # Displaying the selected directory in the
        self.destinationText.insert(0, destinationdirectory)

    def CopyFile(self):
        # Retrieving the source file selected by the
        # user in the SourceBrowse() and storing it in a
        # variable named files_dir
        files_dir = self.files_dir
        patterns_list = self.patterns.get().split()
        # Retrieving the destination location from the
        # textvariable using destinationLocation.get() and
        # storing in destination_location
        destination_location = self.destinationLocation.get()
        # Copying the file to the destination using
        # the copy() of shutil module copy take the
        # source file and the destination folder as
        # the arguments
        try:
            # if path already exists, remove it before copying with copytree()
            if os.path.exists(destination_location):
                shutil.rmtree(destination_location)
                shutil.copytree(files_dir, destination_location, copy_function=shutil.copy2,
                                ignore=shutil.ignore_patterns(*patterns_list))
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(files_dir, destination_location)
            else:
                print('Directory not copied. Error: %s' % e)
        messagebox.showinfo("SUCCESSFUL")
        # Remove current text in entry
        self.sourceText.delete(0, tk.END)
        self.destinationText.delete(0, tk.END)

    def MoveFile(self):
        # Retrieving the source file selected by the
        # user in the SourceBrowse() and storing it in a
        # variable named files_list
        files_dir = self.files_dir
        patterns_list = self.patterns.get().split()
        # Retrieving the destination location from the
        # textvariable using destinationLocation.get() and
        # storing in destination_location
        destination_location = self.destinationLocation.get()

        # Looping through the files present in the list
        # Moving the file to the destination using
        # the move() of shutil module copy take the
        # source file and the destination folder as
        # the arguments
        for file in os.listdir(files_dir):
            if file not in patterns_list:
                try:
                    shutil.move(os.path.join(files_dir, file), os.path.join(destination_location, file))
                # If source and destination are same
                except shutil.SameFileError:
                    print("Source and destination represents the same file.")

                # If there is any permission issue
                except PermissionError:
                    print("Permission denied.")

                # For other errors
                except:
                    print("Error occurred while copying file.")
        messagebox.showinfo("SUCCESSFUL")
        # Remove current text in entry
        self.sourceText.delete(0, tk.END)
        self.destinationText.delete(0, tk.END)


def main():
    window = Tk()
    # Calling the App class function
    App(window)
    window.title("Running the Steps of Multiplex Pipeline")
    window.geometry('880x460')
    window.config(background="black")
    window.mainloop()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
