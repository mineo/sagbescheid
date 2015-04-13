#!/usr/bin/env python2
# coding: utf-8
# Copyright © 2015, Wieland Hoffmann
# License: MIT, see LICENSE for details
import argparse
import logging

from .notifier import INotifier, NotifierRegistry
from .state import State
from . import notifiers, state_helpers
from functools import partial
from operator import attrgetter
from twisted.internet import defer, reactor
from twisted.plugin import getPlugins
from twisted.python import log
from txdbus import client

SERVICE_IFACE = "org.freedesktop.systemd1.Service"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"


PATH_REPLACEMENTS = {
    ".": "_2e",
    "-": "_2d",
    "/": "_2f"
}


def make_path(unit):
    for from_, to in PATH_REPLACEMENTS.iteritems():
        unit = unit.replace(from_, to)
    return unit


class Unit(object):
    systemd_bus_name = "org.freedesktop.systemd1"
    object_path_template = "/org/freedesktop/systemd1/unit/"

    def __init__(self, name, notifier_registry):
        """
        :type name: str
        """
        self.name = name
        self.notifier_registry = notifier_registry
        self.state = State.unknown

    @defer.inlineCallbacks
    def connect(self, con):
        """Connect to the units ``PropertiesChanged`` signal on ``con``.

        :type con: :class:`txdbus.client.DBusClientConnection`
        """
        robj = yield con.getRemoteObject(self.systemd_bus_name,
                                         (self.object_path_template +
                                          make_path(self.name)))
        robj.notifyOnSignal("PropertiesChanged", self.onSignal)

    def onSignal(self, iface, changed, invalidated):
        if iface == UNIT_IFACE:
            new_raw_state = changed.get("ActiveState", None)

            if new_raw_state is None:
                return

            new_state = State[new_raw_state]
            self.notifier_registry.state_changed(self.name, self.state,
                                                 new_state)
            # For now, only toggle the state between active and failed.
            if state_helpers.is_failure(new_state):
                self.state = new_state
            elif state_helpers.is_recovery(self.state, new_state):
                self.state = new_state


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
