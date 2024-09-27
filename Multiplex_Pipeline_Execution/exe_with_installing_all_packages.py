#! /usr/bin/env python
import subprocess
import threading
import time
import tkinter as tk
import tkinter.filedialog as filedialog
from functools import partial


def create_conda_environment(env_name, requirements_file):
    env_exists = False
    packages_to_install = ["gdown", "pandas", "pytest", "yargs"]
    try:
        subprocess.run(f"conda activate {env_name}", shell=True, check=True)
        env_exists = True
    except subprocess.CalledProcessError as e:
        pass
    if not env_exists and requirements_file == " ":
        subprocess.run(
            ''.join([f"conda create -y --name {env_name} python=3.10 "
                    f"&& conda activate {env_name}",
                    ''.join([f" && pip install {package}" for package in packages_to_install])]),
            shell=True)
        print(f"Conda environment {env_name} created.")
    elif not env_exists and requirements_file != " ":
        subprocess.run(f"conda env create -f {requirements_file}", shell=True)
        print(f"Conda environment {env_name} created.")
    else:
        print(f"{env_exists} Conda environment {env_name} already exists.")


def multiplex_browse():
    # Opening the file-dialog directory prompting the user to select destination folder to
    # which files are to be copied using the filedialog.askopendirectory() method
    # Setting initialdir argument is optional
    path = tk.filedialog.askdirectory()
    multiplex_download_entry.delete(0, tk.END)  # Remove current text in entry
    multiplex_download_entry.insert(0, path)  # Insert the 'path'
    multiplex_destination_location.set(path)


def cellseg_browse():
    # Opening the file-dialog directory prompting the user to select destination folder to
    # which files are to be copied using the filedialog.askopendirectory() method
    # Setting initialdir argument is optional
    path = tk.filedialog.askdirectory()
    cellseg_download_entry.delete(0, tk.END)  # Remove current text in entry
    cellseg_download_entry.insert(0, path)  # Insert the 'path'
    cellseg_destination_location.set(path)


def install():
    multiplex_repo_dir = multiplex_destination_location.get()
    cellseg_repo_dir = cellseg_destination_location.get()

    envs = {
        "myenv": {"packages_to_install": [f"{multiplex_repo_dir}/Multiplex_package"], "yml_file": " "},
        "multiplex": {"packages_to_install": [f"{multiplex_repo_dir}/Multiplex_package"],
                      "yml_file": f"{multiplex_repo_dir}/Multiplex_package/multiplex/envs/local/env_multiplex.yml"},
        "cellsegsegmenter_cpu": {"packages_to_install": [f"{multiplex_repo_dir}/Multiplex_package", f"{cellseg_repo_dir}"],
                                 "yml_file": f"{multiplex_repo_dir}/Multiplex_package/multiplex/envs/local/env_cellsegsegmenter_cpu.yml"},
        "cellsegsegmenter_gpu": {"packages_to_install": [f"{multiplex_repo_dir}/Multiplex_package", f"{cellseg_repo_dir}"],
                                 "yml_file": f"{multiplex_repo_dir}/Multiplex_package/multiplex/envs/local/env_cellsegsegmenter_gpu.yml"}
    }
    for env in envs:
        create_conda_environment(f"{env}",
                                 f"{envs[env]['yml_file']}")
    for env in envs:
        for package in envs[env]["packages_to_install"]:
            command = [f"conda activate {env}", f"pip install {package}", "conda deactivate"]
            run_shell_process(command)
    return "The installation is complete. The environments are set"


def run_shell_process(command):
    subprocess.run(" && ".join(command), shell=True)


def processingPleaseWait_(function):
    window_of_process = master
    window_of_process.title("Wait...The installation is running")
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
    window_of_process.title(done[0])


master = tk.Tk()
top_frame = tk.Frame(master)
bottom_frame = tk.Frame(master)
line = tk.Frame(master, height=1, width=400, bg="grey80", relief='groove')

# input_path = tk.Label(top_frame, text="WEB URL of the GITHUB Directory:")
# input_entry = tk.Entry(top_frame, text="https://github.com/nkon887/multiplex-staining.git", width=40)
# browse1 = tk.Button(top_frame, text="Browse", command=input)

multiplex_destination_location = tk.StringVar()
multiplex_download_path = tk.Label(bottom_frame, text="Multiplex Download File Path:")
multiplex_download_entry = tk.Entry(bottom_frame, width=40, textvariable=multiplex_destination_location)
multiplex_browse = tk.Button(bottom_frame, text="Browse", command=multiplex_browse)
cellseg_destination_location = tk.StringVar()
cellseg_download_path = tk.Label(bottom_frame, text="Cellseg Download File Path:")
cellseg_download_entry = tk.Entry(bottom_frame, width=40, textvariable=cellseg_destination_location)
cellseg_browse = tk.Button(bottom_frame, text="Browse", command=cellseg_browse)
install_button = tk.Button(bottom_frame, text="Installation", command=partial(processingPleaseWait_, install))
open_button = tk.Button(bottom_frame, text='Continue', command=master.destroy)

top_frame.pack(side=tk.TOP)
line.pack(pady=10)
bottom_frame.pack(side=tk.BOTTOM)

# input_path.pack(pady=5)
# input_entry.pack(pady=5)
# browse1.pack(pady=5)

multiplex_download_path.pack(pady=5)
multiplex_download_entry.pack(pady=5)
multiplex_browse.pack(pady=5)
cellseg_download_path.pack(pady=5)
cellseg_download_entry.pack(pady=5)
cellseg_browse.pack(pady=5)
install_button.pack(pady=20, fill=tk.X)
open_button.pack(pady=10, fill=tk.X)
master.mainloop()
cmd = [f"conda activate myenv", "python -m multiplex"]
run_shell_process(cmd)
