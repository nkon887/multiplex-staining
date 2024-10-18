#! /usr/bin/env python
import os.path
import subprocess
import threading
import time

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
            subprocess.run(f"conda env create -f {requirements_file}", shell=True)
        for package in packages_to_install:
            command = [f"conda activate {env_name}", f"pip install {package}", "conda deactivate"]
            run_shell_process(command)
        print(f"Conda environment {env_name} created.")
    else:
        print(f"{env_exists} Conda environment {env_name} already exists.")

def install(environments):
    for env in environments:
        create_conda_environment(f"{env}",
                                 f"{environments[env]['yml_file']}", environments[env]["packages_to_install"])
    return "The installation is complete. The environments are set up. The multiplex pipeline is ready for use"

def run_shell_process(command):
    subprocess.run(" && ".join(command), shell=True)

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
multiplex_repo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Multiplex_package")
cellseg_repo_dir = os.path.join(pipeline_dir_path,"CellSeg_package")
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
