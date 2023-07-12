# multiplex.setup_logger.py
import logging
import sys
# create logger with 'pipelineGUI'
logger = logging.getLogger("pipelineGUI")
logger.setLevel(logging.INFO)
# create console handler with a higher log level
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s | %(msecs)d | %(name)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
stdout_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stdout_handler)
