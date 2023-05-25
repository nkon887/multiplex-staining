import subprocess
import tkinter
from functools import partial
from tkinter import *
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


class App:
    def __init__(self, master):
        frame = Frame(master)
        frame.pack()
        self.button = Button(frame,
                             text="QUIT", fg="red",
                             command=frame.quit)
        self.button.pack(side=tkinter.TOP, pady=10, padx=20)
        self.create_conda_environment("multiplex", "env_multiplex.yml")
        self.process = Button(frame,
                              text="STITCHING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "STITCHING"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="IMAGE PREPARATION".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex",
                                                                        "image_preparation.py"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="ALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "ALIGNMENT"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="REALIGNMENT".upper(),
                              command=partial(self.run_shell_command, [['fiji', "", "REALIGNMENT"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="CROPPING".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "CROPPING AFTER ALIGNMENT"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)

        self.process = Button(frame,
                              text="BACKGROUNDADJUSTMENT".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "BACKGROUNDADJUSTMENT"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="MERGING CHANNELS".upper(),
                              command=partial(self.run_shell_command, [["fiji", "", "MERGING CHANNELS"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.create_conda_environment("cellsegsegmenter", "env_cellsegsegmenter.yml")
        self.process = Button(frame,
                              text="DapiSeg Segmentation".upper(),
                              command=partial(self.run_shell_command, [["python", "multiplex", "preparation_dapi_seg"
                                                                                               ".py"],
                                                                       ["python", "cellsegsegmenter", "dapi_seg_main"
                                                                                                      ".py"],
                                                                       ["python", "multiplex",
                                                                        "postprocessing_dapi_seg"
                                                                        ".py"], ["fiji", '', "DAPISEG_RESIZER"]]))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)

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


window = Tk()
app = App(window)
window.title("Running the Steps of Multiplex Pipeline")
window.geometry('550x450')
window.mainloop()
