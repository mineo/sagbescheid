#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015, 2017, 2018 Wieland Hoffmann
# License: MIT, see LICENSE for details
import logging


from automat import MethodicalMachine, NoTransition
from functools import wraps
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


def passthrough_to_registry(func):
    """
    :param func:
    """
    @wraps(func)
    def wrapper(self):
        registry = self.notifier_registry
        object_path = self.object_path
        event_name = func.__name__
        registry.handle_event(object_path, event_name)

    return wrapper


class Unit(object):
    _machine = MethodicalMachine()

    def __init__(self, name, notifier_registry):
        """
        :type name: str
        :type notifier_registry: :class:`sagbescheid.notifier.NotifierRegistry`
        """
        self.object_path = name
        self.notifier_registry = notifier_registry

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
        robj.notifyOnSignal("PropertiesChanged", self.onSignal)

    def onSignal(self, iface, changed, invalidated):
        if iface == UNIT_IFACE:
            new_raw_state = changed.get("ActiveState", None)

            if new_raw_state is None:
                return

            meth = getattr(self, "become_{}".format(new_raw_state))
            try:
                meth()
            except NoTransition as e:
                logging.exception("%s: %s", self.object_path, e)
                raise

    setTheTracingFunction = _machine._setTrace

    @_machine.state(initial=True)
    def unknown(self):
        """The unknown state.
        """
        pass

    @_machine.state()
    def active(self):
        """The active state.
        """
        pass

    @_machine.state()
    def inactive(self):
        """The inactive state.
        """
        pass

    @_machine.state()
    def failed(self):
        """The failed state.
        """
        pass

    @_machine.state()
    def reloading(self):
        """The reloading state.
        """
        pass

    @_machine.state()
    def activating(self):
        """The activating state.
        """
        pass

    @_machine.state()
    def deactivating(self):
        """The deactivating state.
        """
        pass

    @_machine.input()
    def become_unknown(self):
        """"""
        pass

    @_machine.input()
    def become_active(self):
        """"""
        pass

    @_machine.input()
    def become_inactive(self):
        """"""
        pass

    @_machine.input()
    def become_failed(self):
        """"""
        pass

    @_machine.input()
    def become_reloading(self):
        """"""
        pass

    @_machine.input()
    def become_activating(self):
        """"""
        pass

    @_machine.input()
    def become_deactivating(self):
        """"""
        pass

    @_machine.output()
    @passthrough_to_registry
    def normal_start(self):
        """
        :param self:
        """
        pass

    @_machine.output()
    @passthrough_to_registry
    def normal_stop(self):
        """
        :param self:
        """
        pass

    @_machine.output()
    @passthrough_to_registry
    def failure(self):
        """
        :param self:
        """
        pass

    @_machine.output()
    @passthrough_to_registry
    def ongoing_failure(self):
        """
        :param self:
        """
        pass

    @_machine.output()
    @passthrough_to_registry
    def recovery(self):
        """
        :param self:
        """
        pass

    @_machine.output()
    @passthrough_to_registry
    def change_from_unknown(self):
        """
        :param self:
        """
        pass

    unknown.upon(become_unknown, enter=unknown,
                 outputs=[change_from_unknown])
    unknown.upon(become_active, enter=active,
                 outputs=[change_from_unknown])
    unknown.upon(become_inactive, enter=inactive,
                 outputs=[change_from_unknown])
    unknown.upon(become_failed, enter=failed,
                 outputs=[change_from_unknown])
    unknown.upon(become_reloading, enter=reloading,
                 outputs=[change_from_unknown])
    unknown.upon(become_activating, enter=activating,
                 outputs=[change_from_unknown])
    unknown.upon(become_deactivating, enter=deactivating,
                 outputs=[change_from_unknown])

    # This looks weird, but transmission.service is doing the active -> active
    # transition all the time.
    active.upon(become_active, enter=active,
                outputs=[])

    active.upon(become_activating, enter=activating,
                outputs=[])
    active.upon(become_deactivating, enter=deactivating,
                outputs=[])
    active.upon(become_inactive, enter=inactive,
                outputs=[])
    active.upon(become_failed, enter=failed,
                outputs=[failure])
    active.upon(become_reloading, enter=reloading,
                outputs=[])

    inactive.upon(become_active, enter=active,
                  outputs=[])
    inactive.upon(become_failed, enter=failed,
                  outputs=[failure])
    inactive.upon(become_reloading, enter=reloading,
                  outputs=[])
    inactive.upon(become_activating, enter=activating,
                  outputs=[])

    failed.upon(become_active, enter=active,
                outputs=[recovery])
    failed.upon(become_inactive, enter=inactive,
                outputs=[])
    failed.upon(become_failed, enter=failed,
                outputs=[ongoing_failure])
    failed.upon(become_reloading, enter=reloading,
                outputs=[])
    # TODO: There should be a 'recovering' state here
    failed.upon(become_activating, enter=activating,
                outputs=[])
    failed.upon(become_deactivating, enter=deactivating,
                outputs=[])

    reloading.upon(become_active, enter=active,
                   outputs=[])
    reloading.upon(become_inactive, enter=inactive,
                   outputs=[])
    reloading.upon(become_failed, enter=failed,
                   outputs=[])
    reloading.upon(become_reloading, enter=reloading,
                   outputs=[])
    reloading.upon(become_activating, enter=activating,
                   outputs=[])
    reloading.upon(become_deactivating, enter=deactivating,
                   outputs=[])

    activating.upon(become_active, enter=active,
                    outputs=[normal_start])
    activating.upon(become_activating, enter=activating,
                    outputs=[])
    activating.upon(become_inactive, enter=inactive,
                    outputs=[])
    activating.upon(become_failed, enter=failed,
                    outputs=[failure])
    activating.upon(become_reloading, enter=reloading,
                    outputs=[])
    activating.upon(become_deactivating, enter=deactivating,
                    outputs=[])

    deactivating.upon(become_active, enter=active,
                      outputs=[])
    deactivating.upon(become_inactive, enter=inactive,
                      outputs=[normal_stop])
    deactivating.upon(become_failed, enter=failed,
                      outputs=[failure])
    deactivating.upon(become_reloading, enter=reloading,
                      outputs=[])
    deactivating.upon(become_activating, enter=activating,
                      outputs=[])
    deactivating.upon(become_deactivating, enter=deactivating,
                      outputs=[])


@defer.inlineCallbacks
def get_all_unit_paths(con):
    robj = yield con.getRemoteObject(SYSTEMD_BUS_NAME, "/org/freedesktop/systemd1")  # noqa
    dbus_units = yield robj.callRemote("ListUnits",
                                       interface="org.freedesktop.systemd1.Manager")  # noqa
    units = []
    for elem in dbus_units:
        unit_name = elem[6]
        logging.info("Discovered a new unit at %s", unit_name)
        units.append(unit_name)

    defer.returnValue(units)
