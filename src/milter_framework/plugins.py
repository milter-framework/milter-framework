#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error
"""

  Marker milter for Postfix
  ===================================================

  Labels incoming emails with an UUID

  GitHub repository:
  https://github.com/***

  Community support:
  https://github.com/***/issues

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
import importlib

from milter_framework import configuration


if 'plugins' in configuration.CONFIG:


    logging.debug("Found plugins section in the config file")

    if 'output' in configuration.CONFIG['plugins']:

        logging.debug(f"Loading output plugins")

        for output_plugin in configuration.CONFIG['plugins']['output'].split(","):

            try:
                logging.info(f"Trying to load output plugin '{output_plugin}'")

                module_name = f"{configuration.OUTPUT_PLUGIN_NAME_PREFIX}_{output_plugin}"
                symbol = importlib.import_module(module_name)

                configuration.env['plugins']['output'][module_name] = {
                    "symbol": symbol,
                    "config": None,
                    "instance": None,
                }

                logging.debug("Looking up configuration for output plugin '{output_plugin}'")
                plugin_configuration_key = f"plugins.output.{output_plugin}"

                if plugin_configuration_key in configuration.CONFIG:
                    logging.info(f"Found configuration for output plugin '{output_plugin}'")

                    configuration.env['plugins']['output'][module_name]['config'] = configuration.CONFIG[plugin_configuration_key]

                # logging.debug(f"Output plugins: {output_plugins}")

            except Exception as e:
                logging.error(f"Couldn't load output plugin '{output_plugin}': {e}")
                raise e


for output_plugin in configuration.env['plugins']['output']:
    configuration.env['plugins']['output'][output_plugin]['instance'] = configuration.env['plugins']['output'][output_plugin]['symbol'].Plugin(
        config=configuration.env['plugins']['output'][output_plugin]['config']
    )


logging.info("Finished plugins initialisation")
