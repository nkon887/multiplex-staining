#! /usr/bin/env python
import os
import helpertools as ht


start_pipeline_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
im_jy_repo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "im-jy-package/target")
tar_env_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tar_envs")
command = "echo %FIJIPATH%"
path_to_fiji_act = ht.run_shell_process(command, True)
path_to_fiji = os.path.dirname(path_to_fiji_act.decode('UTF-8'))
import shutil
path_to_fiji_module = os.path.join(path_to_fiji, "jars/Lib")
if not os.path.exists(path_to_fiji_module):
    os.mkdir(path_to_fiji_module)
fiji_file="im-jy-package-0.1.0-SNAPSHOT.jar"
path_to_fiji_module_file_target = os.path.join(path_to_fiji_module, fiji_file)
path_to_fiji_module_file_source = os.path.join(im_jy_repo_dir, fiji_file)
if not os.path.exists(path_to_fiji_module_file_target):
    shutil.copyfile(path_to_fiji_module_file_source, path_to_fiji_module_file_target)
else:
    os.remove(path_to_fiji_module_file_target)
    shutil.copyfile(path_to_fiji_module_file_source, path_to_fiji_module_file_target)

import glob
list_tar_files_paths = []
env_dir_paths ={}
if os.path.exists(tar_env_dir) and len(os.listdir(tar_env_dir)) !=  0:
    list_tar_files_paths = glob.glob(os.path.join(tar_env_dir,"*.tar.gz"))
else:
    print(f"The directory {tar_env_dir} doesn't exist (removed) or it is empty. Please check it and change it. Create and or add tar gz files to the directory {tar_env_dir} and rerun this script again")
env_names=["multiplex", "cellsegsegmenter_gpu", "cellsegsegmenter_cpu"]
if len(list_tar_files_paths) !=0:
    for tar_file_path in list_tar_files_paths:
        env_dir_paths = ht.look_for_env_and_unpack(tar_file_path, env_names,tar_env_dir)
    print("All environments are now successfully set")
else:
    print(f"There are no tar.gz files to find in the directory {tar_env_dir}. Please check it and rerun this script again")