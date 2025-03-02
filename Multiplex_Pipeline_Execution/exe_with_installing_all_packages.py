#! /usr/bin/env python
import os.path
import subprocess
import threading
import time

from helpertools import run_shell_process


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
            comm = f"conda env create -f '{requirements_file}'"
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


pipeline_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
im_jy_repo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "im-jy-package/target")
multiplex_repo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Multiplex_package")
cellseg_repo_dir = os.path.join(pipeline_dir_path, "CellSeg_package")
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
envs = {
    "myenv": {"packages_to_install": [f"{multiplex_repo_dir}", "gdown", "pandas", "pytest", "yargs"], "yml_file": " "},
    "multiplex": {"packages_to_install": [f"{multiplex_repo_dir}"],
                  "yml_file": f"{multiplex_repo_dir}/multiplex/envs/local/env_multiplex.yml"},
    "cellsegsegmenter_cpu": {"packages_to_install": [f"{multiplex_repo_dir}", f"{cellseg_repo_dir}"],
                             "yml_file": f"{multiplex_repo_dir}/multiplex/envs/local/env_cellsegsegmenter_cpu.yml"},
    "cellsegsegmenter_gpu": {"packages_to_install": [f"{multiplex_repo_dir}", f"{cellseg_repo_dir}"],
                             "yml_file": f"{multiplex_repo_dir}/multiplex/envs/local/env_cellsegsegmenter_gpu.yml"}
}
install_processing_please_wait(envs)
cmd = [f"conda activate myenv", "python -m multiplex"]
run_shell_process(cmd)
