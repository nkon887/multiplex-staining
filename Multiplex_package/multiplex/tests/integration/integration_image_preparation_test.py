# integration_image_preparation_test.py
import unittest

from tkinter import *
from multiplex import gui
from multiplex import helpertools as ht
import os


class TestBasic(unittest.TestCase):
    def setUp(self):
        # Load test data
        window = Tk()
        self.pipeline_steps = ["", "STITCHING", "DATACHECK", "ALIGNMENT", "REALIGNMENT", "CROPPING",
                               "BACKGROUNDADJUSTMENT",
                               "MERGING_CHANNELS", "DAPISEGMENTATION", "OUTPUT"]
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
        root = os.path.dirname(os.path.realpath(__file__))
        self.main_py_PATH = os.path.join(root, 'main.py')
        self.macro_py_PATH = os.path.join(root, 'macro.py')
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
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[3],
                 self.command_arguments[2]: self.dapiseg_steps[1]},
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.dapiseg_steps[2]},
                {self.command_arguments[0]: self.packages[0], self.command_arguments[1]: list(self.envs)[0],
                 self.command_arguments[2]: self.pipeline_steps[8]}],
            (self.pipeline_steps[9], self.pipeline_steps[0], self.subfolders_list[2], self.subfolders_list[5]): [
                {self.command_arguments[0]: self.packages[1], self.command_arguments[1]: list(self.envs)[1],
                 self.command_arguments[2]: self.pipeline_steps[9]}]
        }

        self.app = gui.App(window, self.pipeline_params, self.dapiseg_steps, self.subfolders_list,
                           self.realignment_subfolder_list, self.dapiseg_subfolder_list, self.command_arguments,
                           self.packages, self.envs, self.main_work_dir, self.main_py_PATH, self.macro_py_PATH)
        window.title("Running the Steps of Multiplex Pipeline")
        window.geometry('880x510')
        window.config(background="black")
        window.mainloop()

    def test_buttons_names(self):
        self.assertEqual([list(self.app.buttons)[i][0] for i in range(len(list(self.app.buttons)))],
                         ["STITCHING", "DATACHECK", "ALIGNMENT", "REALIGNMENT", "CROPPING",
                          "BACKGROUNDADJUSTMENT", "MERGING_CHANNELS", "DAPISEGMENTATION", "OUTPUT"])

    def test_existence_of_button(self):
        button = list(self.app.buttons.items())[0]
        self.assertEqual(str(button[0][0]), 'STITCHING')
        self.assertEqual(str(button[0][1]), '')


if __name__ == '__main__':
    unittest.main()
