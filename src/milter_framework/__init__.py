import pkgutil
import logging

from milter_framework._version import __version__ as version
from milter_framework import configuration

from milter_framework.milter_framework import milter_wrapper

from milter_framework.milter_framework import (
    signal_SIGINT,
    signal_SIGTERM,
    signal_SIGQUIT,
    signal_SIGHUP,
    signal_SIGUSR1,
    signal_SIGUSR2,
)

for finder, name, ispkg in pkgutil.iter_modules():
    logging.warning(f"{name} {ispkg} {finder}")

from milter_framework import plugins
