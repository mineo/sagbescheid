#!/usr/bin/env python2
# coding: utf-8
# Copyright © 2015, Wieland Hoffmann
# License: MIT, see LICENSE for details
import argparse
import logging

from .notifier import get_all_notifiers, get_enabled_notifiers, NotifierRegistry
from .unit import get_all_unit_paths, Unit
from functools import partial
from operator import attrgetter
from twisted.internet import defer, reactor
from twisted.python import log
from txdbus import client


@defer.inlineCallbacks
def setup(args):
    """
    :type args: :class:`argparse.Namespace`
    """
    con = yield client.connect(reactor, "system")
    registry = NotifierRegistry(get_enabled_notifiers(args.notifier))
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
    available_notifiers = list(get_all_notifiers())
    available_notifier_names = map(attrgetter("name"),
                                   available_notifiers)
    parser.add_argument("--notifier", action="append", default=[],
                        choices=available_notifier_names)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--unit", action="append")
    group.add_argument("--all-units", action="store_true", default=False)

    for notifier in available_notifiers:
        arg_group = parser.add_argument_group(notifier.name,
                                              "Arguments for the %s notifier" %
                                              notifier.name)
        notifier.add_arguments(arg_group)
    args = parser.parse_args()
    for notifier in get_enabled_notifiers(args.notifier):
        notifier.handle_arguments(args)

    reactor.callWhenRunning(partial(setup, args))
    reactor.run()

if __name__ == "__main__":
    main()
