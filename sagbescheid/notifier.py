#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
from zope.interface import Attribute, Interface


class INotifier(Interface):
    name = Attribute("The name of the notifier")
    description = Attribute("A description of the notifier")

    def state_changed(unit, old_state, new_state):
        """
        :type unit: str
        :type old_state: :class:`sagbescheid.sagbescheid.State`
        :type new_state: :class:`sagbescheid.sagbescheid.State`
        """


class NotifierRegistry(object):
    def __init__(self, notifiers):
        """
        :type notifiers: [:class:`sagbescheid.notifier.INotifier`]
        """
        self.notifiers = {}
        for notifier in notifiers:
            self.notifiers[notifier.name] = notifier

    def state_changed(self, unit, old_state, new_state):
        for notifier in self.notifiers.values():
            notifier.state_changed(unit, old_state, new_state)
