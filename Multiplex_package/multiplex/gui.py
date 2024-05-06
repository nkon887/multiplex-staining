# multiplex.gui.py

# Importing necessary packages
import errno
import itertools
import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from functools import partial
from tkinter import *
from tkinter import messagebox, filedialog

import multiplex.helpertools as ht
from multiplex.screentip import CreateScreenTip
from multiplex.setup_logger import logger


# Defining App to create necessary tkinter widgets
class App:
    def __init__(self, master, pipeline_params, dapiseg_steps, merge_channels_steps, cropping_experimental_steps,
                 subfolders_list,
                 realignment_subfolder_list,
                 dapiseg_subfolder_list, command_arguments, packages, envs, main_work_dir, main_py_PATH,
                 macro_py_PATH):
        # Creating tkinter variable
        self.base_dir = os.getcwd()
        self.sourceLocation = StringVar()
        self.destinationLocation = StringVar()
        self.varGPU = IntVar()
        self.patterns = StringVar()
        # Creating the loc variable
        self.left_frame = Frame(master, background="black")
        self.line = Frame(master, height=400, width=1, bg="grey80", relief='groove')
        self.right_frame = Frame(master, background="black")
        self.files_dir = ''
        self.destinationdirectory = ''
        self.initial_output_statement = "Please select input and output directories and toggle if you use GPU (" \
                                        "otherwise CPU will be used)! "
        self.pipeline_params = pipeline_params
        self.dapiseg_steps = dapiseg_steps
        self.merge_channels_steps = merge_channels_steps
        self.cropping_experimental_steps = cropping_experimental_steps
        self.subfolder_list = subfolders_list
        self.realignment_subfolder_list = realignment_subfolder_list
        self.dapiseg_subfolder_list = dapiseg_subfolder_list
        self.packages = packages
        self.main_work_dir = main_work_dir
        self.main_py_PATH = main_py_PATH
        self.macro_py_PATH = macro_py_PATH
        self.buttons = {}
        self.envs = envs
        self.env_to_exclude = list(self.envs)[2]
        self.command_arguments = command_arguments
        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            self.buttons[pipeline_step, inputpaths] = Button(self.left_frame,
                                                             text=pipeline_step.upper(),
                                                             command=partial(self.processingPleaseWait_, master,
                                                                             pipeline_step,
                                                                             partial(self.run_shell_command, [
                                                                                 [self.pipeline_params[
                                                                                      pipeline_step, next_steps, inputpaths, outputpaths][
                                                                                      i][
                                                                                      self.command_arguments[0]],
                                                                                  self.pipeline_params[
                                                                                      pipeline_step, next_steps, inputpaths, outputpaths][
                                                                                      i][
                                                                                      self.command_arguments[1]],
                                                                                  self.pipeline_params[
                                                                                      pipeline_step, next_steps, inputpaths, outputpaths][
                                                                                      i][
                                                                                      self.command_arguments[2]]] for
                                                                                 i in range(
                                                                                     len(
                                                                                         self.pipeline_params[
                                                                                             pipeline_step, next_steps, inputpaths, outputpaths]))],
                                                                                     pipeline_step, inputpaths))
                                                             ,
                                                             width=30)
            self.orig_color_button = self.buttons[pipeline_step, inputpaths].cget("background")
            self.buttons[pipeline_step, inputpaths].config(state=tk.NORMAL)
            self.buttons[pipeline_step, inputpaths].pack(side=tk.TOP, pady=10, padx=20)
            if self.sourceLocation.get() == "" and self.destinationLocation.get() == "":
                self.buttons[pipeline_step, inputpaths].config(state=tk.DISABLED)
            else:
                self.buttons[pipeline_step, inputpaths].config(state=tk.NORMAL)
        self.exit_button = Button(self.left_frame,
                                  text="QUIT", fg="red",
                                  command=threading.Thread(target=self.left_frame.quit).start, width=30)
        self.exit_button.pack(side=tk.TOP, pady=10, padx=20)
        CreateScreenTip(self.exit_button, "Click it to close the App Window")
        self.main_input_Label = Label(self.right_frame, text="INPUT/OUTPUT ", bg="black", fg="white", width=20,
                                      height=1)
        self.main_input_Label.grid(row=0, column=2, pady=5, padx=5, columnspan=2)

        # self.patterns_Label = Label(self.right_frame, text="Name Pattern Exceptions: ",
        #                            bg="#E8D579", width=20, height=1)
        # self.patterns_Label.grid(row=1, column=1, pady=5, padx=5)
        # self.patterns_Text = Entry(self.right_frame, width=50, textvariable=self.patterns)
        # self.patterns_Text.grid(row=1, column=2, pady=5, padx=5, columnspan=2)

        # Define a Checkbox
        self.GPU_Toggle = Checkbutton(self.right_frame, text="GPU", bg="#E8D579", variable=self.varGPU, onvalue=1,
                                      offvalue=0)
        self.GPU_Toggle.grid(row=1, column=1, pady=5, padx=5)
        CreateScreenTip(self.GPU_Toggle, "Please toggle it if you have GPU on your PC")
        self.link_Label = Label(self.right_frame, text="Select The Source: ", bg="#E8D579", width=20,
                                height=1)
        self.link_Label.grid(row=2, column=1, pady=5, padx=5)
        self.sourceText = Entry(self.right_frame, width=50, textvariable=self.sourceLocation)
        self.sourceText.grid(row=2, column=2, pady=5, padx=5, columnspan=2)
        self.source_browseButton = Button(self.right_frame, text="Browse",
                                          command=self.source_browse, width=15)
        self.source_browseButton.grid(row=2, column=4, pady=5, padx=5)
        CreateScreenTip(self.source_browseButton, "Please click here to select the input directory")
        self.destinationLabel = Label(self.right_frame, text="Select The Destination: ", bg="#E8D579", width=20,
                                      height=1)
        self.destinationLabel.grid(row=3, column=1, pady=5, padx=5)
        self.destinationText = Entry(self.right_frame, width=50, textvariable=self.destinationLocation)
        self.destinationText.grid(row=3, column=2, pady=5, padx=5, columnspan=2)
        self.dest_browseButton = Button(self.right_frame, text="Browse",
                                        command=self.destination_browse, width=15)
        self.dest_browseButton.grid(row=3, column=4, pady=5, padx=5)
        CreateScreenTip(self.dest_browseButton, "Please click here to select the target directory")
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

    # Define Function to get the input value of varGPU
    def get_gpu_input(self):
        gpu_value = self.varGPU.get()
        logger.info("GPU selection " + str(gpu_value))

    #        if gpu_value != 0:
    #            self.env_to_exclude = list(self.envs)[3]
    #        import gdown
    #        for key in self.envs:
    #            if key not in ["", self.env_to_exclude] and not os.path.exists(list(self.envs[key])[0]):
    #                logger.info(list(self.envs[key])[1])
    #                logger.info(list(self.envs[key])[0])
    #                gdown.download(list(self.envs[key])[1], list(self.envs[key])[0], quiet=False)
    #        for key in self.envs:
    #            if key not in ["", self.env_to_exclude]:
    #                self.create_conda_environment(key, list(self.envs[key])[0])
    def processingPleaseWait(self, pipeline_step, function):
        import tkinter, time, threading
        window_of_process = tkinter.Toplevel()  # or tkinter.Tk()
        # code before computation starts
        window_of_process.title("Running the step " + pipeline_step)
        window_of_process.geometry('500x100')
        window_of_process['bg'] = 'yellow'
        label = tkinter.Label(window_of_process, text="Waiting ...")
        label.pack()
        done = []

        def call():
            result = function()
            done.append(result)

        thread = threading.Thread(target=call)
        thread.start()  # start parallel computation
        while thread.is_alive():
            # code while compution
            window_of_process.update()
            time.sleep(0.001)
            # code when computation is done
        label['text'] = str(done)
        window_of_process['bg'] = 'green'

    def processingPleaseWait_(self, master, step, function):
        import tkinter, time, threading
        window_of_process = master
        # code before computation starts
        window_of_process.title("Running the step " + step)
        # window_of_process.geometry('500x100')
        # window_of_process['bg'] = 'yellow'
        # = tkinter.Label(window_of_process, text="Waiting ...")
        # label.pack()
        self.output_box.insert("end-1c", f"\nWaiting ...")
        done = []

        def call():
            result = function()
            done.append(result)

        thread = threading.Thread(target=call)
        thread.start()  # start parallel computation
        while thread.is_alive():
            # code while compution
            window_of_process.update()
            time.sleep(0.001)
            # code when computation is done
        # label['text'] = str(done)
        self.output_box.insert("end-1c", "\n" + str(done))
        # window_of_process['bg'] = 'green'
        current_next_steps = []
        current_outputpaths = []
        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step == pipeline_step:
                current_next_steps = current_next_steps + next_steps.split(",")
                current_outputpaths = [ht.correct_path(self.destinationLocation.get(), path) for path in
                                       outputpaths.split(",")]
        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step == pipeline_step:
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
                                        [k[0] for k, v in self.pipeline_params.items() if k[0] == switch_next_step][0]
                                    self.output_box.insert("end-1c", f"\nThe  next step {pipe_step} can be done. The "
                                                                     f"input is in {switch_inputpath} in your "
                                                                     f"destination "
                                                                     f"folder")  # adds text
                                    # to text box
                        else:
                            if (switch_next_step, switch_inputpath) in self.buttons:
                                self.buttons[switch_next_step, switch_inputpath].config(state=tk.DISABLED)
                                # self.output_box.delete(1.0, "end-1c")
                                self.output_box.insert("end-1c", f"\nThe  next step {pipeline_step} cannot be done as "
                                                                 f"there is no input in {switch_inputpath} for it in "
                                                                 f"your destination folder")

    def run_shell_command(self, parametersets, command_step, inputpaths):
        pipeline_steps = [i[0] for i in list(self.pipeline_params.keys())]
        pipeline_steps_string_comma_sep = ','.join(pipeline_steps)
        pipeline_steps_string_space_sep = ' '.join(pipeline_steps)
        dapiseg_steps_string_space_sep = ' '.join(self.dapiseg_steps)
        merge_channels_string_space_sep = ' '.join(self.merge_channels_steps)
        cropping_exp_steps_string_space_space_sep = ' '.join(self.cropping_experimental_steps)
        subfolders_string_comma_sep = ','.join(self.subfolder_list)
        subfolders_string_space_sep = ' '.join(self.subfolder_list)
        realignment_subfolders_string_comma_sep = ','.join(self.realignment_subfolder_list)
        dapiseg_subfolders_string_comma_sep = ','.join(self.dapiseg_subfolder_list)
        dapiseg_subfolders_string_space_sep = ' '.join(self.dapiseg_subfolder_list)
        command = []
        command_string = ''
        destination = self.destinationLocation.get()
        for parameterset in parametersets:
            if parameterset[2] == self.dapiseg_steps[1]:
                self.get_gpu_input()
            if self.varGPU.get() != 0 and parameterset[2] == self.dapiseg_steps[1]:
                y = list(parameterset)
                y[1] = list(self.envs)[2]
                parameterset = tuple(y)
            package, env, step = parameterset
            if package == self.packages[1] and env != "":
                command.append(
                    f"conda activate {env} && {package} {self.main_py_PATH} --target {destination} --working_dir "
                    f"{self.main_work_dir} --step {step} --pipeline_steps {pipeline_steps_string_space_sep} "
                    f"--dapiseg_steps {dapiseg_steps_string_space_sep}"
                    f" --merge_channels_steps {merge_channels_string_space_sep}"
                    f" --cropping_exp_steps {cropping_exp_steps_string_space_space_sep}"
                    f" --subfolders "
                    f"{subfolders_string_space_sep} --dapiseg_subfolders "
                    f"{dapiseg_subfolders_string_space_sep} && conda deactivate")
            elif package == self.packages[0]:
                command.append(
                    f"%FIJIPATH% --ij2 --run {self.macro_py_PATH} \"base_dir='{self.sourceLocation.get()}' , "
                    f"working_dir = "
                    f"'{self.main_work_dir}' , target_dir = '{destination}' , step = '{step}' , pipeline_steps = "
                    f"'{pipeline_steps_string_comma_sep}' , subfolders = '{subfolders_string_comma_sep}' , "
                    f"realignment_subfolders = '{realignment_subfolders_string_comma_sep}' , dapiseg_subfolders = "
                    f"'{dapiseg_subfolders_string_comma_sep}' \"")

            else:
                logger.info("Not correct shell command. Please check it")
        if command:
            command_string = ' && '.join(command)
        p = subprocess.Popen(command_string, shell=True)
        """
        A None value indicates that the process hasn't terminated yet.
        """
        p.wait()
        self.buttons[command_step, inputpaths].config(bg='yellow')
        # for parameterset in parametersets:
        #    package, env, step = parameterset
        #    self.switch(step)
        return "done"

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
            self.get_gpu_input()
            import gdown
            for key in self.envs:
                if key not in "" and not os.path.exists(list(self.envs[key])[0]):
                    gdown.download(list(self.envs[key])[1], list(self.envs[key])[0], quiet=False)
            for key in self.envs:
                if key not in "":
                    self.create_conda_environment(key, list(self.envs[key])[0])

            for command_step, inputpaths in self.buttons:
                self.buttons[command_step, inputpaths].config(bg=self.orig_color_button)
                if command_step == list(self.pipeline_params)[0][0]:
                    self.buttons[command_step, inputpaths].config(state=tk.NORMAL)
                    CreateScreenTip(self.buttons[command_step, inputpaths], "Pipeline Start Step")
                else:
                    current_inputpaths = [ht.correct_path(self.destinationLocation.get(), path) for path in
                                          inputpaths.split(",")]
                    if command_step == list(self.pipeline_params)[5][0] or command_step == \
                            list(self.pipeline_params)[6][0]:
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
                    if step != list(self.pipeline_params)[0][0]]):
                self.output_box.delete(1.0, "end-1c")  # Clears the text box of data
                self.output_box.insert("end-1c", f"Please start with {list(self.pipeline_params)[0][0]}")
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

#    def switch(self, step):
#        current_next_steps = []
#        current_outputpaths = []
#        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
#            if step == pipeline_step:
#                current_next_steps = current_next_steps + next_steps.split(",")
#                current_outputpaths = [ht.correct_path(self.destinationLocation.get(), path) for path in
#                                       outputpaths.split(",")]
#        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
#            if step == pipeline_step:
#                for switch_next_step in current_next_steps:
#                    if switch_next_step != '':
#
#                        switch_inputpath = self.match_string(outputpaths.split(","),
#                                                             [k[1] for k, v in self.buttons.items() if
#                                                              k[0] == switch_next_step][0])
#                        check = self.match_string(current_outputpaths, switch_inputpath)
#                        # if any([os.path.exists(inputpath) for inputpath in current_outputpaths]):
#                        if check:
#                            for switch_inputpath_ in list(
#                                    map(",".join, itertools.permutations(switch_inputpath.split(",")))):
#                                if (switch_next_step, switch_inputpath_) in self.buttons:
#                                    self.buttons[switch_next_step, switch_inputpath_].config(
#                                        state=tk.NORMAL)
#                                    # self.output_box.delete(1.0, "end-1c")  # Clears the text box of data
#                                    pipe_step = \
#                                        [k[0] for k, v in self.pipeline_params.items() if k[0] == switch_next_step][0]
#                                    self.output_box.insert("end-1c", f"\nThe  next step {pipe_step} can be done. The "
#                                                                     f"input is in {switch_inputpath} in your "
#                                                                     f"destination "
#                                                                     f"folder")  # adds text
#                                    # to text box
#                        else:
#                            if (switch_next_step, switch_inputpath) in self.buttons:
#                                self.buttons[switch_next_step, switch_inputpath].config(state=tk.DISABLED)
#                                # self.output_box.delete(1.0, "end-1c")
#                                self.output_box.insert("end-1c", f"\nThe  next step {pipeline_step} cannot be done as "
#                                                                 f"there is no input in {switch_inputpath} for it in "
#                                                                 f"your destination folder")
