#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015, 2016 Wieland Hoffmann
# License: MIT, see LICENSE for details
from ..notifier import INotifier
from ..version import version
from .. import state_helpers
from twisted.internet import protocol, reactor
from twisted.plugin import IPlugin
from twisted.words.protocols.irc import IRCClient
from zope.interface.declarations import implementer


class IRCNotifierBot(IRCClient):
    versionName = "sagbescheid"
    versionNum = version
    lineRate = 1

    @property
    def nickname(self):
        return self.factory.nick

    def signedOn(self):
        self.join(self.factory.channel)

    def _msg_channel(self, msg):
        """Send ``msg`` to the configured channel.

        :type msg: str
        """
        self.msg(self.factory.channel, msg)

    def state_changed(self, unit, old_state, new_state):
        """
        :type unit: str
        :type old_state: :class:`sagbescheid.state.State`
        :type new_state: :class:`sagbescheid.state.State`
        """
        unit = unit.encode("utf-8")
        if state_helpers.is_ongoing_failure(old_state, new_state):
            self._msg_channel("%s is still failing." % unit)
        elif state_helpers.is_failure(new_state):
            self._msg_channel("%s entered failed state." % unit)
        elif state_helpers.is_recovery(old_state, new_state):
            self._msg_channel("%s recovered." % unit)
        elif state_helpers.is_normal_stop(old_state, new_state):
            self._msg_channel("%s stopped normally" % unit)
        elif state_helpers.is_normal_start(old_state, new_state):
            self._msg_channel("%s started normally" % unit)


@implementer(IPlugin, INotifier)
class IRCNotifierFactory(protocol.ReconnectingClientFactory):
    name = "irc"
    description = "Log events to an IRC channel"

    protocol = IRCNotifierBot

    def add_arguments(self, group):
        group.add_argument("--irc-nick", action="store",
                           help="Nick for the bot")
        group.add_argument("--irc-channel", action="store",
                           help="Channel for the bot to join")
        group.add_argument("--irc-server", action="store",
                           help="IRC server address")
        group.add_argument("--irc-port", action="store", type=int, default=6667,
                           help="IRC server port")

    def handle_arguments(self, args):
        self.channel = args.irc_channel
        self.nick = args.irc_nick
        self.port = args.irc_port
        self.server = args.irc_server
        reactor.connectTCP(self.server, self.port, self)

    def state_changed(self, *args):
        """Pass state change events through to the client.
        """
        self.prot.state_changed(*args)

    def buildProtocol(self, addr):
        self.prot = protocol.ReconnectingClientFactory.buildProtocol(self, addr)
        return self.prot

obj = IRCNotifierFactory()
