#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015, 2017, 2018, 2019 Wieland Hoffmann
# License: MIT, see LICENSE for details
from ..notifier import INotifier
from email.mime.text import MIMEText
from six import StringIO
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

    def normal_start(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def normal_stop(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass

    def failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._send_mail("%s failed." % object_path)

    def ongoing_failure(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._send_mail("%s is still failing." % object_path)

    def recovery(self, object_path):
        """
        :param self:
        :param object_path:
        """
        self._send_mail("%s recovered." % object_path)

    def change_from_unknown(self, object_path):
        """
        :param self:
        :param object_path:
        """
        pass


sendmailnotifier = SMTPNotifier()
