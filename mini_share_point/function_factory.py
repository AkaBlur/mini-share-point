import configparser
import importlib
import logging
from typing import Callable

from . import util


@staticmethod
def entry_call() -> str:
    """Main entry point of any loaded function"""


__ModList: dict[str, Callable[..., entry_call]] = {}


def load_mods(ModuleConfigFile: str) -> bool:
    """Load all registered python modules inside basic module config"""
    ModConfig = configparser.ConfigParser()
    if util.check_file_exist(ModuleConfigFile):
        ModConfig.read(ModuleConfigFile)

    else:
        logging.getLogger(__name__).critical(
            "Module configuration <%s> file not found!", ModuleConfigFile
        )
        return False

    if "Modules" not in ModConfig.sections():
        logging.getLogger(__name__).critical(
            "Module configuration could not be loaded!"
        )
        return False

    for ModName in ModConfig["Modules"]:
        PyModule = ModConfig["Modules"][ModName]

        try:
            Mod = importlib.import_module(PyModule)
            __ModList[ModName] = Mod

        except ModuleNotFoundError:
            logging.getLogger(__name__).warning(
                "Module <%s> given in mods not found! Skipping initialization", PyModule
            )

    logging.getLogger(__name__).debug("Function setup complete")

    return True


def call_module(module: str) -> str:
    """Call module by its registered name"""
    if module in __ModList:
        return __ModList[module].entry_call()

    else:
        logging.getLogger(__name__).warning("Requested module <%s> not found!", module)

        return ""
