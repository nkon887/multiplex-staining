import os
import helpertools as ht


# -------------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------------
TAR_ENV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tar_envs")
ENV_NAMES = ["multiplex", "cellsegsegmenter_gpu", "cellsegsegmenter_cpu"]


# -------------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------------
def list_subdirectories(path):
    """Return full paths of subdirectories inside a directory."""
    if not os.path.isdir(path):
        return []
    return [entry.path for entry in os.scandir(path) if entry.is_dir()]


def report_missing(message):
    """Print error messages."""
    print(f"[ERROR] {message}")


# -------------------------------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------------------------------

# --- 1. Check tar_envs directory ---
subfolders = list_subdirectories(TAR_ENV_DIR)
if not subfolders:
    report_missing(
        f"Directory '{TAR_ENV_DIR}' is missing or contains no subfolders.\n"
        f"Run install.py to create environments and try again."
    )
    raise SystemExit


# --- 2. Detect existing environments inside subfolders ---
env_dir_paths = {}  # { env_name: folder_path }

for folder_path in subfolders:
    detected_env = ht.look_for_env_and_report(folder_path, ENV_NAMES)
    if detected_env:
        env_dir_paths[detected_env] = folder_path


# --- 3. Check if all required envs are present ---
if len(env_dir_paths) == len(ENV_NAMES):
    print("[OK] All environments are already correctly set.")

    multiplex_env = ENV_NAMES[0]
    multiplex_env_path = env_dir_paths[multiplex_env]

    # Activate and run the multiplex entrypoint
    ht.run_shell_process([
        f'cd "{multiplex_env_path}"',
        r'.\Scripts\activate.bat',
        f'python -m {multiplex_env} --path "{TAR_ENV_DIR}"'
    ])

else:
    found = sorted(env_dir_paths.keys())
    missing = sorted(set(ENV_NAMES) - set(found))

    report_missing(
        "Some required environments are missing.\n"
        f"Found:   {found}\n"
        f"Missing: {missing}\n"
        "Please fix the installation and rerun this script."
    )
    raise SystemExit
