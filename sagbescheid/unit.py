#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
from .state import State
from . import state_helpers
from twisted.internet import defer


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
        :type notifier_registry: :class:`sagbescheid.notifier.NotifierRegistry`
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
