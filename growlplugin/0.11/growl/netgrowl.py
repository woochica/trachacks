# -*- coding: utf-8 -*-
#
# Growl 0.6 Network Protocol Client for Python
#   :version: 0.6
#   :author: Rui Carmo (http://the.taoofmac.com)
#   :copyright: (C) 2004 Rui Carmo. Code under BSD License.
#   :contributors:  Ingmar J Stein (Growl Team), 
#                   Emmanuel Blot (tweaks for TracGrowlPlugin)
#

import struct
import md5

GROWL_PROTOCOL_VERSION = 1
GROWL_TYPE_REGISTRATION = 0
GROWL_TYPE_NOTIFICATION = 1

class GrowlRegistrationPacket(object):
    """Builds a Growl Network Registration packet."""

    def __init__(self, application="Trac", password=None):
        self.notifications = []
        self.defaults = [] # array of indexes into notifications
        self.application = application.encode("utf-8")
        self.password = password

    def addNotification(self, notification, enabled=True):
        """Adds a notification type and sets whether it is enabled on the GUI"""
        self.notifications.append(notification)
        if enabled:
            self.defaults.append(len(self.notifications)-1)

    def payload(self):
        """Returns the packet payload."""
        self.data = struct.pack("!BBH",
                                GROWL_PROTOCOL_VERSION,
                                GROWL_TYPE_REGISTRATION,
                                len(self.application))
        self.data += struct.pack("BB",
                                 len(self.notifications),
                                 len(self.defaults))
        self.data += self.application
        for notification in self.notifications:
            encoded = notification.encode("utf-8")
            self.data += struct.pack("!H", len(encoded))
            self.data += encoded
        for default in self.defaults:
            self.data += struct.pack("B", default)
        self.checksum = md5.new()
        self.checksum.update(self.data)
        if self.password:
            self.checksum.update(self.password.encode("utf-8"))
        self.data += self.checksum.digest()
        return self.data


class GrowlNotificationPacket(object):
    """Builds a Growl Network Notification packet."""

    def __init__(self, notification, title, description, application="Trac",
                 password=None, priority=0, sticky=False):
        self.application = application.encode("utf-8")
        self.notification = notification.encode("utf-8")
        self.title = title.encode("utf-8")
        self.description = description.encode("utf-8")
        flags = (priority & 0x07) * 2
        if priority < 0:
            flags |= 0x08
        if sticky:
            flags = flags | 0x0001
        self.data = struct.pack("!BBHHHHH",
                                GROWL_PROTOCOL_VERSION,
                                GROWL_TYPE_NOTIFICATION,
                                flags,
                                len(self.notification),
                                len(self.title),
                                len(self.description),
                                len(self.application))
        self.data += self.notification
        self.data += self.title
        self.data += self.description
        self.data += self.application
        self.checksum = md5.new()
        self.checksum.update(self.data)
        if password:
            self.checksum.update(password.encode("utf-8"))
        self.data += self.checksum.digest()

    def payload(self):
        """Returns the packet payload."""
        return self.data
