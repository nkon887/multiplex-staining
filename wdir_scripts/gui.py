# gui.py

# Importing necessary packages
import errno
import itertools
import os
import re
import shutil
import subprocess
import tkinter as tk
from functools import partial
from tkinter import *
from tkinter import messagebox, filedialog
from tooltip import CreateToolTip

import helpertools as ht
from setup_logger import logger


# Defining App to create necessary tkinter widgets
class App:
    def __init__(self, master):
        # Creating tkinter variable
        self.base_dir = os.getcwd()
        self.sourceLocation = StringVar()
        self.destinationLocation = StringVar()
        self.patterns = StringVar()
        # Creating the loc variable
        self.left_frame = Frame(master, background="black")
        self.line = Frame(master, height=400, width=1, bg="grey80", relief='groove')
        self.right_frame = Frame(master, background="black")
        self.files_dir = ''
        self.destinationdirectory = ''
        self.initial_output_statement = "Please select input and output directories!"
        self.create_conda_environment("multiplex", "env_multiplex.yml")
        self.create_conda_environment("cellsegsegmenter", "env_cellsegsegmenter.yml")
        self.pipeline_params = {("STITCHING", "STITCHING", "imageCheck", "", "workingDir/01_input"): [
            {"package": "fiji", "env": "", "step": "STITCHING"}],
            ("IMAGE PREPARATION", "imageCheck", "ALIGNMENT", "workingDir/01_input", "workingDir/01_input"): [
                {"package": "python", "env": "multiplex", "step": "imageCheck"}],
            ("ALIGNMENT", "ALIGNMENT", "REALIGNMENT,CROPPING AFTER ALIGNMENT", "workingDir/01_input", "workingDir"
                                                                                                      "/02_01_input_to_precrop,workingDir/02_alignment"): [
                {"package": "fiji", "env": "", "step": "ALIGNMENT"
                 }],
            ("REALIGNMENT", "REALIGNMENT", "CROPPING  AFTER ALIGNMENT", "workingDir/02_01_input_to_precrop,"
                                                                        "workingDir/02_alignment",
             "workingDir/02_alignment"): [
                {"package": "fiji", "env": "", "step": "REALIGNMENT"}],
            ("CROPPING", "CROPPING AFTER ALIGNMENT", "BACKGROUNDADJUSTMENT", "workingDir/02_alignment", "workingDir"
                                                                                                        "/02_alignment"): [
                {"package": "fiji", "env": "", "step": "CROPPING AFTER ALIGNMENT"}],
            ("BACKGROUNDADJUSTMENT", "BACKGROUNDADJUSTMENT", "MERGING CHANNELS,DAPISEG RESIZER,resultsOutput",
             "workingDir/02_alignment",
             "workingDir/03_bg_processed"): [
                {"package": "fiji", "env": "", "step": "BACKGROUNDADJUSTMENT"}],
            (
                "MERGING CHANNELS", "MERGING CHANNELS", "", "workingDir/03_bg_processed",
                "workingDir/04_mergedChannels"): [
                {"package": "fiji", "env": "", "step": "MERGING CHANNELS"}],
            ("DAPI SEGMENTATION", "DAPISEG RESIZER", "", "workingDir/03_bg_processed", "workingDir"
                                                                                       "/05_dapi_seg"
                                                                                       "/04_binary_size_correct"): [
                {"package": "python", "env": "multiplex",
                 "step": "preparation_dapiSeg"},
                {"package": "python", "env": "cellsegsegmenter",
                 "step": "main_dapiSeg"},
                {"package": "python", "env": "multiplex",
                 "step": "postprocessing_dapiSeg"},
                {"package": "fiji", "env": "", "step": "DAPISEG_RESIZER"}],
            ("Results Output".upper(), "resultsOutput", "",
             "workingDir/03_bg_processed",
             "workingDir"
             "/06_results_output"): [
                {"package": "python", "env": "multiplex", "step": "resultsOutput"}]
        }
        self.buttons = {}
        for (pipeline_step, command_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            self.buttons[command_step, inputpaths] = Button(self.left_frame,
                                                            text=pipeline_step.upper(),
                                                            command=partial(
                                                                self.run_shell_command, [
                                                                    [self.pipeline_params[
                                                                         pipeline_step, command_step, next_steps, inputpaths, outputpaths][
                                                                         i][
                                                                         "package"],
                                                                     self.pipeline_params[
                                                                         pipeline_step, command_step, next_steps, inputpaths, outputpaths][
                                                                         i][
                                                                         "env"],
                                                                     self.pipeline_params[
                                                                         pipeline_step, command_step, next_steps, inputpaths, outputpaths][
                                                                         i][
                                                                         "step"]]
                                                                    for
                                                                    i in range(
                                                                        len(
                                                                            self.pipeline_params[
                                                                                pipeline_step, command_step, next_steps, inputpaths, outputpaths]))],
                                                                command_step, inputpaths),
                                                            width=30)
            self.orig_color_button = self.buttons[command_step, inputpaths].cget("background")
            self.buttons[command_step, inputpaths].config(state=tk.NORMAL)
            self.buttons[command_step, inputpaths].pack(side=tk.TOP, pady=10, padx=20)
            if self.sourceLocation.get() == "" and self.destinationLocation.get() == "":
                self.buttons[command_step, inputpaths].config(state=tk.DISABLED)
            else:
                self.buttons[command_step, inputpaths].config(state=tk.NORMAL)

        self.exit_button = Button(self.left_frame,
                                  text="QUIT", fg="red",
                                  command=self.left_frame.quit, width=30)
        self.exit_button.pack(side=tk.TOP, pady=10, padx=20)
        CreateToolTip(self.exit_button, "Click it to close the App Window")
        self.main_input_Label = Label(self.right_frame, text="INPUT/OUTPUT ", bg="black", fg="white", width=20,
                                      height=1)
        self.main_input_Label.grid(row=0, column=2, pady=5, padx=5, columnspan=2)
        # self.patterns_Label = Label(self.right_frame, text="Name Pattern Exceptions: ",
        #                            bg="#E8D579", width=20, height=1)
        # self.patterns_Label.grid(row=1, column=1, pady=5, padx=5)
        # self.patterns_Text = Entry(self.right_frame, width=50, textvariable=self.patterns)
        # self.patterns_Text.grid(row=1, column=2, pady=5, padx=5, columnspan=2)
        self.link_Label = Label(self.right_frame, text="Select The Source: ", bg="#E8D579", width=20,
                                height=1)
        self.link_Label.grid(row=2, column=1, pady=5, padx=5)
        self.sourceText = Entry(self.right_frame, width=50, textvariable=self.sourceLocation)
        self.sourceText.grid(row=2, column=2, pady=5, padx=5, columnspan=2)
        self.source_browseButton = Button(self.right_frame, text="Browse",
                                          command=self.source_browse, width=15)
        self.source_browseButton.grid(row=2, column=4, pady=5, padx=5)
        self.destinationLabel = Label(self.right_frame, text="Select The Destination: ", bg="#E8D579", width=20,
                                      height=1)
        self.destinationLabel.grid(row=3, column=1, pady=5, padx=5)
        self.destinationText = Entry(self.right_frame, width=50, textvariable=self.destinationLocation)
        self.destinationText.grid(row=3, column=2, pady=5, padx=5, columnspan=2)
        self.dest_browseButton = Button(self.right_frame, text="Browse",
                                        command=self.destination_browse, width=15)
        self.dest_browseButton.grid(row=3, column=4, pady=5, padx=5)
        self.output_box = tk.Text(self.right_frame, width=70, height=10)
        self.output_box.grid(row=6, column=0, columnspan=5, pady=15, padx=5)
        self.output_box.insert("end-1c", self.initial_output_statement)
        # self.copyButton = Button(self.right_frame, text="Copy File(s)",
        #                         command=self.copy_file, width=15)
        # self.copyButton.grid(row=4, column=2, pady=5, padx=5)
        # self.moveButton = Button(self.right_frame, text="Move File(s)",
        #                         command=self.move_file, width=15)
        # self.moveButton.grid(row=4, column=3, pady=5, padx=5)
        self.left_frame.pack(side=tk.LEFT)
        self.line.pack(side=tk.LEFT, padx=10)
        self.right_frame.pack(side=tk.LEFT)

    def run_shell_command(self, parametersets, command_step, inputpaths):
        self.buttons[command_step, inputpaths].config(bg='yellow')
        # self.output_box.insert("end-1c", "\nRunning the step...")
        command = []
        command_string = ''
        destination = self.destinationLocation.get()
        for parameterset in parametersets:
            package, env, step = parameterset
            if package == "python" and env != "":
                command.append(f"conda activate {env} && {package} main.py {destination} {step}  && "
                               f"conda deactivate")
            elif package == "fiji":
                command.append(
                    f"%FIJIPATH% --ij2 --run macro.py \"base_dir='{self.sourceLocation.get()}' , target_dir = '"
                    f"{destination}' , step = '{step}'\"")

            else:
                "Not correct shell command. Please check it"
        if command:
            command_string = ' && '.join(command)
        p = subprocess.Popen(command_string, shell=True)
        """
        A None value indicates that the process hasn't terminated yet.
        """
        p.wait()
        for parameterset in parametersets:
            package, env, step = parameterset
            self.switch(step)

    def create_conda_environment(self, env_name, requirements_file):
        env_exists = False
        try:
            subprocess.run(f"conda activate {env_name}", shell=True, check=True)
            env_exists = True
        except subprocess.CalledProcessError as e:
            pass
        if not env_exists:
            subprocess.run(f"conda env create -f {requirements_file}", shell=True)
            logger.info(f"Conda environment {env_name} created.")
        else:
            logger.info(f"{env_exists} Conda environment {env_name} already exists.")

    def source_browse(self):
        # Opening the file-dialog directory prompting the user to select files to copy using
        # filedialog.askopenfilenames() method. Setting initialdir argument is optional Since multiple
        # files may be selected, converting the selection to list using list()

        self.files_dir = filedialog.askdirectory(initialdir=self.base_dir)

        # Displaying the selected files in the root.sourceText
        self.sourceText.delete(0, tk.END)  # Remove current text in entry
        # Entry using root.sourceText.insert()
        self.sourceText.insert(0, self.files_dir)
        self.switch_on_buttons()

    def switch_on_buttons(self):
        if self.sourceLocation.get() != "" and self.destinationLocation.get() != "":
            for command_step, inputpaths in self.buttons:
                self.buttons[command_step, inputpaths].config(bg=self.orig_color_button)
                if command_step == "STITCHING":
                    self.buttons[command_step, inputpaths].config(state=tk.NORMAL)
                    CreateToolTip(self.buttons[command_step, inputpaths], "Pipeline Start Step")
                else:
                    current_inputpaths = [ht.correct_path(self.destinationLocation.get(), path) for path in
                                          inputpaths.split(",")]
                    if command_step == "BACKGROUNDADJUSTMENT":
                        pattern = re.compile(r'.*_Cropped\.tif')
                        if all([os.path.exists(inputpath) for inputpath in current_inputpaths]):
                            for inputpath in current_inputpaths:
                                if os.listdir(inputpath):

                                    if not any([pattern.match(filepath) for filepath in os.listdir(inputpath)]):
                                        self.buttons[command_step, inputpaths].config(state=tk.DISABLED)
                                    else:
                                        self.buttons[command_step, inputpaths].config(state=tk.NORMAL)
                        if not all([os.path.exists(inputpath) for inputpath in current_inputpaths]):
                            self.buttons[command_step, inputpaths].config(state=tk.DISABLED)
                    else:
                        if not all([os.path.exists(inputpath) for inputpath in current_inputpaths]):
                            self.buttons[command_step, inputpaths].config(state=tk.DISABLED)
                        else:
                            self.buttons[command_step, inputpaths].config(state=tk.NORMAL)
            if all([str(self.buttons[(step, inputpaths)]['state']) == tk.DISABLED for step, inputpaths in self.buttons
                    if step != "STITCHING"]):
                self.output_box.delete(1.0, "end-1c")  # Clears the text box of data
                self.output_box.insert("end-1c", f"Please start with STITCHING")
            else:
                self.output_box.delete(1.0, "end-1c")  # Clears the text box of data
                self.output_box.insert("end-1c", f"Start with any enabled step")
        else:
            self.output_box.delete(1.0, "end-1c")  # Clears the text box of data
            self.output_box.insert("end-1c", self.initial_output_statement)
            for command_step, inputpaths in self.buttons:
                self.buttons[command_step, inputpaths].config(state=tk.DISABLED)
                self.buttons[command_step, inputpaths].config(bg=self.orig_color_button)

    def destination_browse(self):
        # Opening the file-dialog directory prompting the user to select destination folder to
        # which files are to be copied using the filedialog.askopendirectory() method
        # Setting initialdir argument is optional
        self.destinationdirectory = filedialog.askdirectory(
            initialdir=self.base_dir)
        # Displaying the selected files in the root.sourceText
        self.destinationText.delete(0, tk.END)  # Remove current text in entry
        # Displaying the selected directory in the
        self.destinationText.insert(0, self.destinationdirectory)
        self.switch_on_buttons()

    def copy_file(self):
        # Retrieving the source file selected by the user in the SourceBrowse() and storing it in a
        # variable named files_dir
        files_dir = self.files_dir
        patterns_list = self.patterns.get().split()
        # Retrieving the destination location from the textvariable using destinationLocation.get() and
        # storing in destination_location
        destination_location = self.destinationLocation.get()
        # Copying the file to the destination using the copy() of shutil module copy take the
        # source file and the destination folder as the arguments
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
                logger.error('Directory not copied. Error: %s' % e)
        messagebox.showinfo("SUCCESSFUL")
        # Remove current text in entry
        self.sourceText.delete(0, tk.END)
        self.destinationText.delete(0, tk.END)

    def move_file(self):
        # Retrieving the source file selected by the user in the SourceBrowse() and storing it in a
        # variable named files_list
        files_dir = self.files_dir
        patterns_list = self.patterns.get().split()
        # Retrieving the destination location from the textvariable using destinationLocation.get() and
        # storing in destination_location
        destination_location = self.destinationLocation.get()

        # Looping through the files present in the list. Moving the file to the destination using
        # the move() of shutil module copy take the source file and the destination folder as the arguments
        for file in os.listdir(files_dir):
            if file not in patterns_list:
                try:
                    shutil.move(ht.correct_path(files_dir, file), ht.correct_path(destination_location, file))
                # If source and destination are same
                except shutil.SameFileError:
                    logger.error("Source and destination represents the same file.")

                # If there is any permission issue
                except PermissionError:
                    logger.error("Permission denied.")

                # For other errors
                except:
                    logger.error("Error occurred while copying file.")
        messagebox.showinfo("SUCCESSFUL")
        # Remove current text in entry
        self.sourceText.delete(0, tk.END)
        self.destinationText.delete(0, tk.END)

    def match_string(self, _list_, inputpath):

        inputpaths = inputpath.split(",")
        found_current_inputpaths = []
        for path in inputpaths:
            for _string_ in _list_:
                findid = [re.search(path, _string_)]
                for f in findid:
                    if f is not None:
                        found_current_inputpaths.append(f.string)
        return ",".join(list(set(found_current_inputpaths)))

    def switch(self, step):
        current_next_steps = []
        current_outputpaths = []
        for (pipeline_step, command_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step == command_step:
                current_next_steps = current_next_steps + next_steps.split(",")
                current_outputpaths = [ht.correct_path(self.destinationLocation.get(), path) for path in
                                       outputpaths.split(",")]
        for (pipeline_step, command_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step == command_step:
                for switch_next_step in current_next_steps:
                    if switch_next_step != '':

                        switch_inputpath = self.match_string(outputpaths.split(","),
                                                             [k[1] for k, v in self.buttons.items() if
                                                              k[0] == switch_next_step][0])
                        check = self.match_string(current_outputpaths, switch_inputpath)
                        # if any([os.path.exists(inputpath) for inputpath in current_outputpaths]):
                        if check:
                            for switch_inputpath_ in list(
                                    map(",".join, itertools.permutations(switch_inputpath.split(",")))):
                                if (switch_next_step, switch_inputpath_) in self.buttons:
                                    self.buttons[switch_next_step, switch_inputpath_].config(
                                        state=tk.NORMAL)
                                    # self.output_box.delete(1.0, "end-1c")  # Clears the text box of data
                                    pipe_step = \
                                        [k[0] for k, v in self.pipeline_params.items() if k[1] == switch_next_step][
                                            0]
                                    self.output_box.insert("end-1c", f"\nThe  next step {pipe_step} can be done. The "
                                                                     f"input is in {switch_inputpath} in your "
                                                                     f"destination "
                                                                     f"folder")  # adds text
                                    # to text box
                        else:
                            if (switch_next_step, switch_inputpath) in self.buttons:
                                self.buttons[switch_next_step, switch_inputpath].config(state=tk.DISABLED)
                                # self.output_box.delete(1.0, "end-1c")
                                self.output_box.insert("end-1c", f"\nThe  next step {pipe_step} cannot be done as "
                                                                 f"there is no input in {switch_inputpath} for it in "
                                                                 f"your destination folder")
