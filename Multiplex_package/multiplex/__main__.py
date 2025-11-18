# multiplex/__main__.py
from multiplex import main

# --- logger -------------------------------------------------
try:
    from multiplex.setup_logger import logger  # configured logger
except Exception:  # minimal fallback logger
    import logging
    logger = logging.getLogger("multiplex")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

main()
