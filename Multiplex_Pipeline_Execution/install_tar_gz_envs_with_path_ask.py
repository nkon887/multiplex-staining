#! /usr/bin/env python
import os
import subprocess
import threading
import time
import tkinter as tk
import tkinter.filedialog as filedialog

def run_shell_process(command, out=False):
    if out:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
        out = result.stdout
        return out
    else:
        subprocess.run(" && ".join(command), shell=True)
        return

def create_conda_environment(env_name, requirements_file, packages_to_install):
    env_exists = False

    try:
        subprocess.run(f"conda activate {env_name}", shell=True, check=True)
        env_exists = True
    except subprocess.CalledProcessError as e:
        pass
    if not env_exists:
        if requirements_file == " ":
            subprocess.run(
                ''.join([f"conda create -y --name {env_name} python=3.10"
                         ]),
                shell=True)
        elif requirements_file != " ":
            comm = f"conda env create -f \"{requirements_file}\""
            #           print(comm)
            subprocess.run(comm, shell=True)
        for package in packages_to_install:
            if os.path.exists(package):
                command = [f"conda activate {env_name}", f"pip install \"{package}\"", "conda deactivate"]
            else:
                command = [f"conda activate {env_name}", f"pip install {package}", "conda deactivate"]
            #            print(command)
            run_shell_process(command, False)
        print(f"Conda environment {env_name} created.")
    else:
        print(f"{env_exists} Conda environment {env_name} already exists.")


def install(environments):
    for env in environments:
        create_conda_environment(f"{env}",
                                 f"{environments[env]['yml_file']}", environments[env]["packages_to_install"])
    return "The installation is complete. The environments are set up. The multiplex pipeline is ready for use"


def install_processing_please_wait(environments):
    done = []

    def call():
        result = install(environments)
        done.append(result)

    thread = threading.Thread(target=call)
    thread.start()  # start parallel computation
    while thread.is_alive():
        time.sleep(0.001)
    print(done[0])

def look_for_env_and_unpack(path):
    import glob, os
    os.chdir(path)
    for file in glob.glob("*.tar.gz"):
        if "multiplex" in file or "cellsegsegmenter_gpu" in file or "cellsegsegmenter_cpu" in file:
            run_shell_process([f"mkdir {os.path.splitext(os.path.basename(file))}", f"tar -xf {file} -C {os.path.splitext(os.path.basename(file))}"])

def targz_browse():
    # Opening the file-dialog directory prompting the user to select destination folder toAdd commentMore actions
    # which files are to be copied using the filedialog.askopendirectory() method
    # Setting initialdir argument is optional
    path = tk.filedialog.askdirectory()
    targz_download_entry.delete(0, tk.END)  # Remove current text in entry
    targz_download_entry.insert(0, path)  # Insert the 'path'
    targz_envs_location.set(path)


start_pipeline_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#look_for_env_and_unpack(start_pipeline_dir_path)
im_jy_repo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "im-jy-package/target")
master = tk.Tk()
master.title("Pipeline Start")
mainframe = tk.Frame(master)
targz_envs_location = tk.StringVar()
targz_download_path = tk.Label(mainframe, text="TARGZ Download File Path:")
targz_download_path.grid(row=1, column=0, pady=5, padx=5)
targz_download_entry = tk.Entry(mainframe, width=32, textvariable=targz_envs_location)
targz_download_entry.grid(row=1, column=1, pady=5, padx=5)
targz_browse = tk.Button(mainframe, text="Browse", command=targz_browse, width=15)
targz_browse.grid(row=1, column=2, pady=5, padx=5)
open_button = tk.Button(master, text='Continue', command=master.destroy, width=15)
mainframe.pack(pady=10)
open_button.pack(pady=10)
master.mainloop()
#tar_env_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tar_envs")
from pathlib import Path
tar_env_dir = Path(targz_envs_location.get())
command = "echo %FIJIPATH%"
path_to_fiji_act = run_shell_process(command, True)
path_to_fiji = os.path.dirname(path_to_fiji_act.decode('UTF-8'))
import shutil
path_to_fiji_module = os.path.join(path_to_fiji, "jars/Lib")
if not os.path.exists(path_to_fiji_module):
    os.mkdir(path_to_fiji_module)
path_to_fiji_module_file_target = os.path.join(path_to_fiji_module, "im-jy-package-0.1.0-SNAPSHOT.jar")
path_to_fiji_module_file_source = os.path.join(im_jy_repo_dir, "im-jy-package-0.1.0-SNAPSHOT.jar")
if not os.path.exists(path_to_fiji_module_file_target):
    shutil.copyfile(path_to_fiji_module_file_source, path_to_fiji_module_file_target)
else:
    os.remove(path_to_fiji_module_file_target)
    shutil.copyfile(path_to_fiji_module_file_source, path_to_fiji_module_file_target)

import glob
list_tar_files_paths = []
if os.path.exists(tar_env_dir) and len(os.listdir(tar_env_dir)) !=  0:
    list_tar_files_paths = glob.glob(os.path.join(tar_env_dir,"*.tar.gz"))
else:
    print(f"The directory {tar_env_dir} doesn't exist (removed) or it is empty. Please check it and change it. Create and or add tar gz files to the directory {tar_env_dir} and rerun this script again")
env_dir_paths={}
if len(list_tar_files_paths) !=0:
    for tar_file_path in list_tar_files_paths:
        env_dir= (os.path.splitext(os.path.basename(tar_file_path))[0]).split('.')[0]
        env_dir_path = os.path.join(tar_env_dir, env_dir)
        env_dir_paths[env_dir]=env_dir_path
        command = " && ".join([f"mkdir {env_dir_path}", f"tar -xzf {tar_file_path} -C  {env_dir_path}", f"cd {env_dir_path}",
                     r".\Scripts\activate.bat", r".\Scripts\conda-unpack.exe", r".\Scripts\deactivate.bat"])
        print(command)
        subprocess.run(command, shell=True)
        print(f"The environment {env_dir} is set with the path {env_dir_path}")
    print("All environments are now successfully set")
else:
    print(f"There are no tar.gz files to find in the directory {tar_env_dir}. Please check it and rerun this script again")
env_dir_path_multiplex = ""
multiplex_env = "multiplex"
if multiplex_env in env_dir_paths:
    env_dir_path_multiplex = env_dir_paths[multiplex_env]
if env_dir_path_multiplex != "":
    run_shell_process([f"cd {env_dir_path_multiplex}", r".\Scripts\activate.bat", f"python -m {multiplex_env} --path {tar_env_dir}"])
else:
    print(f"The environment {multiplex_env} can't be found")