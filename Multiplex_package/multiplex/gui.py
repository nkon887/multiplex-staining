# multiplex.gui.py

# Importing necessary packages
import errno
import itertools
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from functools import partial
from tkinter import *
from tkinter import messagebox, filedialog, ttk
import tkinter.scrolledtext as st
import multiplex.helpertools as ht
from multiplex.screentip import CreateScreenTip
from multiplex.setup_logger import logger
from tkinter.messagebox import askyesno


# Defining App to create necessary tkinter widgets
class App:
    def __init__(self, master, pipeline_params, stitching_steps, align_steps, dapiseg_steps, merge_channels_steps, bg_steps,
                 cropping_experimental_steps, fast_button_step, subfolders_list, realignment_subfolder_list,
                 dapiseg_subfolder_list, command_arguments, packages, envs, main_work_dir, main_py_PATH,
                 macro_py_PATH, csv_ext, metadata_file):
        # Creating tkinter variable
        self.csv_ext = csv_ext
        self.metadata_file = metadata_file
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
        self.stitching_steps = stitching_steps
        self.align_steps = align_steps
        self.dapiseg_steps = dapiseg_steps
        self.merge_channels_steps = merge_channels_steps
        self.bg_steps = bg_steps
        self.cropping_experimental_steps = cropping_experimental_steps
        self.fast_button_step = fast_button_step
        self.subfolder_list = subfolders_list
        self.realignment_subfolder_list = realignment_subfolder_list
        self.dapiseg_subfolder_list = dapiseg_subfolder_list
        self.packages = packages
        self.main_work_dir = main_work_dir
        self.main_py_PATH = main_py_PATH
        self.macro_py_PATH = macro_py_PATH
        self.buttons = {}
        self.r = {}
        self.envs = envs
        self.env_to_exclude = list(self.envs)[2]
        self.command_arguments = command_arguments
        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if pipeline_step != "CROP":
                self.buttons[pipeline_step, inputpaths] = Button(self.left_frame,
                                                                 text=pipeline_step.replace("_", " ").upper(),
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
                                                                                          self.command_arguments[2]]]
                                                                                     for
                                                                                     i in range(
                                                                                         len(
                                                                                             self.pipeline_params[
                                                                                                 pipeline_step, next_steps, inputpaths, outputpaths]))
                                                                                 ],
                                                                                         pipeline_step, inputpaths))
                                                                 ,
                                                                 width=30, font=("Times New Roman", 12, "bold"))
            elif pipeline_step == "CROP":
                self.buttons[pipeline_step, inputpaths] = Button(self.left_frame,
                                                                 text=pipeline_step.replace("_", " ").upper(),
                                                                 command=partial(self.processingPleaseWait_, master,
                                                                                 pipeline_step,
                                                                                 partial(self.run_shell_command,
                                                                                         self.set_params_by_crop(
                                                                                             pipeline_step, next_steps,
                                                                                             inputpaths, outputpaths,
                                                                                             0),
                                                                                         pipeline_step, inputpaths))
                                                                 ,
                                                                 width=30, font=("Times New Roman", 12, "bold"))

            self.orig_color_button = self.buttons[pipeline_step, inputpaths].cget("background")
            self.buttons[pipeline_step, inputpaths].config(state=tk.NORMAL)
            self.buttons[pipeline_step, inputpaths].pack(side=tk.TOP, pady=10, padx=20)
            if r'{}'.format(self.sourceLocation.get()) == "" and r'{}'.format(self.destinationLocation.get()) == "":
                self.buttons[pipeline_step, inputpaths].config(state=tk.DISABLED)
            else:
                self.buttons[pipeline_step, inputpaths].config(state=tk.NORMAL)
        self.exit_button = Button(self.left_frame,
                                  text="QUIT", fg="red",
                                  command=threading.Thread(target=self.left_frame.quit).start, width=30,
                                  font=("Times New Roman", 12, "bold"))
        self.exit_button.pack(side=tk.TOP, pady=10, padx=20)
        CreateScreenTip(self.exit_button, "Click it to close the App Window")
        self.main_input_Label = LabelFrame(self.right_frame, text="INPUT/OUTPUT PATHS",
                                           background="black", fg="white", font=("Times New Roman", 12, "bold"),
                                           width=110)
        self.main_input_Label.grid(row=0, column=0, pady=5, padx=5)

        # self.patterns_Label = Label(self.right_frame, text="Name Pattern Exceptions: ",
        #                            bg="#E8D579", width=20, height=1)
        # self.patterns_Label.grid(row=1, column=1, pady=5, padx=5)
        # self.patterns_Text = Entry(self.right_frame, width=50, textvariable=self.patterns)
        # self.patterns_Text.grid(row=1, column=2, pady=5, padx=5, columnspan=2)

        self.link_Label = Label(self.main_input_Label, text="Select The Source: ", font=("Times New Roman", 14),
                                background="#E8D579", width=20)
        self.link_Label.grid(row=1, column=0, pady=5, padx=5)
        self.sourceText = Entry(self.main_input_Label, textvariable=self.sourceLocation, font=("Times New Roman", 14),
                                width=32)
        self.sourceText.grid(row=1, column=1, pady=5, padx=5)
        self.source_browseButton = Button(self.main_input_Label, text="Browse", font=("Times New Roman", 14), width=20,
                                          command=self.source_browse)
        self.source_browseButton.grid(row=1, column=3, pady=5, padx=5)
        CreateScreenTip(self.sourceText, "Input path of data to be stitched")
        CreateScreenTip(self.source_browseButton, "Please click here to select the input directory")
        self.destinationLabel = Label(self.main_input_Label, text="Select The Destination: ",
                                      background="#E8D579", font=("Times New Roman", 14), width=20)
        self.destinationLabel.grid(row=2, column=0, pady=5, padx=5)
        self.destinationText = Entry(self.main_input_Label, textvariable=self.destinationLocation,
                                     font=("Times New Roman", 14), width=32)
        self.destinationText.grid(row=2, column=1, pady=5, padx=5)
        self.dest_browseButton = Button(self.main_input_Label, text="Browse", font=("Times New Roman", 14),
                                        command=self.destination_browse, width=20)
        self.dest_browseButton.grid(row=2, column=3, pady=5, padx=5)
        CreateScreenTip(self.destinationText,
                        "Output path of the working directory")
        CreateScreenTip(self.dest_browseButton, "Please click here to select the output path of the working directory")

        self.main_input_parameters_Label = LabelFrame(self.right_frame, text="STEP PARAMETERS", background="black",
                                                      fg="white", font=("Times New Roman", 12, "bold"), width=110)
        self.main_input_parameters_Label.grid(row=3, column=0, pady=5, padx=5)
        # Define a Checkbox
        self.info_frame_gpu_force_save = LabelFrame(self.main_input_parameters_Label,
                                                    text="Check the GPU option and the Force Save options",
                                                    bg="#E8D579",
                                                    font=("Times New Roman", 14), width=90)
        self.info_frame_gpu_force_save.grid(row=4, column=0, padx=5, pady=5)
        self.GPU_Toggle = Checkbutton(self.info_frame_gpu_force_save, text="GPU", bg="#E8D579", variable=self.varGPU,
                                      onvalue=1,
                                      offvalue=0, font=("Times New Roman", 14), width=32)
        self.GPU_Toggle.grid(row=5, column=0, pady=5, padx=5)
        CreateScreenTip(self.info_frame_gpu_force_save,
                        "Please toggle the GPU option (for DAPISEG step acceleration) if you have GPU and toggle the "
                        "ForceSave option if you want to rewrite the output data on your PC")
        self.selected_forceSave_Option = IntVar()
        # check button
        self.forceSave_Toggle = Checkbutton(self.info_frame_gpu_force_save, text="forceSave",
                                            variable=self.selected_forceSave_Option, onvalue=1, offvalue=0,
                                            bg="#E8D579", width=32, font=("Times New Roman", 14))
        self.forceSave_Toggle.grid(row=5, column=2, padx=5, pady=5)
        self.selected_crop_Option = StringVar(None, 'manual')
        self.crop_options = (('Manual_Selection', 'manual'),
                             ('Semiautomatic_Selection', 'semiautomatic'),
                             ('Automatic_Selection', 'automatic'))
        self.info_frame_crop = LabelFrame(self.main_input_parameters_Label,
                                          text="Choose the cropping option for the step CROP",
                                          bg="#E8D579", font=("Times New Roman", 14), width=90)

        self.info_frame_crop.grid(row=6, column=0, padx=5, pady=5)
        # radio buttons
        for i, crop_option in enumerate(self.crop_options):
            self.r[crop_option] = Radiobutton(self.info_frame_crop, text=crop_option[0].replace("_", " "),
                                              value=crop_option[1],
                                              variable=self.selected_crop_Option, bg="#E8D579", width=20,
                                              font=("Times New Roman", 14))
            self.r[crop_option].grid(row=6, column=i, padx=5, pady=5)
        CreateScreenTip(self.info_frame_crop,
                        "Please select the mode option for the step CROP.`Manual Selection`: the stack of a certain "
                        "`sampleID` is loaded, and the user has to set the region of interest manually and then after "
                        "the confirmation (clicking `Ok` in the `Action required` dialog) it is automatically "
                        "cropped. `Semiautomatic Selection`: the coordinates of the rectangle frame excluding the "
                        "black regions of the background will be automatically determined and preset for the user and "
                        "it can be then adjusted if needed, then after confirmation (clicking `Ok` in the `Action "
                        "required` dialog) the image files are cropped. `Automatic Selection`: the coordinates of the "
                        "rectangle form excluding the black background regions are automatically determined and "
                        "automatically cut without user intervention.")
        self.main_output_Label = LabelFrame(self.right_frame, text="OUTPUT MESSAGES", background="black",
                                            fg="white", font=("Times New Roman", 12, "bold"), width=110)
        self.main_output_Label.grid(row=8, column=0, pady=5, padx=5)
        self.output_box = st.ScrolledText(self.main_output_Label, height=4, font=("Times New Roman", 14), width=78)
        self.output_box.grid(row=9, column=0, pady=5, padx=5)
        self.output_box.insert("end-1c", self.initial_output_statement)

        CreateScreenTip(self.main_output_Label, "The status of the executed step is displayed in this box")
        # self.copyButton = Button(self.right_frame, text="Copy File(s)",
        #                         command=self.copy_file, width=15)
        # self.copyButton.grid(row=4, column=2, pady=5, padx=5)
        # self.moveButton = Button(self.right_frame, text="Move File(s)",
        #                         command=self.move_file, width=15)
        # self.moveButton.grid(row=4, column=3, pady=5, padx=5)
        self.left_frame.pack(side=tk.LEFT)
        self.line.pack(side=tk.LEFT, padx=10)
        self.right_frame.pack(side=tk.LEFT)

    def set_params_by_crop(self, pipeline_step, next_steps, inputpaths, outputpaths, crop_option):
        pipeline_params = [
            [self.pipeline_params[
                 pipeline_step, next_steps, inputpaths, outputpaths][crop_option][
                 i][
                 self.command_arguments[0]],
             self.pipeline_params[
                 pipeline_step, next_steps, inputpaths, outputpaths][
                 crop_option][
                 i][
                 self.command_arguments[1]],
             self.pipeline_params[
                 pipeline_step, next_steps, inputpaths, outputpaths][
                 crop_option][
                 i][
                 self.command_arguments[2]]]
            for
            i in range(
                len(
                    self.pipeline_params[
                        pipeline_step, next_steps, inputpaths, outputpaths][
                        crop_option]))
        ]
        return pipeline_params

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
    # def processingPleaseWait(self, pipeline_step, function):
    #    import tkinter, time, threading
    #    window_of_process = tkinter.Toplevel()  # or tkinter.Tk()
    #    # code before computation starts
    #    window_of_process.title("Running the step " + pipeline_step)
    #    window_of_process.geometry('500x100')
    #    window_of_process['bg'] = 'yellow'
    #    label = tkinter.Label(window_of_process, text="Waiting ...")
    #    label.pack()
    #    done = []
    #
    #    def call():
    #        result = function()
    #        done.append(result)
    #
    #    thread = threading.Thread(target=call)
    #    thread.start()  # start parallel computation
    #    while thread.is_alive():
    #        # code while computation
    #        window_of_process.update()
    #        time.sleep(0.001)
    #        # code when computation is done
    #    label['text'] = str(done)
    #    window_of_process['bg'] = 'green'

    # Define Function to get the input value of varGPU
    def get_crop_option(self):
        crop_value = self.selected_crop_Option.get()
        logger.info("CROP selection " + str(crop_value))

    def get_forceSave_option(self):
        forceSave_value = self.selected_forceSave_Option.get()
        logger.info("forceSave selection " + str(forceSave_value))

    def processingPleaseWait_(self, master, step, function):
        import tkinter, time, threading
        window_of_process = master
        # code before computation starts
        window_of_process.title("Running the step " + step)
        # window_of_process.geometry('500x100')
        # window_of_process['bg'] = 'yellow'
        # = tkinter.Label(window_of_process, text="Waiting ...")
        # label.pack()
        self.output_box.insert("end-1c", f"\n{step} is running. Waiting ...")
        done = []

        def call():
            result = function()
            done.append(result)

        thread = threading.Thread(target=call)
        thread.start()  # start parallel computation
        while thread.is_alive():
            # code while computation
            window_of_process.update()
            time.sleep(0.001)
            # code when computation is done
        # label['text'] = str(done)
        self.output_box.insert("end-1c", "\n" + done[0])
        # window_of_process['bg'] = 'green'
        current_next_steps = []
        current_outputpaths = []
        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step == pipeline_step:
                current_next_steps = current_next_steps + next_steps.split(",")
                current_outputpaths = [ht.correct_path(r'{}'.format(self.destinationLocation.get()), path) for path in
                                       outputpaths.split(",")]
        for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
            if step == pipeline_step:
                for switch_next_step in current_next_steps:
                    if switch_next_step != '':
                        # logger.info(switch_next_step)
                        # logger.info(self.buttons.items())
                        switch_inputpath = self.match_string(outputpaths.split(","),
                                                             [k[1] for k, v in self.buttons.items() if
                                                              k[0] == switch_next_step][0])
                        check = self.match_string(current_outputpaths, switch_inputpath)
                        # if any([os.path.exists(inputpath) for inputpath in current_outputpaths]):
                        if check and "ERROR" not in done[0]:
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
                                self.output_box.insert("end-1c",
                                                       f"\nThe  next step {switch_next_step} cannot be done as "
                                                       f"there is either no input in {switch_inputpath} for it in "
                                                       f"your destination folder or the ERROR was during the "
                                                       f"last step {pipeline_step}")

    def confirm_dialog(self, message):
        answer = askyesno(title='confirmation', message=message)
        if answer:
            return 'yes'
        else:
            return 'no'

    def run_shell_command(self, parametersets, command_step, inputpaths):
        self.get_forceSave_option()
        forceSave_option = self.selected_forceSave_Option.get()
        selected_crop_Option = self.selected_crop_Option.get()
        pipeline_steps = [i[0] for i in list(self.pipeline_params.keys())]
        pipeline_steps_string_comma_sep = ','.join(pipeline_steps)
        pipeline_steps_string_space_sep = ' '.join(pipeline_steps)
        stitching_steps_string_space_sep = ' '.join(self.stitching_steps)
        align_steps_string_space_sep = ' '.join(self.align_steps)
        dapiseg_steps_string_space_sep = ' '.join(self.dapiseg_steps)
        merge_channels_string_space_sep = ' '.join(self.merge_channels_steps)
        bg_string_space_sep = ' '.join(self.bg_steps)
        cropping_exp_steps_string_space_sep = ' '.join(self.cropping_experimental_steps)
        fast_button_step_string_space_sep = ' '.join(self.fast_button_step)
        subfolders_string_comma_sep = ','.join(self.subfolder_list)
        subfolders_string_space_sep = ' '.join(self.subfolder_list)
        realignment_subfolders_string_comma_sep = ','.join(self.realignment_subfolder_list)
        dapiseg_subfolders_string_comma_sep = ','.join(self.dapiseg_subfolder_list)
        dapiseg_subfolders_string_space_sep = ' '.join(self.dapiseg_subfolder_list)
        command = []
        command_string = ''
        destination = r'{}'.format(self.destinationLocation.get())
        trigger = 'no'
        if command_step == "CLEAN_OUTPUT":
            trigger = self.confirm_dialog('Are you sure that you want to clean intermediate data and get only results data?')
            if trigger == 'no':
                return "The user canceled the step execution. Doing nothing" + "\nDONE"
        if command_step == "CROP":
            self.get_crop_option()
            # logger.info(self.selected_crop_Option.get())
            for item in range(len(self.crop_options)):
                if selected_crop_Option == self.crop_options[item][1]:
                    for (pipeline_step, next_steps, inputpaths, outputpaths) in self.pipeline_params:
                        if pipeline_step == command_step:
                            parametersets = self.set_params_by_crop(pipeline_step, next_steps, inputpaths, outputpaths,
                                                                    item)
        for parameterset in parametersets:
            if parameterset[2] == self.dapiseg_steps[2]:
                self.get_gpu_input()
            if self.varGPU.get() != 0 and parameterset[2] == self.dapiseg_steps[2]:
                y = list(parameterset)
                y[1] = list(self.envs)[2]
                parameterset = tuple(y)
            package, env, step = parameterset
            if package == self.packages[1] and env != "" and step not in self.dapiseg_steps[2]:
                # destination = destination.replace(" ", "\\ ")
                command.append(
                    f"conda activate {env} && {package} {self.main_py_PATH} --source " + r'{}'.format(
                        self.sourceLocation.get()) + " --target " + r'{}'.format(
                        destination) + " --working_dir "
                                       f"{self.main_work_dir} --env {env} --step {step} --pipeline_steps {pipeline_steps_string_space_sep} "
                                       f" --stitching_steps {stitching_steps_string_space_sep}"
                                       f" --dapiseg_steps {dapiseg_steps_string_space_sep}"
                                       f" --merge_channels_steps {merge_channels_string_space_sep}"
                                       f" --bg_steps {bg_string_space_sep}"
                                       f" --cropping_exp_steps {cropping_exp_steps_string_space_sep}"
                                       f" --fast_button_step {fast_button_step_string_space_sep}"
                                       f" --align_steps {align_steps_string_space_sep}"
                                       f" --subfolders "
                                       f"{subfolders_string_space_sep} --dapiseg_subfolders "
                                       f"{dapiseg_subfolders_string_space_sep} --forceSave "
                                       f"{forceSave_option} && conda deactivate")
            elif package == self.packages[1] and env != "" and step in self.dapiseg_steps[2]:
                folder = ht.correct_path(destination, self.main_work_dir)
                ht.setting_directory(destination, self.subfolder_list[4])
                dapi_seg_input_dir = ht.setting_directory(destination, self.dapiseg_subfolder_list[0])
                dapi_seg_output_dir = ht.setting_directory(destination, self.dapiseg_subfolder_list[1])
                root = os.path.dirname(os.path.realpath(__file__))
                dapi_main_py_PATH = os.path.join(root, 'dapi_seg_main.py')
                try:
                    # Get list of files in folder
                    file_list = os.listdir(folder)
                except:
                    file_list = []
                fnames = [
                    f
                    for f in file_list
                    if os.path.isfile(ht.correct_path(folder, f)) and f.lower().endswith(
                        self.csv_ext) and f.lower() == self.metadata_file
                ]
                # logger.info(ht.correct_path(folder, fnames[0]))
                dates_patients_channels_markers_dict = {}
                # channels_markers_out = []
                patientIDs = []
                dates_patients_channels_markers_together = []
                if len(fnames) == 1:
                    data = ht.read_data_from_csv(ht.correct_path(folder, self.metadata_file))
                    for dic in data:
                        patientIDs.append(dic["expID"])
                patientIDs = dict.fromkeys(patientIDs)
                for patientID in patientIDs:
                    command.append(
                        f"conda activate {env} && python {dapi_main_py_PATH}  --input {dapi_seg_input_dir} --out {dapi_seg_output_dir} --patientID {patientID} && conda deactivate")

            elif package == self.packages[0]:
                command.append(
                    f"%FIJIPATH% --ij2 --run {self.macro_py_PATH} \"base_dir='{r'{}'.format(self.sourceLocation.get())}' , "
                    f"working_dir = "
                    f"'{self.main_work_dir}' , target_dir = '{destination}' , step = '{step}' , pipeline_steps = "
                    f"'{pipeline_steps_string_comma_sep}' , subfolders = '{subfolders_string_comma_sep}' , "
                    f"realignment_subfolders = '{realignment_subfolders_string_comma_sep}' , dapiseg_subfolders = "
                    f"'{dapiseg_subfolders_string_comma_sep}' , crop_option = '{selected_crop_Option}', forceSave = "
                    f"'{forceSave_option}'\"")

            else:
                logger.info("Not correct shell command. Please check it")
        #        if command:
        #            command_string = ' && '.join(command)
        split_words = ["WARNING", "ERROR"]
        out_step = ""
        for cmd in command:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            for line in iter(p.stdout.readline, b""):
                sys.stdout.buffer.write(line)
            out = p.communicate()[0]
            out = self.checkIfNone(out)
            out_step += out
            """
            A None value indicates that the process hasn't terminated yet.
            """
            p.wait()
        output_message = ""
        for substring in out_step.splitlines():
            messages = ""
            for split_word in split_words:
                if split_word in substring:
                    messages = split_word + substring.split(split_word)[1] + "\n"
            output_message += messages
        # logger.info(self.buttons)
        self.buttons[command_step, inputpaths].config(bg='yellow')
        # for parameterset in parametersets:
        #    package, env, step = parameterset
        #    self.switch(step)
        return output_message + "\nDONE"

    def checkIfNone(self, var):
        if var is not None:
            var = var.decode("utf-8")
        else:
            var = ""
        return var

    #    def create_conda_environment(self, env_name, requirements_file):
    #        env_exists = False
    #        try:
    #            subprocess.run(f"conda activate {env_name}", shell=True, check=True)
    #            env_exists = True
    #        except subprocess.CalledProcessError as e:
    #            pass
    #        if not env_exists:
    #            subprocess.run(f"conda env create -f {requirements_file}", shell=True)
    #            logger.info(f"Conda environment {env_name} created.")
    #        else:
    #            logger.info(f"{env_exists} Conda environment {env_name} already exists.")

    def source_browse(self):
        # Opening the file-dialog directory prompting the user to select files to copy using
        # filedialog.askopenfilenames() method. Setting initialdir argument is optional Since multiple
        # files may be selected, converting the selection to list using list()

        # self.files_dir = filedialog.askdirectory(initialdir=self.base_dir)
        self.files_dir = filedialog.askdirectory()

        # Displaying the selected files in the root.sourceText
        self.sourceText.delete(0, tk.END)  # Remove current text in entry
        # Entry using root.sourceText.insert()
        self.sourceText.insert(0, self.files_dir)
        self.switch_on_buttons()

    def switch_on_buttons(self):
        if r'{}'.format(self.sourceLocation.get()) != "" and r'{}'.format(self.destinationLocation.get()) != "":
            self.get_gpu_input()
            #            import gdown
            #            for key in self.envs:
            #                if key not in "" and not os.path.exists(list(self.envs[key])[0]):
            #                    gdown.download(list(self.envs[key])[1], list(self.envs[key])[0], quiet=False)
            #            for key in self.envs:
            #                if key not in "":
            #                    self.create_conda_environment(key, list(self.envs[key])[0])

            for command_step, inputpaths in self.buttons:
                self.buttons[command_step, inputpaths].config(bg=self.orig_color_button)
                if command_step == list(self.pipeline_params)[0][0]:
                    self.buttons[command_step, inputpaths].config(state=tk.NORMAL)
                    CreateScreenTip(self.buttons[command_step, inputpaths], "Pipeline Start Step")
                else:
                    current_inputpaths = [ht.correct_path(r'{}'.format(self.destinationLocation.get()), path) for path
                                          in
                                          inputpaths.split(",")]
                    if command_step == list(self.pipeline_params)[4][0] or command_step == \
                            list(self.pipeline_params)[8][0]:
                        # logger.info(str(list(self.pipeline_params)[5][0]))
                        pattern = re.compile(r'.*_Cropped\.tif')
                        if all([os.path.exists(inputpath) for inputpath in current_inputpaths]):
                            for inputpath in current_inputpaths:
                                # logger.info(inputpath)
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
        # self.destinationdirectory = filedialog.askdirectory(
        #    initialdir=self.base_dir)
        self.destinationdirectory = filedialog.askdirectory()
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
        destination_location = r'{}'.format(self.destinationLocation.get())
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
        destination_location = r'{}'.format(self.destinationLocation.get())

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
