#! /usr/bin/env python
import os
import subprocess
from helpertools import run_shell_process


def create_conda_environment(env_name):
    env_exists = False
    packages_to_install = ["gdown", "pandas", "pytest", "yargs",
                           "\"git+https://github.com/nkon887/multiplex-staining.git#multiplex&subdirectory"
                           f"=Multiplex_package\""]
    try:
        subprocess.run(f"conda activate {env_name}", shell=True, check=True)
        env_exists = True
    except subprocess.CalledProcessError as e:
        pass
    if not env_exists:
        subprocess.run(
            ''.join([f"conda create -y --name {env_name} python=3.10 "
                     f"&& conda activate {env_name}",
                     ''.join([f" && pip install {package}" for package in packages_to_install])]),
            shell=True)
        print(f"Conda environment {env_name} created.")
    else:
        print(f"{env_exists} Conda environment {env_name} already exists.")


env_name = "myenv"
create_conda_environment(env_name)
pipeline_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
im_jy_repo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "im-jy-package/target")
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
cmd = [f"conda activate {env_name}", "python -m multiplex"]
subprocess.run(" && ".join(cmd), shell=True)
