import os
import errno
import sys
import config
import time
import pythontools as pt
import shutil


class ResultsOutput:
    def __init__(self, main_dir, bg_adjust_dir, merge_channels_dir, dapi_seg_binary_size_correct_dir,
                 results_output_folder):
        self.main_dir = main_dir
        self.bg_adjust_dir = bg_adjust_dir
        self.merge_channels_dir = merge_channels_dir
        self.dapi_seg_binary_size_correct_dir = dapi_seg_binary_size_correct_dir
        self.results_output_folder = results_output_folder

    def process(self):
        try:
            # if path already exists, remove it before copying with copytree()
            if os.path.exists(self.results_output_folder) and len(os.listdir(self.results_output_folder)) == 0:
                shutil.rmtree(self.results_output_folder)
                shutil.copytree(self.bg_adjust_dir, self.results_output_folder, copy_function=shutil.copy2)
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(self.bg_adjust_dir, self.results_output_folder)
            else:
                print('Directory not copied. Error: %s' % e)
        folders = os.listdir(self.results_output_folder)
        if len(folders) != 0:
            for subfolder in folders:
                for seg_file in os.listdir(self.dapi_seg_binary_size_correct_dir):
                    if str(subfolder) in str(seg_file):
                        print(seg_file)
                        shutil.copy(os.path.join(self.dapi_seg_binary_size_correct_dir, seg_file),
                                    os.path.join(self.results_output_folder, subfolder, seg_file))
                for merge_subfolder in os.listdir(self.merge_channels_dir):
                    if str(subfolder) in str(merge_subfolder):
                        print(merge_subfolder)
                        for merge_file in os.listdir(os.path.join(self.merge_channels_dir, merge_subfolder)):
                            shutil.copy(os.path.join(self.merge_channels_dir, merge_subfolder, merge_file),
                                        os.path.join(self.results_output_folder, subfolder, merge_file))
        else:
            print("The folder is target folder is empty")
        for folder in os.listdir(self.main_dir):
            if folder not in self.results_output_folder:
                subfolder_path = os.path.join(self.main_dir, folder)
                try:
                    shutil.rmtree(subfolder_path)
                except OSError as e:
                    print("Error: %s - %s." % (e.filename, e.strerror))


def main():
    # Calling the ResultsOutput class function
    ResultsOutput(config.working_dir, config.bg_adjust_dir, config.merge_channels_dir,
                  config.dapi_seg_binary_size_correct_dir,
                  config.results_output_folder).process()


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nDuration of the program execution:")
    print(pt.convert(end_time - start_time))
