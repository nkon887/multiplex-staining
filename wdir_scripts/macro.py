# @String base_dir
# @String target_dir
# @String step
from java.lang import System
from prPackage import main
import setup_logger
import logging

# macro.py creates its own logger, as a sub logger to 'pipelineGUI'
logger = logging.getLogger('pipelineGUI.macro')

main.processing(base_dir, target_dir, step)
System.exit(0)
