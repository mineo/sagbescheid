#!/usr/bin/env python2
# coding: utf-8
# Copyright © 2015, Wieland Hoffmann
# License: MIT, see LICENSE for details
import argparse
import logging

from .notifier import INotifier, NotifierRegistry
from .unit import get_all_unit_paths, Unit
from . import notifiers
from functools import partial
from operator import attrgetter
from twisted.internet import defer, reactor
from twisted.plugin import getPlugins
from twisted.python import log
from txdbus import client


@defer.inlineCallbacks
def setup(args):
    """
    :type args: :class:`argparse.Namespace`
    """
    con = yield client.connect(reactor, "system")
    available_notifiers = getPlugins(INotifier, notifiers)
    available_notifier_name_map = {n.name: n for n in available_notifiers}
    notifiers_to_activate = []

    for notifier in args.notifier:
        notifier_plugin = available_notifier_name_map[notifier]
        notifiers_to_activate.append(notifier_plugin)

    registry = NotifierRegistry(notifiers_to_activate)
    if args.all_units:
        # Get the names of all units
        units = yield get_all_unit_paths(con)
        for unit in units:
            yield Unit.from_child_object_path(unit, registry).connect(con)
    else:
        for unit in args.unit:
            Unit.from_unit_filename(unit, registry).connect(con)


def main():
    observer = log.PythonLoggingObserver(loggerName="")
    observer.start()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    available_notifiers = map(attrgetter("name"),
                              getPlugins(INotifier, notifiers))
    parser.add_argument("--notifier", action="append", default=[],
                        choices=available_notifiers)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--unit", action="append")
    group.add_argument("--all-units", action="store_true", default=False)
    args = parser.parse_args()

    reactor.callWhenRunning(partial(setup, args))
    reactor.run()

if __name__ == "__main__":
    main()
