#! /usr/bin/env python
import os.path
import subprocess
from functools import partial


def create_conda_environment(env_name):
    env_exists = False
    try:
        subprocess.run(f"conda activate {env_name}", shell=True, check=True)
        env_exists = True
    except subprocess.CalledProcessError as e:
        pass
    if not env_exists:
        subprocess.run(
            f"conda create -y --name {env_name} python=3.10 "
            f"&& conda activate {env_name} && pip "
            f"install gdown && pip install pandas && pip install pytest && pip install yargs && pip install gitpython",
            shell=True)
        print(f"Conda environment {env_name} created.")
    else:
        print(f"{env_exists} Conda environment {env_name} already exists.")


def create_conda_environment_from_file(env_name, requirements_file):
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
        print(f"{env_exists} Conda environment {env_name} already exists.")


env_name = "myenv"
create_conda_environment(env_name)
import tkinter.filedialog as filedialog
import tkinter as tk

master = tk.Tk()


# def input():
#    input_path = tk.filedialog.askopenfilename()
#    input_entry.delete(1, tk.END)  # Remove current text in entry
#    input_entry.insert(0, input_path)  # Insert the 'path'


def destination_browse():
    # Opening the file-dialog directory prompting the user to select destination folder to
    # which files are to be copied using the filedialog.askopendirectory() method
    # Setting initialdir argument is optional
    path = tk.filedialog.askdirectory()
    download_entry.delete(0, tk.END)  # Remove current text in entry
    download_entry.insert(0, path)  # Insert the 'path'
    destination_location.set(path)


def download():
    from git import Repo
    git_url = "https://github.com/nkon887/multiplex-staining.git"
    repo_dir = destination_location.get()
    multiplex_location=f"{repo_dir}/multiplex"
    cellseg_location = f"{repo_dir}/cellseg"
    if not os.path.exists(multiplex_location):
        os.mkdir(multiplex_location)
        Repo.clone_from(git_url, multiplex_location)
    git_url = "https://github.com/nkon887/CellSeg_package.git"
    if not os.path.exists(cellseg_location):
        os.mkdir(cellseg_location)
        Repo.clone_from(git_url, cellseg_location)
    cmd = [f"conda activate myenv", f"pip install {multiplex_location}/Multiplex_package", "conda deactivate"]
    subprocess.run(" && ".join(cmd), shell=True)
    create_conda_environment_from_file("multiplex",
                                       f"{multiplex_location}/Multiplex_package/multiplex/envs/local/env_multiplex.yml")
    cmd = [f"conda activate multiplex", f"pip install {multiplex_location}/Multiplex_package", "conda deactivate"]
    subprocess.run(" && ".join(cmd), shell=True)
    create_conda_environment_from_file("cellsegsegmenter_cpu",
                                       f"{multiplex_location}/Multiplex_package/multiplex/envs/local/env_cellsegsegmenter_cpu.yml")
    cmd = [f"conda activate cellsegsegmenter_cpu", f"pip install {multiplex_location}/Multiplex_package", "conda deactivate"]
    subprocess.run(" && ".join(cmd), shell=True)
    cmd = [f"conda activate cellsegsegmenter_cpu", f"pip install {cellseg_location}", "conda deactivate"]
    subprocess.run(" && ".join(cmd), shell=True)
    create_conda_environment_from_file("cellsegsegmenter_gpu",
                                       f"{multiplex_location}/Multiplex_package/multiplex/envs/local/env_cellsegsegmenter_gpu.yml")
    cmd = [f"conda activate cellsegsegmenter_gpu", f"pip install {multiplex_location}/Multiplex_package", "conda deactivate"]
    subprocess.run(" && ".join(cmd), shell=True)
    cmd = [f"conda activate cellsegsegmenter_gpu", f"pip install {cellseg_location}", "conda deactivate"]
    subprocess.run(" && ".join(cmd), shell=True)


top_frame = tk.Frame(master)
bottom_frame = tk.Frame(master)
line = tk.Frame(master, height=1, width=400, bg="grey80", relief='groove')

# input_path = tk.Label(top_frame, text="WEB URL of the GITHUB Directory:")
# input_entry = tk.Entry(top_frame, text="https://github.com/nkon887/multiplex-staining.git", width=40)
# browse1 = tk.Button(top_frame, text="Browse", command=input)

destination_location = tk.StringVar()
download_path = tk.Label(bottom_frame, text="Download File Path:")
download_entry = tk.Entry(bottom_frame, width=40, textvariable=destination_location)
browse2 = tk.Button(bottom_frame, text="Browse", command=destination_browse)
begin_button = tk.Button(bottom_frame, text='Begin!', command=download)

top_frame.pack(side=tk.TOP)
line.pack(pady=10)
bottom_frame.pack(side=tk.BOTTOM)

# input_path.pack(pady=5)
# input_entry.pack(pady=5)
# browse1.pack(pady=5)

download_path.pack(pady=5)
download_entry.pack(pady=5)
browse2.pack(pady=5)

begin_button.pack(pady=20, fill=tk.X)

master.mainloop()
cmd = [f"conda activate myenv", "python -m multiplex"]
subprocess.run(" && ".join(cmd), shell=True)
