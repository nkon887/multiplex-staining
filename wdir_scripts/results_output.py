import os
import errno
import sys
import config
import time
import pythontools as pt
import shutil


class ResultsOutput:
    def __init__(self, bg_adjust_dir, merge_channels_dir, dapi_seg_binary_size_correct_dir, results_output_folder):
        self.bg_adjust_dir = bg_adjust_dir
        self.merge_channels_dir = merge_channels_dir
        self.dapi_seg_binary_size_correct_dir = dapi_seg_binary_size_correct_dir
        self.results_output_folder = results_output_folder

    def process(self):
        try:
            # if path already exists, remove it before copying with copytree()
            if os.path.exists(self.results_output_folder):
                shutil.rmtree(self.results_output_folder)
                shutil.copytree(self.bg_adjust_dir, self.results_output_folder, copy_function=shutil.copy2)
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(self.bg_adjust_dir, self.results_output_folder)
            else:
                print('Directory not copied. Error: %s' % e)
        folders = os.listdir(self.results_output_folder)
        #if os.listdir(folders):
            #for subfolder in folders:
                #for seg_subfolder in os.listdir(self.dapi_seg_binary_size_correct_dir):
                    #if str(subfolder) in str(seg_subfolder):

        #else:
            #print("Empty")

