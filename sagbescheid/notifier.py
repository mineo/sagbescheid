#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015, 2017 Wieland Hoffmann
# License: MIT, see LICENSE for details
from . import notifiers

from twisted.plugin import getPlugins
from zope.interface import Attribute, Interface


class INotifier(Interface):
    name = Attribute("The name of the notifier")
    description = Attribute("A description of the notifier")

    def add_arguments(parser):
        """Allows notifiers to add additional command line arguments.

        :type parser: :class:`argparse.ArgumentParser`
        """

    def handle_arguments(args):
        """Called when command line arguments have been parsed.

        :type: :class:`argparse.Namespace`
        """

    def normal_start(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def normal_stop(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def ongoing_failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def recovery(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def change_from_unknown(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass


class NotifierRegistry(object):
    def __init__(self, notifiers):
        """
        :type notifiers: [:class:`sagbescheid.notifier.INotifier`]
        """
        self.notifiers = {}
        for notifier in notifiers:
            self.notifiers[notifier.name] = notifier

    def handle_event(self, object_path, event_name):
        """
        :param self:
        :param object_path:
        :param event_name:
        """
        for notifier in self.notifiers.itervalues():
            method = getattr(notifier, event_name)
            method(object_path)


def get_all_notifiers():
    return getPlugins(INotifier, notifiers)


def get_enabled_notifiers(enabled_notifier_names):
    """
    :type enabled_notifier_names: :class:`[str]`
    :rtype: :class:`sagbescheid.notifier.INotifier`
    """
    available_notifiers = get_all_notifiers()
    available_notifier_name_map = {n.name: n for n in available_notifiers}
    notifiers_to_activate = []

    for notifier in enabled_notifier_names:
        notifier_plugin = available_notifier_name_map[notifier]
        notifiers_to_activate.append(notifier_plugin)

    return notifiers_to_activate
