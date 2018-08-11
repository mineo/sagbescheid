#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015, 2016, 2017, 2018 Wieland Hoffmann
# License: MIT, see LICENSE for details
from ..notifier import INotifier
from ..version import version
from functools import wraps
from twisted.internet import protocol, reactor
from twisted.plugin import IPlugin
from twisted.words.protocols.irc import IRCClient
from zope.interface.declarations import implementer


def passthrough_to_client(func):
    """
    :param func:
    """
    @wraps(func)
    def wrapper(self, object_path):
        client = self.prot
        event_name = func.__name__
        method = getattr(client, event_name)
        method(object_path)

    return wrapper


class IRCNotifierBot(IRCClient):
    versionName = "sagbescheid"
    versionNum = version
    lineRate = 1

    @property
    def nickname(self):
        return self.factory.nick

    def signedOn(self):
        self.factory.resetDelay()
        self.join(self.factory.channel)

    def _msg_channel(self, msg):
        """Send ``msg`` to the configured channel.

        :type msg: str
        """
        self.msg(self.factory.channel, msg)

    def normal_start(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._msg_channel("%s started normally." % object_path)

    def normal_stop(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._msg_channel("%s stopped normally." % object_path)

    def failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._msg_channel("%s failed." % object_path)

    def ongoing_failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._msg_channel("%s is still failing." % object_path)

    def recovery(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._msg_channel("%s recovered." % object_path)

    def change_from_unknown(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass


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

    def buildProtocol(self, addr):
        self.prot = protocol.ReconnectingClientFactory.buildProtocol(self, addr)
        return self.prot

    @passthrough_to_client
    def normal_start(self, object_path):
        """
        :param self:
        :param object_path:
        """

    @passthrough_to_client
    def normal_stop(self, object_path):
        """
        :param self:
        :param object_path:
        """

    @passthrough_to_client
    def failure(self, object_path):
        """
        :param self:
        :param object_path:
        """

    @passthrough_to_client
    def ongoing_failure(self, object_path):
        """
        :param self:
        :param object_path:
        """

    @passthrough_to_client
    def recovery(self, object_path):
        """
        :param self:
        :param object_path:
        """

    @passthrough_to_client
    def change_from_unknown(self, object_path):
        """
        :param self:
        :param object_path:
        """


obj = IRCNotifierFactory()
