#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
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
OBJECT_PATH_TEMPLATE = "/org/freedesktop/systemd1/unit/"


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
        name = OBJECT_PATH_TEMPLATE + make_path(name)
        return cls(name, notifier_registry)

    @classmethod
    def from_child_object_path(cls, name, notifier_registry):
        """Return an object of class ``cls`` (in the basic case a
        :class:`sagbescheid.unit.Unit` object). The object path will be built
        from the node name returned by introspecting systemd DBus bus.

        :type name: str
        :type notifier_registry: :class:`sagbescheid.notifier.NotifierRegistry`
        """
        name = "/" + name
        return cls(name, notifier_registry)

    @defer.inlineCallbacks
    def connect(self, con):
        """Connect to the units ``PropertiesChanged`` signal on ``con``.

        :type con: :class:`txdbus.client.DBusClientConnection`
        """
        robj = yield con.getRemoteObject(SYSTEMD_BUS_NAME, self.object_path)
        robj.notifyOnSignal("PropertiesChanged", self.onSignal)

    def onSignal(self, iface, changed, invalidated):
        if iface == UNIT_IFACE:
            new_raw_state = changed.get("ActiveState", None)

            if new_raw_state is None:
                return

            new_state = State[new_raw_state]
            self.notifier_registry.state_changed(self.object_path, self.state,
                                                 new_state)
            # For now, only toggle the state between active, inactive and failed
            if (state_helpers.is_failure(new_state) or
                state_helpers.is_recovery(self.state, new_state) or
                state_helpers.is_normal_start(self.state, new_state) or
                state_helpers.is_normal_stop(self.state, new_state)):
                self.state = new_state


@defer.inlineCallbacks
def get_all_unit_paths(con):
    robj = yield con.getRemoteObject(SYSTEMD_BUS_NAME, "/")
    introspection_xml = yield robj.callRemote("Introspect")
    parser = ElementTree.XMLParser()
    units = []
    for _, elem in ElementTree.iterparse(BytesIO(
            introspection_xml.encode("utf-8")),
        parser=parser):
        if elem.tag == "node":
            if "name" in elem.attrib:
                units.append(elem.attrib["name"])

    defer.returnValue(units)
