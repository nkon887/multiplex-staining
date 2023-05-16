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
                             command=frame.quit, )
        self.button.pack(side=tkinter.TOP, pady=5, padx=20)
        self.create_conda_environment("multiplex", "env_multiplex.yml")
        bash_scr_path = os.path.join(os.getcwd(), "exec.sh").replace("\\", "/")
        self.process = Button(frame,
                              text="STITCHING".upper(),
                              command=partial(self.run_bash_command, bash_scr_path, "STITCHING"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="IMAGE PREPARATION".upper(),
                              command=partial(self.run_process_python, "multiplex", "python",
                                              "image_preparation.py"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="ALIGNMENT".upper(),
                              command=partial(self.run_bash_command, bash_scr_path, "ALIGNMENT"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="GENERATION OF HYPERSTACKS".upper(),
                              command=partial(self.run_bash_command, bash_scr_path,
                                              "GENERATION OF "
                                              "HYPERSTACKS"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="CROPPING BEFORE ALIGNMENT".upper(),
                              command=partial(self.run_bash_command, bash_scr_path, "CROPPING "
                                                                                    "BEFORE "
                                                                                    "ALIGNMENT"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="REALIGNMENT".upper(),
                              command=partial(self.run_bash_command, bash_scr_path,
                                              "REALIGNMENT"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="CROPPING AFTER ALIGNMENT".upper(),
                              command=partial(self.run_bash_command, bash_scr_path, "CROPPING "
                                                                                    "AFTER "
                                                                                    "ALIGNMENT"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="BACKGROUNDADJUSTMENT".upper(),
                              command=partial(self.run_bash_command, bash_scr_path,
                                              "BACKGROUNDADJUSTMENT"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="MERGING CHANNELS".upper(),
                              command=partial(self.run_bash_command, bash_scr_path, "MERGING "
                                                                                    "CHANNELS"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="DapiSeg Preparation".upper(),
                              command=partial(self.run_process_python, "multiplex", "python",
                                              "preparation_dapi_seg.py"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.create_conda_environment("cellsegsegmenter", "env_cellsegsegmenter.yml")
        self.process = Button(frame,
                              text="DapiSeg Segmentation".upper(),
                              command=partial(self.run_process_python, "cellsegsegmenter",
                                              "python", "dapi_seg_main.py"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="DapiSeg Postprocessing".upper(),
                              command=partial(self.run_process_python, "multiplex", "python",
                                              "postprocessing_dapi_seg.py"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="DAPISEG_RESIZER".upper(),
                              command=partial(self.run_bash_command, os.path.join(os.getcwd(), 'exec.sh'),
                                              "DAPISEG_RESIZER"))
        self.process.pack(side=tkinter.TOP, pady=5, padx=20)
        self.process = Button(frame,
                              text="Pipeline via Bash".upper(),
                              command=partial(self.run_bash_command, os.path.join(os.getcwd(), 'exec.sh')))
        # command=partial(self.run_bash_command, "ls"))
        self.process.pack(side=tkinter.BOTTOM, pady=5, padx=20)

    # def run_process_fiji(self, env, package, command):
    #    subprocess.run('')
    def run_process_python(self, env, package, command):
        subprocess.run('conda activate ' + env + ' && ' + package + ' ' + command + ' && conda deactivate',
                       shell=True, check=True)

    def run_bash_command(self, cmd, arg):
        # subprocess.Popen(["C:/Users/naam11/AppData/Local/Programs/Git/bin/bash.exe", '-c', cmd],
        subprocess.Popen(["C:/Users/naam11/AppData/Local/Programs/Git/bin/bash.exe", '-c', cmd + " " + arg],
                         bufsize=-1,
                         executable=None,
                         stdin=None,
                         stdout=None,
                         stderr=None,
                         preexec_fn=None,
                         close_fds=True,
                         shell=False)  # ,
        # cwd="C:/Users/naam11/Documents/GitHub/multiplex-staining/wdir_scripts")
        # , capture_output=True)

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
window.geometry('550x600')
window.mainloop()
