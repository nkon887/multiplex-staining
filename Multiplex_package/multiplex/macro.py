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
import setup_logger
import logging

# multiplex.macro.py creates its own logger, as a sub logger to 'pipelineGUI'
logger = logging.getLogger('pipelineGUI.macro')

main.processing(base_dir, target_dir, working_dir, step, pipeline_steps, subfolders, realignment_subfolders, dapiseg_subfolders)
System.exit(0)
