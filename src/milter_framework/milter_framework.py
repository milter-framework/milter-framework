#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error
"""

  Marker milter for Postfix
  ===================================================

  Labels incoming emails with an UUID

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

import os
import sys
import uuid
import json
import signal
import logging
import datetime
from threading import Thread

import Milter
from pyp8s import MetricsHandler

from .configuration import env

class PostfixMilterMarker(Milter.Base):
    """
        Dumps the entire email to somewhere
    """

    def __init__(self):

        MetricsHandler.inc("milter_init", 1)

        self.id = Milter.uniqueID()
        self.uuid = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        self.body_chunks = []
        self.message = {
            "session_id": self.id,
            "uuid": self.uuid,
            "timestamp": self.timestamp,

            "mail_from": None,
            "rcpt_to": None,
            "helo": None,

            "hostname": None,
            "family": None,
            "hostaddr": None,

            "headers": {},
            "body": None,
        }

        logging.info(f"id={self.id} Milter initialised with uuid={self.uuid}")

    @Milter.noreply
    def connect(self, hostname, family, hostaddr):
        """
            connect method
        """

        MetricsHandler.inc(f"milter_connect", 1)
        logging.debug(f"id={self.id} Incoming connection hostname={hostname} family={family} hostaddr={hostaddr}")

        self.message["hostname"] = hostname
        self.message["family"] = family
        self.message["hostaddr"] = hostaddr

        logging.info(f"id={self.id} Incoming connection from {hostaddr} ({hostname})")
        return Milter.CONTINUE

    @Milter.noreply
    def hello(self, hostname):
        """
            Called when the SMTP client says HELO.
        """

        MetricsHandler.inc(f"milter_helo", 1)
        logging.debug(f"id={self.id} Received HELO hostname={hostname}")

        self.message["helo"] = hostname

        return Milter.CONTINUE

    @Milter.noreply
    def envfrom(self, mailfrom, *args, **kwargs):
        """
            Called when the SMTP client says MAIL FROM
        """

        MetricsHandler.inc(f"milter_mail_from", 1)
        logging.debug(f"id={self.id} MAIL FROM detected mailfrom={mailfrom} args={args} kwargs={kwargs}")

        self.message["mail_from"] = mailfrom

        logging.info(f"id={self.id} MAIL FROM: {mailfrom}")
        return Milter.CONTINUE

    @Milter.noreply
    def envrcpt(self, to, *args, **kwargs):
        """
            Called when the SMTP client says RCPT TO
        """

        MetricsHandler.inc(f"milter_rcpt_to", 1)
        logging.debug(f"id={self.id} RCPT TO detected to={to} args={args} kwargs={kwargs}")

        self.message["rcpt_to"] = to

        logging.info(f"id={self.id} RCPT TO: {to}")
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, field, value):
        """
            Called for each header field in the message body.
        """

        MetricsHandler.inc(f"milter_header", 1)
        logging.debug(f"id={self.id} Processing a header field={field} value={value}")

        if field in self.message["headers"]:
            self.message["headers"][field].append(value)
        else:
            self.message["headers"][field] = [value, ]


        return Milter.CONTINUE

    @Milter.noreply
    def data(self):
        """
            Called when the SMTP client says DATA.
        """

        MetricsHandler.inc(f"milter_data", 1)
        logging.debug(f"id={self.id} Client started sending DATA")

        logging.info(f"id={self.id} DATA started")
        return Milter.CONTINUE

    @Milter.noreply
    def body(self, blk):
        """
            Called to supply the body of the message to the Milter by chunks.
        """

        MetricsHandler.inc(f"milter_body_chunk", 1)
        logging.debug(f"id={self.id} Processing body by chunks blk={blk}")
        self.body_chunks.append(blk)

        return Milter.CONTINUE

    def eoh(self):
        """
            Called at the blank line that terminates the header fields.
        """

        MetricsHandler.inc(f"milter_eoh", 1)
        logging.debug(f"id={self.id} Reached the end of headers")

        logging.info(f"id={self.id} End of headers. Headers count: {len(self.message['headers'])}")

        for output_plugin_name in env['plugins']['output']:
            logging.info(f"Invoking plugin {output_plugin_name} for eoh")
            env['plugins']['output'][output_plugin_name]['instance'].event("eoh", self.message)

        self.message["queue_id"] = self.getsymval('i')
        logging.info(f"id={self.id} Queue id: '{self.message['queue_id']}'")

        # return Milter.REJECT
        return Milter.CONTINUE

    def eom(self):
        """
            Called at the end of the message body.
        """

        MetricsHandler.inc("milter_eom", 1)
        logging.debug(f"id={self.id} Reached the end of message")

        logging.debug(f"id={self.id} Merging body chunks into a utf-8 string")
        self.message["body"] = "".join([ chunk.decode("utf-8") for chunk in self.body_chunks])
        
        logging.info(f"id={self.id} End of message. Merged '{len(self.body_chunks)}' body chunks, body size '{len(self.message['body']) if self.message['body'] is not None else None}'")

        self.addheader(field="X-Marker-UUID", value=self.uuid, idx=-1)

        for output_plugin_name in env['plugins']['output']:
            logging.info(f"Invoking plugin {output_plugin_name} for eom")
            env['plugins']['output'][output_plugin_name]['instance'].event("eom", self.message)

        return Milter.CONTINUE

    def close(self):
        """
            Called when the connection is closed.
        """

        MetricsHandler.inc("milter_close", 1)
        logging.debug(f"id={self.id} Connection closed")

        # logging.debug(f"id={self.id} Dumping message into JSON structure")
        # logging.debug(f"id={self.id} Message: {self.message}")
        # filename = f"output/{self.timestamp}_{self.id}_{self.uuid}.json"
        # with open(filename, "w") as fh:
        #     fh.write(json.dumps(self.message))

        # logging.debug(f"id={self.id} Dumped message to {filename}")
        logging.info(f"id={self.id} Connection closed. Body size: {len(self.message['body']) if self.message['body'] is not None else None}")
        return Milter.CONTINUE


def milter_wrapper():
    """
        Milter thread wrapper
    """

    Milter.factory = PostfixMilterMarker

    flags = Milter.CHGHDRS + Milter.ADDHDRS + Milter.QUARANTINE
    Milter.set_flags(flags)

    logging.info(f"Starting Milter")
    Milter.runmilter(f"{Milter.factory.__class__.__name__}", "inet:19000", timeout=300)
    logging.info(f"Milter exited")


def signal_SIGINT(signum, frame):
    MetricsHandler.inc("SIGINT", 1)
    logging.warning(f"Caught a signal: signum={signum} frame={frame} (SIGINT)")

def signal_SIGTERM(signum, frame):
    MetricsHandler.inc("SIGTERM", 1)
    logging.warning(f"Caught a signal: signum={signum} frame={frame} (SIGTERM)")

def signal_SIGQUIT(signum, frame):
    MetricsHandler.inc("SIGQUIT", 1)
    logging.warning(f"Caught a signal: signum={signum} frame={frame} (SIGQUIT)")

def signal_SIGHUP(signum, frame):
    MetricsHandler.inc("SIGHUP", 1)
    logging.warning(f"Caught a signal: signum={signum} frame={frame} (SIGHUP)")

def signal_SIGUSR1(signum, frame):
    MetricsHandler.inc("SIGUSR1", 1)
    logging.warning(f"Caught a signal: signum={signum} frame={frame} (SIGUSR1)")

def signal_SIGUSR2(signum, frame):
    MetricsHandler.inc("SIGUSR2", 1)
    logging.warning(f"Caught a signal: signum={signum} frame={frame} (SIGUSR2)")


if __name__ == '__main__':


    logging.info("Setting PostfixMilterMarker")

    logging.info("Setting signal handlser")
    signal.signal(signal.SIGINT, signal_SIGINT)
    signal.signal(signal.SIGQUIT, signal_SIGTERM)
    signal.signal(signal.SIGTERM, signal_SIGQUIT)

    signal.signal(signal.SIGHUP, signal_SIGHUP)
    signal.signal(signal.SIGUSR1, signal_SIGUSR1)
    signal.signal(signal.SIGUSR2, signal_SIGUSR2)

    logging.debug("Setting up milter thread")
    milter_thread = Thread(target=milter_wrapper)
    milter_thread.daemon = True
    milter_thread.start()

    logging.info("Setting up metrics server")
    MetricsHandler.serve()

    logging.info("Waiting for signals")
    signal.pause()

    logging.debug("Exiting")
    sys.exit(0)

