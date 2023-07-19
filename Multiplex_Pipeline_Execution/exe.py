#! /usr/bin/env python
import subprocess


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
            f"install gdown && pip install pandas && pip install pytest && pip install yargs && "
            f"pip install \"git+https://github.com/nkon887/multiplex-staining.git#multiplex&subdirectory"
            f"=Multiplex_package\"", shell=True)
        print(f"Conda environment {env_name} created.")
    else:
        print(f"{env_exists} Conda environment {env_name} already exists.")


env_name = "myenv"
create_conda_environment(env_name)
cmd = [f"conda activate {env_name}", "python -m multiplex"]
subprocess.run(" && ".join(cmd), shell=True)
