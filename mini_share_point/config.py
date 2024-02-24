import configparser
import logging
import os


__config = configparser.ConfigParser()


def load_config(ConfigFilePath: str) -> bool:
    """Load the main configuration from file"""
    if os.path.exists(ConfigFilePath) and os.path.isfile(ConfigFilePath):
        __config.read(ConfigFilePath)
        return True

    else:
        logging.getLogger(__name__).critical(
            "Could not find config file <%s> in default location!", ConfigFilePath
        )
        return False


def read_config(Section: str, Key: str, Fallback: str) -> str:
    """Return a configured value"""
    Val = __config.get(Section, Key, fallback=Fallback)

    return Val
