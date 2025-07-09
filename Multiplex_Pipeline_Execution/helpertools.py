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

def look_for_env_and_unpack(tar_file_path, env_names, tar_env_dir):
    import os
    env_dir_paths = {}
    if any(env_name in tar_file_path for env_name in env_names):
        env_dir = (os.path.splitext(os.path.basename(tar_file_path))[0]).split('.')[0]
        env_dir_path = os.path.join(tar_env_dir, env_dir)
        env_dir_paths[env_dir] = env_dir_path
        command = " && ".join(
            [f'mkdir "{env_dir_path}"', f'tar -xzf "{tar_file_path}" -C  "{env_dir_path}"', f'cd "{env_dir_path}"',
             r".\Scripts\activate.bat", r".\Scripts\conda-unpack.exe", r".\Scripts\deactivate.bat", f'del "{tar_file_path}"'])
        subprocess.run(command, shell=True)
        print(f"The environment {env_dir} is set with the path {env_dir_path}")
    else:
        print("There are tar.gz files but they are not assignable to any of env required")
    return env_dir_paths
def look_for_env_and_report(subfolder_file_path, env_names):
    out = ""
    for env_name in env_names:
        if env_name in subfolder_file_path:
            env_dir_path = subfolder_file_path
            command = " && ".join(
            [f'cd "{env_dir_path}"', r".\Scripts\activate.bat", r".\Scripts\conda-unpack.exe", r".\Scripts\deactivate.bat"])
            subprocess.run(command, shell=True)
            print(f"The environment {env_name} is set with the path {env_dir_path}")
            out=env_name
    return out