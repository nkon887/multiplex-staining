#! /usr/bin/env python
import os
import glob
import shutil
import helpertools as ht


# -------------------------------------------------------------------------
# PATH SETUP
# -------------------------------------------------------------------------
def safe_decode(value):
    """Decode a byte-string safely to UTF-8."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def ensure_directory(path):
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# Determine root directories
START_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
REPO_IM_JY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "im-jy-package", "target")
TAR_ENV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tar_envs")

# -------------------------------------------------------------------------
# FIND FIJI PATH
# -------------------------------------------------------------------------
command = "echo %FIJIPATH%"
raw = ht.run_shell_process(command, print_output=True)
path_to_fiji = os.path.dirname(safe_decode(raw).strip())

if not path_to_fiji or not os.path.exists(path_to_fiji):
    raise RuntimeError(f"FIJI path not found or invalid: '{path_to_fiji}'")

# -------------------------------------------------------------------------
# INSTALL im-jy PACKAGE JAR INTO FIJI
# -------------------------------------------------------------------------
FIJI_LIB_DIR = os.path.join(path_to_fiji, "jars", "Lib")
FIJI_JAR_NAME = "im-jy-package-0.1.0-SNAPSHOT.jar"
TARGET_JAR_PATH = os.path.join(FIJI_LIB_DIR, FIJI_JAR_NAME)
SOURCE_JAR_PATH = os.path.join(REPO_IM_JY_DIR, FIJI_JAR_NAME)

ensure_directory(FIJI_LIB_DIR)

try:
    if os.path.exists(TARGET_JAR_PATH):
        os.remove(TARGET_JAR_PATH)

    shutil.copyfile(SOURCE_JAR_PATH, TARGET_JAR_PATH)
    print(f"[OK] Copied {FIJI_JAR_NAME} into FIJI: {TARGET_JAR_PATH}")

except Exception as e:
    print(f"[ERROR] Failed to install JAR into FIJI: {e}")

# -------------------------------------------------------------------------
# PROCESS CONDA ENV TARS
# -------------------------------------------------------------------------
tar_files = glob.glob(os.path.join(TAR_ENV_DIR, "*.tar.gz"))

if not os.path.exists(TAR_ENV_DIR) or not tar_files:
    print(
        f"[ERROR] Directory '{TAR_ENV_DIR}' is missing or contains no .tar.gz files.\n"
        f"Add environment tarballs and rerun this script."
    )
else:
    env_names = ["multiplex", "cellsegsegmenter_gpu", "cellsegsegmenter_cpu"]
    unpack_results = {}

    for tar_path in tar_files:
        try:
            result = ht.look_for_env_and_unpack(
                tar_path,
                env_names,
                TAR_ENV_DIR
            )
            unpack_results.update(result)
        except Exception as e:
            print(f"[ERROR] Failed processing {tar_path}: {e}")

    print("[OK] All environments have been successfully set up.")
    print("Unpacked environments:", unpack_results)
