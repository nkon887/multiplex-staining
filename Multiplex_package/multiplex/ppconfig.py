import multiplex.helpertools as ht
import os


class PIPELINEConfig:
    def __init__(self):
        self.info_txt_file = 'infos.txt'
        self.metadata_file = 'metadata.csv'
        self.dates_number = 20
        self.input_dates = 'dates'
        self.standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
        length_standard_search_terms = len(self.standard_search_terms)
        self.standard_replacements = ["" if i < (length_standard_search_terms - 2) else "_" for i in
                                      range(length_standard_search_terms)]
        self.dapi_str = "dapi"
        self.stack_name = "Stack"
        self.tiff_ext = ".tif"
        self.main_work_dir = "workingDir"
        self.subfolders_list = [ht.correct_path(self.main_work_dir, str(i + 1).zfill(2) + "_" + subfolder) for
                                i, subfolder in
                                enumerate(["input", "alignment", "bg_processed", "mergedChannels", "dapi_seg",
                                           "results_output"])]
        self.dapiseg_subfolder_list = [ht.correct_path(self.subfolders_list[4], str(i + 1).zfill(2) + "_" + subfolder)
                                       for i, subfolder in
                                       enumerate(
                                           ["input_folder", "seg_output", "dapi_seg_binary", "binary_size_correct"])]
        self.realignment_subfolder_list = [
            ht.correct_path(self.main_work_dir, str(2).zfill(2) + "_" + str(i + 1).zfill(2) + "_" + subfolder) for
            i, subfolder in
            enumerate(["input_to_precrop", "stacks", "cropped_input"])]
        self.pipeline_steps = ["", "STITCHING", "DATACHECK", "ALIGNMENT", "REALIGNMENT", "CROPPING",
                               "BACKGROUNDADJUSTMENT",
                               "MERGING_CHANNELS", "DAPISEGMENTATION", "OUTPUT"]
        self.dapiseg_steps = ["preparation_dapiSeg", "main_dapiSeg", "postprocessing_dapiSeg"]
        self.command_arguments = ["package", "env", "step"]
        self.packages = ["fiji", "python"]
        root = os.path.dirname(os.path.realpath(__file__))
        self.main_py_PATH = os.path.join(root, 'main.py')
        self.macro_py_PATH = os.path.join(root, 'macro.py')
        import gdown
        root = os.path.dirname(os.path.realpath(__file__))
        ENV_DIRECTORY = os.path.join(root, 'envs')
        if not os.path.exists(ENV_DIRECTORY):
            os.makedirs(ENV_DIRECTORY)
        ENVMULTIPLEX_PATH = os.path.join(ENV_DIRECTORY, 'env_multiplex.yml')
        ENVCELLSEGSEGMENTER_PATH = os.path.join(ENV_DIRECTORY, 'env_cellsegsegmenter.yml')
        for url, path in zip(['https://drive.google.com/uc?id=1TnbvKc1FSsFcNmRl_MwssJEq9GLrzBDz&export=download',
                              'https://drive.google.com/uc?id=1hjerdMIh9ijeLjgQ0VADBtbU73BM1f0_&export=download'],
                             [ENVMULTIPLEX_PATH, ENVCELLSEGSEGMENTER_PATH]):
            if not os.path.exists(path):
                gdown.download(url, path, quiet=False)
        self.envs = {"": "", "multiplex": ENVMULTIPLEX_PATH, "cellsegsegmenter": ENVCELLSEGSEGMENTER_PATH}
        self.pipeline_params = {
            (self.pipeline_steps[1], self.pipeline_steps[2], "", self.subfolders_list[0]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[1]}],
            (self.pipeline_steps[2], self.pipeline_steps[3], self.subfolders_list[0], self.subfolders_list[0]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.pipeline_steps[2]}],
            (self.pipeline_steps[3], self.pipeline_steps[4] + "," + self.pipeline_steps[5], self.subfolders_list[0],
             self.realignment_subfolder_list[0] + "," + self.subfolders_list[1]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: "", self.command_arguments[2]:
                    self.pipeline_steps[3]}],
            (self.pipeline_steps[4], self.pipeline_steps[5], self.realignment_subfolder_list[0] + ","
             + self.subfolders_list[1], self.subfolders_list[1]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[4]}],
            (self.pipeline_steps[5], self.pipeline_steps[6], self.subfolders_list[1], self.subfolders_list[1]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[5]}],
            (self.pipeline_steps[6],
             self.pipeline_steps[7] + "," + self.pipeline_steps[8] + "," + self.pipeline_steps[9],
             self.subfolders_list[1], self.subfolders_list[2]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[6]}],
            (self.pipeline_steps[7], self.pipeline_steps[0], self.subfolders_list[2], self.subfolders_list[3]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[7]}],
            (self.pipeline_steps[8], self.pipeline_steps[0], self.subfolders_list[2], self.dapiseg_subfolder_list[3]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[0]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[2],
                 self.command_arguments[2]: self.dapiseg_steps[1]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[2]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[8]}],
            (self.pipeline_steps[9], self.pipeline_steps[0], self.subfolders_list[2], self.subfolders_list[5]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.pipeline_steps[9]}]
        }
