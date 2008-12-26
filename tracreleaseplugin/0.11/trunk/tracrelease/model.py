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
        self.install_procedures = []

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


class InstallProcedures(object):
    def __init__(self, id = None, name = None, description = None, contain_files = None):
        self.id = id
        self.name = name
        self.description = description
        self.contain_files = contain_files


class ReleaseInstallProcedure(object):
    def __init__(self, release_id = None, install_procedure = None, install_files = None):
        self.release_id = release_id
        self.install_procedure = install_procedure
        self.install_files = install_files

