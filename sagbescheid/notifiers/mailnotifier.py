#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
from ..notifier import INotifier
from .. import state_helpers
from email.mime.text import MIMEText
from StringIO import StringIO
from twisted.internet import defer, reactor
from twisted.mail.smtp import SMTPSenderFactory, ESMTPSenderFactory
from twisted.plugin import IPlugin
from zope.interface.declarations import implementer


@implementer(IPlugin, INotifier)
class SMTPNotifier(object):
    name = "smtp"
    description = "Send notification emails via SMTP"
    factory = SMTPSenderFactory

    def add_arguments(self, group):
        group.add_argument("--smtp-from", action="store")
        group.add_argument("--smtp-to", action="store")
        group.add_argument("--smtp-host", action="store")
        group.add_argument("--smtp-port", action="store", type=int)

    def handle_arguments(self, args):
        self.from_ = args.smtp_from
        self.to = args.smtp_to
        self.host = args.smtp_host
        self.port = args.smtp_port

    def _build_message_file(self, msg):
        """
        :type msg: str
        """
        msg = msg
        message = MIMEText(msg, _subtype='plain', _charset='utf-8')
        message['Subject'] = "sagbescheid service notification"
        message['From'] = self.from_
        message['To'] = self.to
        return StringIO(message.as_string())

    def _send_mail(self, msg):
        """
        :type msg: str
        """
        d = defer.Deferred()
        message = self._build_message_file(msg)
        f = self.factory(self.from_, [self.to], message, d)
        reactor.connectTCP(self.host, self.port, f)

    def state_changed(self, unit, old_state, new_state):
        """
        :type unit: str
        :type old_state: :class:`sagbescheid.state.State`
        :type new_state: :class:`sagbescheid.state.State`
        """
        if state_helpers.is_ongoing_failure(old_state, new_state):
            self._send_mail("%s is still failing." % unit)
        elif state_helpers.is_failure(new_state):
            self._send_mail("%s entered failed state." % unit)
        elif state_helpers.is_recovery(old_state, new_state):
            self._send_mail("%s recovered." % unit)


smtp = SMTPNotifier()


class ESMTPNotifier(SMTPNotifier):
    name = "esmtp"
    description = "Send notification emails via ESMTP"
    factory = ESMTPSenderFactory

    def add_arguments(self, group):
        group.add_argument("--esmtp-from", action="store")
        group.add_argument("--esmtp-to", action="store")
        group.add_argument("--esmtp-user", action="store")
        group.add_argument("--esmtp-password", action="store")
        group.add_argument("--esmtp-host", action="store")
        group.add_argument("--esmtp-port", action="store", type=int)

    def handle_arguments(self, args):
        self.from_ = args.esmtp_from
        self.to = args.esmtp_to
        self.user = args.esmtp_user
        self.password = args.esmtp_password
        self.host = args.esmtp_host
        self.port = args.esmtp_port

    def _send_mail(self, msg):
        """
        :type msg: str
        """
        d = defer.Deferred()
        message = self._build_message_file(msg)
        f = self.factory(self.user, self.password, self.from_, [self.to],
                         message, d, requireTransportSecurity=True)
        reactor.connectTCP(self.host, self.port, f)

esmtp = ESMTPNotifier()
