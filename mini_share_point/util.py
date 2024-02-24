import logging
import os


def check_file_exist(Filepath: str) -> bool:
    """Checks if a given file exists"""
    if os.path.exists(Filepath) and os.path.isfile(Filepath):
        return True

    else:
        logging.getLogger(__name__).info("File not found! - %s", Filepath)
        return False
