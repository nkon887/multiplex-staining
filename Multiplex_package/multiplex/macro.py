# @String base_dir
# @String target_dir
# @String working_dir
# @String step
# @String pipeline_steps
# @String subfolders
# @String realignment_subfolders
# @String dapiseg_subfolders
from java.lang import System
from prPackage import main
import logging
import os
import sys

root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(root))
import setup_logger

# multiplex.macro.py creates its own logger, as a sub logger to 'pipelineGUI'
logger = logging.getLogger('pipelineGUI.macro')

main.processing(base_dir, target_dir, working_dir, step, pipeline_steps, subfolders, realignment_subfolders,
                dapiseg_subfolders)
System.exit(0)
