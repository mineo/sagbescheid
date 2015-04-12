#!/usr/bin/env python2
# coding: utf-8
# Copyright © 2015, Wieland Hoffmann
# License: MIT, see LICENSE for details
import argparse
import enum
import logging

from functools import partial
from twisted.internet import defer, reactor
from twisted.python import log
from txdbus import client

SERVICE_IFACE = "org.freedesktop.systemd1.Service"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"


class State(enum.Enum):
    active = 1
    reloading = 2
    inactive = 3
    failed = 4
    activating = 5
    deactivating = 6
    unknown = 7

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

    def __init__(self, name):
        """
        :type name: str
        """
        self.name = name
        self.state = State.unknown

    @defer.inlineCallbacks
    def connect(self, con):
        """Connect to the units ``PropertiesChanged`` signal on ``con``.

        :type con: :class:`txdbus.client.DBusClientConnection`
        """
        logging.info("Connecting to %s", self.name)
        robj = yield con.getRemoteObject(self.systemd_bus_name,
                                         (self.object_path_template +
                                          make_path(self.name)))
        robj.notifyOnSignal("PropertiesChanged", self.onSignal)

    def _log(self, msg):
        """Log ``msg`` about this unit. The log message will automatically be
        prefixed with the unit name.

        :type msg: str
        """
        logging.info("Unit %s %s", self.name, msg)

    def onSignal(self, iface, changed, invalidated):
        if iface == UNIT_IFACE:
            if "ActiveState" in changed:
                newstate = State[changed["ActiveState"]]
            else:
                return
            if newstate == State.failed:
                if self.state != State.failed:
                    self._log("has failed")
                else:
                    self._log("is still in failed state")
                self.state = newstate
            elif newstate == State.activating:
                self._log("is starting")
            elif (newstate == State.active and self.state == State.failed):
                self._log("has recovered")
                self.state = newstate


@defer.inlineCallbacks
def setup(units):
    """For each unit in ``units``, setup a :class:`Unit` object that connects to
    its ``PropertiesChanged`` signal.

    :type units: [str]
    """
    con = yield client.connect(reactor, "system")
    for unit in units:
        Unit(unit).connect(con)


def main():
    observer = log.PythonLoggingObserver(loggerName="")
    observer.start()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", action="append")
    args = parser.parse_args()

    reactor.callWhenRunning(partial(setup, args.unit))
    reactor.run()

if __name__ == "__main__":
    main()
