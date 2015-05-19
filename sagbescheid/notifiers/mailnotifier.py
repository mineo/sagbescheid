#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
from ..notifier import INotifier
from .. import state_helpers
from email.mime.text import MIMEText
from StringIO import StringIO
from twisted.mail.smtp import (messageid, sendmail)
from twisted.plugin import IPlugin
from zope.interface.declarations import implementer


@implementer(IPlugin, INotifier)
class SMTPNotifier(object):
    name = "smtp"
    description = "Send notification emails via twisted.mail.smtp.sendmail"

    def add_arguments(self, group):
        group.add_argument("--smtp-from", action="store",
                           help="The address to use in the From: header")
        group.add_argument("--smtp-to", action="store",
                           help="The address to use in the To: header")
        group.add_argument("--smtp-user", action="store", default=None,
                           help="The SMTP username")
        group.add_argument("--smtp-password", action="store", default=None,
                           help="The SMTP password")
        group.add_argument("--smtp-host", action="store",
                           help="The SMTP host")
        group.add_argument("--smtp-port", action="store", type=int,
                           help="The SMTP port")
        group.add_argument("--smtp-require-authentication", action="store_true",
                           default=False, help="Require authentication")
        group.add_argument("--smtp-require-transport-security",
                           action="store_true", default=False,
                           help="Require STARTTLS")

    def handle_arguments(self, args):
        self.from_ = args.smtp_from
        self.to = args.smtp_to
        self.user = args.smtp_user
        self.password = args.smtp_password
        self.host = args.smtp_host
        self.port = args.smtp_port
        self.auth = args.smtp_require_authentication
        self.transport_sec = args.smtp_require_transport_security

    def _build_message_file(self, msg):
        """
        :type msg: str
        """
        msg = msg
        message = MIMEText(msg, _subtype='plain', _charset='utf-8')
        message['Subject'] = "sagbescheid service notification"
        message['From'] = self.from_
        message['To'] = self.to
        message['Message-ID'] = messageid()
        return StringIO(message.as_string())

    def _send_mail(self, msg):
        """
        :type msg: str
        """
        message = self._build_message_file(msg)
        sendmail(self.host, self.from_, [self.to], message, port=self.port,
                 username=self.user, password=self.password,
                 requireAuthentication=self.auth,
                 requireTransportSecurity=self.transport_sec)

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

sendmailnotifier = SMTPNotifier()
