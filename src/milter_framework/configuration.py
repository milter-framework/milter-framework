#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error
"""

      Marker milter for Postfix - configuration

"""

import os
import pathlib
import configparser
import logging
import importlib
import pkgutil


MODULE_DIR = pathlib.Path(__file__).parent
PWD = pathlib.Path(os.getcwd())

GENERAL_PLUGIN_NAME_PREFIX = "mf"
OUTPUT_PLUGIN_NAME_PREFIX = f"{GENERAL_PLUGIN_NAME_PREFIX}_output"

PWD_CONFIG_FILENAME = PWD / "settings.ini"
DEFAULT_CONFIG_FILENAME = MODULE_DIR / "settings.ini"
CONFIG_FILENAME = None

CONFIG_LOOKUP_LIST = [
    PWD_CONFIG_FILENAME,
    DEFAULT_CONFIG_FILENAME,
]

for config_path_option in CONFIG_LOOKUP_LIST:
    if os.path.isfile(config_path_option):
        CONFIG_FILENAME = config_path_option
        logging.info(f"Config file path: {CONFIG_FILENAME}")
        break


CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_FILENAME)

_LOGLEVEL = CONFIG['general'].get('LOGLEVEL', 'info')
_LOGFILE = CONFIG['general'].get('LOGFILE', '/var/log/postfix-milter-marker.log')


try:
    loglevel = getattr(logging, _LOGLEVEL.upper())

except Exception as e:
    logging.error(f"Couldn't process LOGLEVEL={_LOGLEVEL}")
    logging.warning(f"Setting default log level as INFO")
    loglevel = logging.INFO


try:
    basedir = os.path.dirname(_LOGFILE)
    
    # if not os.path.isdir(_LOGFILE):
    #     logging.error(f"Logfile couldn't be created, directory does not exist: {_LOGFILE}")

    logfile = _LOGFILE

except Exception as e:
    logging.error(f"Couldn't init logger: {str(e)}")
    raise e


env = {
    "general": {
        "loglevel": loglevel,
        "logfile": logfile,
    },

    "plugins": {
        "output": {}
    }

}

logging.root.handlers = []
logging.basicConfig(
    level=loglevel,
    format="%(asctime)s level=%(levelname)s function=%(name)s.%(funcName)s %(message)s",
    handlers=[
        logging.FileHandler(filename=env['general']['logfile']),
        logging.StreamHandler()
    ]
)

