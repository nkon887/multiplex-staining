import os

import helpertools as ht

tar_env_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tar_envs")
env_names=["multiplex", "cellsegsegmenter_gpu", "cellsegsegmenter_cpu"]
list_subfolder_paths=[]
if os.path.exists(tar_env_dir) and len(os.listdir(tar_env_dir)) !=  0:
    list_subfolder_paths = [f.path for f in os.scandir(tar_env_dir)]
else:
    print(f"The directory {tar_env_dir} doesn't exist (removed) or it is empty. Please check it and change it. Rerun the installation using {install.py} and rerun this script again")
env_dir_paths={}
if len(list_subfolder_paths) !=0:
    for subfolder_file_path in list_subfolder_paths:
        env = ht.look_for_env_and_report(subfolder_file_path, env_names, tar_env_dir)
        if env !="":
            env_dir_paths[env] = subfolder_file_path
    if len(env_dir_paths)==3:
        print("All environments are already successfully set")
        multiplex_env = env_names[0]
        env_dir_path_multiplex = env_dir_paths[multiplex_env]
        ht.run_shell_process([f'cd "{env_dir_path_multiplex}"', r'.\Scripts\activate.bat',
                                  f'python -m {multiplex_env} --path {tar_env_dir}'])
    else:
        envs_set=list(env_dir_paths.keys())
        diff=list(set(env_names) - set(envs_set))
        print("The following environments are not set:" + ''.join(str(x) for x in diff) + ", please check it and rerun the script again")
else:
    print(f"There is no subfolder to find in the directory {tar_env_dir}. Please check it and rerun this script again")