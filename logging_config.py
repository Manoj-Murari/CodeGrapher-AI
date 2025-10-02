# --- logging_config.py ---

import logging
import sys

def setup_logging():
    """
    Configures a logger to write to both a file (app.log) and the console,
    using UTF-8 encoding for broad character support.
    """
    # Remove any existing handlers to avoid duplicate logging
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            # Explicitly set UTF-8 encoding for the file handler
            logging.FileHandler("app.log", encoding='utf-8'),
            # Explicitly set UTF-8 encoding for the console stream handler
            logging.StreamHandler(sys.stdout)
        ]
    )
    # The StreamHandler might still use the terminal's default encoding.
    # For Windows, this can be an issue. A full fix is more complex,
    # but for now, we can just remove the emojis from our log messages.