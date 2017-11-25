#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015, 2017 Wieland Hoffmann
# License: MIT, see LICENSE for details
import logging


from ..notifier import INotifier
from .. import state_helpers
from twisted.plugin import IPlugin
from zope.interface.declarations import implementer


@implementer(IPlugin, INotifier)
class LoggingNotifier(object):
    name = "logging"
    description = "Log events through Pythons logging module"

    def add_arguments(self, group):
        group.add_argument("--logging-level",
                           action="store",
                           default="info",
                           help="The log level to use",
                           choices=["CRITICAL", "ERROR", "WARNING", "INFO",
                                    "DEBUG"])

    def handle_arguments(self, args):
        level = getattr(logging, args.logging_level.upper())
        logging.basicConfig(level=level)

    def normal_start(self, object_path):
        """
        :param self:
        :param object_path:
        """
        logging.info("%s started normally.", object_path)

    def normal_stop(self, object_path):
        """
        :param self:
        :param object_path:
        """
        logging.info("%s stopped normally.", object_path)

    def failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        logging.info("%s failed.", object_path)

    def ongoing_failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        logging.info("%s is still failing.", object_path)

    def recovery(self, object_path):
        """
        :param self:
        :param object_path:
        """
        logging.info("%s recovered.", object_path)

    def change_from_unknown(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass


obj = LoggingNotifier()
