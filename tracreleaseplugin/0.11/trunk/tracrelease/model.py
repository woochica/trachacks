# -*- coding: utf8 -*-


class Release(object):
    def __init__(self, id = None, version = None, description = None,
                 author = None, creation = None, planned = None, install = None):
        self.id = id
        self.version = version
        self.description = description
        self.author = author
        self.creation_date = creation
        self.planned_date = planned
        self.install_date = install
        self.tickets = []
        self.signatures = []

class ReleaseTicket(object):
    def __init__(self, release_id = None, ticket_id = None, summary = None,
                 component = None, type = None, version = None):
        self.release_id = release_id
        self.ticket_id = ticket_id
        self.summary = summary
        self.component = component
        self.type = type
        self.version = version

class ReleaseSignee(object):
    def __init__(self, id = None, user = None, date = None):
        self.release_id = id
        self.signature = user
        self.sign_date = date


