#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
import logging


from .state import State
from . import state_helpers
from io import BytesIO
from xml.etree import ElementTree
from twisted.internet import defer


SERVICE_IFACE = "org.freedesktop.systemd1.Service"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"


PATH_REPLACEMENTS = {
    ".": "_2e",
    "-": "_2d",
    "/": "_2f"
}

SYSTEMD_BUS_NAME = "org.freedesktop.systemd1"
UNIT_PATH_PREFIX = "/org/freedesktop/systemd1/unit/"


def make_path(unit):
    for from_, to in PATH_REPLACEMENTS.iteritems():
        unit = unit.replace(from_, to)
    return unit


class Unit(object):
    def __init__(self, name, notifier_registry):
        """
        :type name: str
        :type notifier_registry: :class:`sagbescheid.notifier.NotifierRegistry`
        """
        self.object_path = name
        self.notifier_registry = notifier_registry
        self.state = State.unknown

    @classmethod
    def from_unit_filename(cls, name, notifier_registry):
        """Return an object of class ``cls`` (in the basic case a
        :class:`sagbescheid.unit.Unit` object). The object path will be built
        from the unit filename ``name``.

        :type name: str
        :type notifier_registry: :class:`sagbescheid.notifier.NotifierRegistry`
        """
        name = UNIT_PATH_PREFIX + make_path(name)
        return cls(name, notifier_registry)

    @classmethod
    def from_child_object_path(cls, name, notifier_registry):
        """Return an object of class ``cls`` (in the basic case a
        :class:`sagbescheid.unit.Unit` object). The object path will be built
        from the node name returned by introspecting systemd DBus bus.

        :type name: str
        :type notifier_registry: :class:`sagbescheid.notifier.NotifierRegistry`
        """
        return cls(name, notifier_registry)

    @defer.inlineCallbacks
    def connect(self, con):
        """Connect to the units ``PropertiesChanged`` signal on ``con``.

        :type con: :class:`txdbus.client.DBusClientConnection`
        """
        logging.debug("Connecting %s", self.object_path)
        robj = yield con.getRemoteObject(SYSTEMD_BUS_NAME, self.object_path)
        state = yield robj.callRemote("Get", UNIT_IFACE, "ActiveState")
        logging.debug("The state of %s is %s", self.object_path, state)
        self.state = State[state]
        robj.notifyOnSignal("PropertiesChanged", self.onSignal)

    def onSignal(self, iface, changed, invalidated):
        if iface == UNIT_IFACE:
            new_raw_state = changed.get("ActiveState", None)

            if new_raw_state is None:
                return

            logging.debug("%s: state change to %s, old was %s",
                          self.object_path, new_raw_state, self.state)
            new_state = State[new_raw_state]
            self.notifier_registry.state_changed(self.object_path, self.state,
                                                 new_state)
            # For now, only toggle the state between active, inactive and failed
            if (state_helpers.is_failure(new_state) or
                state_helpers.is_recovery(self.state, new_state) or
                state_helpers.is_normal_start(self.state, new_state) or
                state_helpers.is_normal_stop(self.state, new_state) or
                state_helpers.is_change_from_unknown(self.state, new_state)):
                self.state = new_state


@defer.inlineCallbacks
def get_all_unit_paths(con):
    robj = yield con.getRemoteObject(SYSTEMD_BUS_NAME, "/org/freedesktop/systemd1")
    dbus_units = yield robj.callRemote("ListUnits",
                                       interface="org.freedesktop.systemd1.Manager")
    units = []
    for elem in dbus_units:
        unit_name = elem[6]
        logging.info("Discovered a new unit at %s", unit_name)
        units.append(unit_name)

    defer.returnValue(units)
