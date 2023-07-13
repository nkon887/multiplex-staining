# multiplex.results_output.py
import os
import errno
import shutil
import multiplex.setup_logger
import logging
import multiplex.helpertools as ht

# multiplex.results_output.py creates its own logger, as a sub logger to 'multiplex.main'
logger = logging.getLogger('multiplex.main.resultsOutput')


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
                logger.error('Directory not copied. Error: %s' % e)
        folders = os.listdir(self.results_output_folder)
        if len(folders) != 0:
            for subfolder in folders:
                for seg_file in os.listdir(self.dapi_seg_binary_size_correct_dir):
                    if str(subfolder) in str(seg_file):
                        logger.info(f"Processing the subfolder {seg_file}")
                        shutil.copy(ht.correct_path(self.dapi_seg_binary_size_correct_dir, seg_file),
                                    ht.correct_path(self.results_output_folder, subfolder, seg_file))
                for merge_subfolder in os.listdir(self.merge_channels_dir):
                    if str(subfolder) in str(merge_subfolder):
                        merge_subfolder_path = ht.correct_path(self.merge_channels_dir, merge_subfolder)
                        logger.info(f"Processing the subfolder {merge_subfolder}")
                        for merge_file in os.listdir(merge_subfolder_path):
                            save_dir = ht.correct_path(self.results_output_folder, subfolder, os.path.basename(self.merge_channels_dir)[3:])
                            if not os.path.exists(save_dir):
                                os.makedirs(save_dir)
                            shutil.copy(ht.correct_path(self.merge_channels_dir, merge_subfolder, merge_file),
                                        ht.correct_path(save_dir, merge_file))
        else:
            logger.warning("The target folder is empty")

        for folder in os.listdir(self.main_dir):
            if str(folder) not in str(self.results_output_folder):
                subfolder_path = ht.correct_path(self.main_dir, folder)
                if os.path.isdir(subfolder_path):
                    try:
                        shutil.rmtree(subfolder_path)
                    except OSError as e:
                        logger.error("Error: %s - %s." % (e.filename, e.strerror))
