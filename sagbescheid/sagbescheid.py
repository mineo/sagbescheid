#!/usr/bin/env python2
# coding: utf-8
# Copyright © 2015, Wieland Hoffmann
# License: MIT, see LICENSE for details
import argparse
import logging

from .notifier import INotifier, NotifierRegistry
from .unit import Unit
from . import notifiers
from functools import partial
from operator import attrgetter
from twisted.internet import defer, reactor
from twisted.plugin import getPlugins
from twisted.python import log
from txdbus import client


@defer.inlineCallbacks
def setup(enabled_notifiers, units):
    """Add each ``notifier`` to a notifier registry.

    For each unit in ``units``, setup a :class:`Unit` object that connects to
    its ``PropertiesChanged`` signal.

    :type notifiers: [str]
    :type units: [str]
    """
    con = yield client.connect(reactor, "system")
    available_notifiers = getPlugins(INotifier, notifiers)
    available_notifier_name_map = {n.name: n for n in available_notifiers}
    notifiers_to_activate = []

    for notifier in enabled_notifiers:
        notifier_plugin = available_notifier_name_map[notifier]
        notifiers_to_activate.append(notifier_plugin)

    registry = NotifierRegistry(notifiers_to_activate)
    for unit in units:
        Unit(unit, registry).connect(con)


def main():
    observer = log.PythonLoggingObserver(loggerName="")
    observer.start()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    available_notifiers = map(attrgetter("name"),
                              getPlugins(INotifier, notifiers))
    parser.add_argument("--notifier", action="append", default=[],
                        choices=available_notifiers)
    parser.add_argument("--unit", action="append")
    args = parser.parse_args()

    reactor.callWhenRunning(partial(setup, args.notifier, args.unit))
    reactor.run()

if __name__ == "__main__":
    main()
