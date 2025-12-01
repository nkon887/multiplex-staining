# @String base_dir
# @String target_dir
# @String working_dir
# @String step
# @String pipeline_steps
# @String subfolders
# @String realignment_subfolders
# @String dapiseg_subfolders
# @String crop_option
# @String forceSave
from java.lang import System
from prPackage import main
import logging
import os
import sys
def close_fiji_console():
    from ij import IJ
    from java.awt import Frame

    try:
        IJ.run("Console", "hide")
    except:
        pass

    for w in Frame.getFrames():
        if w.getTitle() == "Console":
            w.setVisible(False)
close_fiji_console()
root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(root))
import setup_logger

# --- logger -------------------------------------------------
try:
    from multiplex.setup_logger import logger  # configured logger
    # multiplex/macro.py creates its own logger, as a sub logger to 'multiplex'
    logger = logging.getLogger('multiplex.macro')
except Exception:  # minimal fallback logger
    import logging
    logger = logging.getLogger("multiplex")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

main.processing(base_dir, target_dir, working_dir, step, pipeline_steps, subfolders, realignment_subfolders,
                dapiseg_subfolders, crop_option, forceSave)
