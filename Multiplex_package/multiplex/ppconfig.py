import multiplex.helpertools as ht
import os
import logging
import multiplex.setup_logger

# multiplex.ppconfig.py creates its own logger, as a sub logger to 'multiplex'
logger = logging.getLogger('multiplex.ppconfig')


class PIPELINEConfig:
    def __init__(self):
        self.info_txt_file = 'infos.txt'
        self.metadata_file = 'metadata.csv'
        self.csv_ext = '.csv'
        self.dates_number = 20
        self.input_dates = 'dates'
        self.standard_search_terms = [" - Copy", "-Background subtraction", "_ORG", " "]
        length_standard_search_terms = len(self.standard_search_terms)
        self.standard_replacements = ["" if i < (length_standard_search_terms - 2) else "_" for i in
                                      range(length_standard_search_terms)]
        self.dapi_str = "dapi"
        self.stack_name = "Stack"
        self.tiff_ext = ".tif"
        self.cropped_suffix = "_Cropped"
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
        # self.pipeline_steps = ["", "STITCH", "DATACHECK", "ALIGN", "CROP",
        #                       "AUTOCROP", "ADJUST_BG", "MERGE_CHANNELS",
        #                       "DAPISEG",
        #                       "OUTPUT", "BG_MERGE_DAPISEG"]
        self.pipeline_steps = ["", "STITCH", "DATACHECK", "ALIGN/REALIGN", "CROP",
                               "ADJUST_BG", "MERGE_CHANNELS",
                               "DAPISEG",
                               "OUTPUT", "FAST_BUTTON"]

        self.cropping_experimental_steps = ["cropping_with_coords", "automatic_cropping_with_coords"]
        self.merge_channels_steps = ["setting_merge_channels_parameters"]
        self.bg_steps = ["setting_bg_parameters"]
        self.dapiseg_steps = ["setDapiSegParams", "preparation_dapiSeg", "main_dapiSeg", "postprocessing_dapiSeg"]
        self.fast_button_step = ["fast_button"]
        self.command_arguments = ["package", "env", "step"]
        self.packages = ["fiji", "python"]
        root = os.path.dirname(os.path.realpath(__file__))
        self.main_py_PATH = os.path.join(root, 'main.py')
        self.macro_py_PATH = os.path.join(root, 'macro.py')
        ENV_DIRECTORY = os.path.join(root, 'envs')
        if not os.path.exists(ENV_DIRECTORY):
            os.makedirs(ENV_DIRECTORY)
        ENVMULTIPLEX_PATH = os.path.join(ENV_DIRECTORY, 'env_multiplex.yml')
        ENVCELLSEGSEGMENTERGPU_PATH = os.path.join(ENV_DIRECTORY, 'env_cellsegsegmenter_gpu.yml')
        ENVCELLSEGSEGMENTERCPU_PATH = os.path.join(ENV_DIRECTORY, 'env_cellsegsegmenter_cpu.yml')
        self.conda_cellseg_envs = ["cellsegsegmenter_gpu", "cellsegsegmenter_cpu"]
        self.envs = {"": ["", ""],
                     "multiplex": [ENVMULTIPLEX_PATH, 'https://drive.google.com/uc?id'
                                                      '=1TnbvKc1FSsFcNmRl_MwssJEq9GLrzBDz&export=download'],
                     self.conda_cellseg_envs[0]: [ENVCELLSEGSEGMENTERGPU_PATH,
                                                  'https://drive.google.com/uc?id=1pU7DgYOPHoWi9bawMvEH94GnYEBya2YM'
                                                  '&export=download'],
                     self.conda_cellseg_envs[1]: [ENVCELLSEGSEGMENTERCPU_PATH,
                                                  'https://drive.google.com/uc?id=1jyJwnx6CcC9Mkgjd_dfl7nHLXPjW7FdT'
                                                  '&export=download']}
        # pipeline params are defined as follows:
        #   execution step, steps to be switched on, subfolders as condition to be switched on, subfolders to create after step execution, for each substep constructor package, environment and step
        self.pipeline_params = {
            (self.pipeline_steps[1], self.pipeline_steps[2], "", self.subfolders_list[0]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[1]}],
            (self.pipeline_steps[2], self.pipeline_steps[3], self.subfolders_list[0], self.subfolders_list[0]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.pipeline_steps[2]}],
            (self.pipeline_steps[3],
             self.pipeline_steps[4] + "," + self.pipeline_steps[5],
             self.subfolders_list[0],
             self.realignment_subfolder_list[0] + "," + self.subfolders_list[1]): [
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: "", self.command_arguments[2]:
                    self.pipeline_steps[3]},
                # {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                # self.command_arguments[2]: "REALIGNMENT"}
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[3]}
            ],
            # (self.pipeline_steps[4], self.pipeline_steps[5] + "," + self.pipeline_steps[6],
            # self.realignment_subfolder_list[0] + ","
            # + self.subfolders_list[1], self.subfolders_list[1]): [
            #    {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
            #     self.command_arguments[2]: self.pipeline_steps[4]}],
            (self.pipeline_steps[4], self.pipeline_steps[5] + "," + self.pipeline_steps[9], self.subfolders_list[1],
             self.subfolders_list[1]):
                [
                    [
                        {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                         self.command_arguments[2]: self.pipeline_steps[4]}
                    ],
                    [
                        {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                         self.command_arguments[2]: self.cropping_experimental_steps[0]},
                        {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                         self.command_arguments[2]: self.pipeline_steps[4]}
                    ],
                    [
                        {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                         self.command_arguments[2]: self.cropping_experimental_steps[1]}
                    ]

                ],
            # (self.pipeline_steps[5], self.pipeline_steps[6] + "," + self.pipeline_steps[10], self.subfolders_list[1],
            # self.subfolders_list[1]): [
            #    {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
            #     self.command_arguments[2]: self.cropping_experimental_steps[0]},
            #    {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
            #     self.command_arguments[2]: self.pipeline_steps[4]}],
            (self.pipeline_steps[5],
             self.pipeline_steps[6] + "," + self.pipeline_steps[7] + "," + self.pipeline_steps[8],
             self.subfolders_list[1], self.subfolders_list[2]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.bg_steps[0]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[5]}],
            (self.pipeline_steps[6], self.pipeline_steps[5], self.subfolders_list[2], self.subfolders_list[3]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.merge_channels_steps[0]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[6]}],
            (self.pipeline_steps[7], self.pipeline_steps[5], self.subfolders_list[2], self.dapiseg_subfolder_list[3]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[0]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[1]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[3],
                 self.command_arguments[2]: self.dapiseg_steps[2]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[3]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[7]}],
            (self.pipeline_steps[8], self.pipeline_steps[0], self.subfolders_list[2], self.subfolders_list[5]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.pipeline_steps[8]}],
            (self.pipeline_steps[9],
             self.pipeline_steps[5] + "," + self.pipeline_steps[6] + "," + self.pipeline_steps[7] + "," +
             self.pipeline_steps[8], self.subfolders_list[1],
             self.subfolders_list[2] + "," + self.subfolders_list[3]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.fast_button_step[0]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[5]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[6]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[1]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[3],
                 self.command_arguments[2]: self.dapiseg_steps[2]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[3]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[7]}
            ]
        }
