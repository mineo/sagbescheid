#!/usr/bin/env python2
# coding: utf-8
# Copyright © 2015, Wieland Hoffmann
# License: MIT, see LICENSE for details
import argparse
import logging

from .argparse_ext import TestAction
from .notifier import get_all_notifiers, get_enabled_notifiers, NotifierRegistry
from .state import State
from .unit import get_all_unit_paths, Unit, UNIT_IFACE
from functools import partial
from operator import attrgetter
from twisted.internet import defer, reactor
from twisted.python import log
from txdbus import client, error


@defer.inlineCallbacks
def setup(args):
    """
    :type args: :class:`argparse.Namespace`
    """
    con = yield client.connect(reactor, "system")
    registry = NotifierRegistry(get_enabled_notifiers(args.notifier))
    try:
        if args.all_units:
            # Get the names of all units
            units = yield get_all_unit_paths(con)
            for unit in units:
                yield Unit.from_child_object_path(unit, registry).connect(con)
        else:
            for unit in args.unit:
                Unit.from_unit_filename(unit, registry).connect(con)
    except error.DBusException:
        logging.exception(
            "The following exception occured during the initial setup:")
        reactor.stop()


def test(args):
    registry = NotifierRegistry(get_enabled_notifiers(args.notifier))
    units = []
    for unit in args.unit:
        units.append(Unit.from_unit_filename(unit, registry))

    def emit_signals():
        for unit in units:
            unit.state = State[args.test_state_from]
            change = {"ActiveState": args.test_state_to}
            unit.onSignal(UNIT_IFACE, change, None)
            reactor.callLater(2, reactor.stop)

    reactor.callLater(2, emit_signals)


def build_arg_parser():
    parser = argparse.ArgumentParser(prog='sagbescheid',
                                     fromfile_prefix_chars='@',
                                     description='Monitor systemd unit states',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)  # noqa
    available_notifiers = list(get_all_notifiers())
    available_notifier_names = map(attrgetter("name"),
                                   available_notifiers)
    parser.add_argument("--notifier", action="append", default=[],
                        choices=available_notifier_names,
                        help="A notifier to enable.")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Be more verbose.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--unit", action="append",
                       help="A unit to monitor.")
    group.add_argument("--all-units", action="store_true", default=False,
                       help="Monitor all units.")

    for notifier in available_notifiers:
        arg_group = parser.add_argument_group(notifier.name,
                                              "Arguments for the %s notifier" %
                                              notifier.name)
        notifier.add_arguments(arg_group)
    test_group = parser.add_argument_group("Test notifications", """Send a test
    notification for enabled units""")
    test_group.add_argument("--test",
                            action=TestAction,
                            default=False,
                            nargs=0,
                            help="Enable testing mode")
    test_group.add_argument("--test-state-from", action="store",
                            choices=State.__members__.keys(),
                            default="failed",
                            help="The start state for all units")
    test_group.add_argument("--test-state-to", action="store",
                            choices=State.__members__.keys(),
                            default="active",
                            help="The state units will transition to")
    return parser


def main():
    observer = log.PythonLoggingObserver(loggerName="")
    observer.start()

    parser = build_arg_parser()
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    for notifier in get_enabled_notifiers(args.notifier):
        notifier.handle_arguments(args)

    if not args.test:
        reactor.callWhenRunning(partial(setup, args))
    else:
        test(args)
    reactor.run()

if __name__ == "__main__":
    main()
