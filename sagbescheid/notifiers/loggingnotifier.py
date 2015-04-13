#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
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

    def state_changed(self, unit, old_state, new_state):
        """
        :type unit: str
        :type old_state: :class:`sagbescheid.state.State`
        :type new_state: :class:`sagbescheid.state.State`
        """
        if state_helpers.is_ongoing_failure(old_state, new_state):
            logging.info("%s is still failing.", unit)
        elif state_helpers.is_failure(new_state):
            logging.info("%s entered failed state.", unit)
        elif state_helpers.is_recovery(old_state, new_state):
            logging.info("%s recovered.", unit)
        else:
            logging.info("%s changed from %s to %s", unit, old_state,
                         new_state)

obj = LoggingNotifier()
