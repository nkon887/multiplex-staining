import glob, os
import helpertools as ht
tar_env_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tar_envs")
list_tar_files_paths = []
if os.path.exists(tar_env_dir) and len(os.listdir(tar_env_dir)) !=  0:
    list_tar_files_paths = glob.glob(os.path.join(tar_env_dir,"*.tar.gz"))
else:
    print(f"The directory {tar_env_dir} doesn't exist (removed) or it is empty. Please check it and change it. Create and or add tar gz files to the directory {tar_env_dir} and rerun this script again")
env_dir_paths={}
env_names=["multiplex", "cellsegsegmenter_gpu", "cellsegsegmenter_cpu"]
if len(list_tar_files_paths) !=0:
    for tar_file_path in list_tar_files_paths:
        env_dir_paths = ht.look_for_env_and_unpack(tar_file_path, env_names, tar_env_dir)
    print("All environments are now successfully set")
else:
    print(f"There are no tar.gz files to find in the directory {tar_env_dir}. Please check it and rerun this script again")
env_dir_path_multiplex = ""
multiplex_env = env_names[0]
if multiplex_env in env_dir_paths:
    env_dir_path_multiplex = env_dir_paths[multiplex_env]
if env_dir_path_multiplex != "":
    ht.run_shell_process([f'cd "{env_dir_path_multiplex}"', r'.\Scripts\activate.bat', f'python -m {multiplex_env} --path {tar_env_dir}'])
else:
    print(f"The environment {multiplex_env} can't be found")