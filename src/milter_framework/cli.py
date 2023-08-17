#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error
"""

  Marker milter for Postfix
  ===================================================

  CLI tool

  GitHub repository:
  https://github.com/milter-framework/milter-framework

  Community support:
  https://github.com/milter-framework/milter-framework/issues

  Copyright © 2023, Pavel Kim

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import logging
import signal
import threading
import sys

import milter_framework as mf
from pyp8s import MetricsHandler



def main():
    print("Main CLI")
    print(f"env: {mf.configuration.env}")

    logging.info("Setting PostfixMilterMarker")

    logging.info("Setting signal handlser")
    signal.signal(signal.SIGINT, mf.signal_SIGINT)
    signal.signal(signal.SIGQUIT, mf.signal_SIGTERM)
    signal.signal(signal.SIGTERM, mf.signal_SIGQUIT)

    signal.signal(signal.SIGHUP, mf.signal_SIGHUP)
    signal.signal(signal.SIGUSR1, mf.signal_SIGUSR1)
    signal.signal(signal.SIGUSR2, mf.signal_SIGUSR2)

    logging.debug("Setting up milter thread")
    milter_thread = threading.Thread(target=mf.milter_wrapper)
    milter_thread.daemon = True
    milter_thread.start()

    logging.info("Setting up metrics server")
    MetricsHandler.serve()

    logging.info("Waiting for signals")
    signal.pause()

    logging.debug("Exiting")
    sys.exit(0)


if __name__ == '__main__':
    main()
