import subprocess
import threading
import time
import tkinter as tk
import tkinter.filedialog as filedialog


def run_shell_process(command, print_output=False):
    if print_output:
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


def look_for_env_and_unpack(tar_file_path, env_names, tar_env_dir):
    """
    Unpacks a Windows conda environment tarball (either conda-pack or manual),
    fixes nested folders, runs conda-unpack, and returns {env_name: env_dir_path}.
    """

    import os, tarfile, shutil, subprocess, time

    out = {}

    base = os.path.basename(tar_file_path)

    # 1) Detect which env this tar belongs to
    env_name = None
    for n in env_names:
        if n in base:
            env_name = n
            break

    if env_name is None:
        print(f"[ERROR] Tarball {base} does not match any expected env name.")
        return {}

    # 2) Define final environment target folder
    env_dir = base.replace(".tar.gz", "").replace(".tgz", "")
    env_dir_path = os.path.join(tar_env_dir, env_dir)

    # If exists from failed extraction, remove it first
    if os.path.exists(env_dir_path):
        shutil.rmtree(env_dir_path, ignore_errors=True)

    os.makedirs(env_dir_path, exist_ok=True)

    print(f"[INFO] Extracting {base} into {env_dir_path}")

    # ------------------------------------------------------------------
    # 3) Detect whether tar contains top-level folder or not
    # ------------------------------------------------------------------
    with tarfile.open(tar_file_path, "r:gz") as tf:
        members = tf.getmembers()

        # Extract top-level names
        top = {m.name.split("/")[0] for m in members}

        # Case A: conda-pack tarball → has NO top-level "env" folder
        # Known pattern: python.exe, Scripts/, DLLs/, etc. at root
        conda_pack_root = any(
            m.name in ("python.exe", "Scripts/activate.bat", "Scripts/conda-unpack.exe")
            for m in members
        )

        # Case B: manual tarball → contains a wrapping folder
        has_single_top_folder = len(top) == 1

        # ------------------------------------------------------------------
        # Extraction rules:
        # ------------------------------------------------------------------
        if conda_pack_root:
            # DIRECT extraction → into env_dir_path
            tf.extractall(env_dir_path)

        elif has_single_top_folder:
            # Manual tar: extract wrapper, then MOVE contents inside env_dir_path
            wrapper = list(top)[0]
            temp_extract = os.path.join(tar_env_dir, "__temp_extract__")
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract, ignore_errors=True)

            os.makedirs(temp_extract, exist_ok=True)
            tf.extractall(temp_extract)

            wrapper_path = os.path.join(temp_extract, wrapper)

            # Move wrapper/* → env_dir_path/
            for item in os.listdir(wrapper_path):
                shutil.move(os.path.join(wrapper_path, item), env_dir_path)

            shutil.rmtree(temp_extract, ignore_errors=True)

        else:
            # Fallback: extract everything into env_dir_path
            tf.extractall(env_dir_path)

    # Remove tarball after closing handles
    try:
        os.remove(tar_file_path)
    except Exception as e:
        print(f"[WARNING] Could not remove tarball: {e}")

    # ------------------------------------------------------------------
    # 4) Fix nested folder if somehow present (env/env/*)
    # ------------------------------------------------------------------
    nested = os.path.join(env_dir_path, env_dir)
    if os.path.isdir(nested):
        print("[FIX] Found nested folder → flattening...")
        for item in os.listdir(nested):
            shutil.move(os.path.join(nested, item), env_dir_path)
        shutil.rmtree(nested, ignore_errors=True)

    # ------------------------------------------------------------------
    # 5) Validate environment structure
    # ------------------------------------------------------------------
    scripts = os.path.join(env_dir_path, "Scripts")
    activate = os.path.join(scripts, "activate.bat")
    unpack_exe = os.path.join(scripts, "conda-unpack.exe")
    python_exe = os.path.join(env_dir_path, "python.exe")

    required = [scripts, activate, python_exe]

    if not all(os.path.exists(r) for r in required):
        print(f"[ERROR] Invalid environment after extraction: {env_dir_path}")
        return {}

    # ------------------------------------------------------------------
    # 6) Run conda-unpack
    # ------------------------------------------------------------------
    if os.path.exists(unpack_exe):
        cmd = " && ".join([
            f'cd "{env_dir_path}"',
            f'"{activate}"',
            f'"{unpack_exe}"',
            f'"{activate}" & conda deactivate'  # safe fallback for older envs
        ])
        subprocess.run(cmd, shell=True)
    else:
        print("[WARNING] conda-unpack.exe not found → skipping.")

    print(f"[INFO] Environment ready: {env_dir_path}")

    out[env_name] = env_dir_path
    return out


def look_for_env_and_report(env_dir_path, env_names):
    """
    Validates an extracted environment and runs conda-unpack only if correct.
    Returns the env_name if environment is valid, else ''.
    """

    import os

    env_name = None

    # match env by name in path
    for name in env_names:
        if name in os.path.basename(env_dir_path):
            env_name = name
            break

    if not env_name:
        return ""

    # --- Validate environment ---
    scripts = os.path.join(env_dir_path, "Scripts")
    activate = os.path.join(scripts, "activate.bat")
    unpack_exe = os.path.join(scripts, "conda-unpack.exe")
    python_exe = os.path.join(env_dir_path, "python.exe")

    # conda-pack windows environments ALWAYS have these:
    required = [scripts, activate, python_exe]

    if not all(os.path.exists(r) for r in required):
        print(f"[ERROR] {env_dir_path} is not a valid conda environment")
        return ""

    # --- Run conda-unpack ---
    if os.path.exists(unpack_exe):
        cmd = " && ".join([
            f'cd "{env_dir_path}"',
            f'"{activate}"',
            f'"{unpack_exe}"',
            r'Scripts\deactivate.bat'
        ])
        subprocess.run(cmd, shell=True)
    else:
        print("[WARNING] conda-unpack not found → skipping.")

    print(f"The environment {env_name} is set")
    return env_name