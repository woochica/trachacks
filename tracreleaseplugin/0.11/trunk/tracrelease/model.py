# -*- coding: utf-8 -*-


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
        
    def __str__(self):
        t = ",".join([str(ticket) for ticket in self.tickets])
        s = ",".join([str(sign) for sign in self.signatures])
        i = ",".join([str(inst) for inst in self.install_procedures])
        
        return "<Release: id: %s; version: %s; tickets: %s; signs: %s; installs: %s>" % (self.id, self.version, t, s, i)

class ReleaseTicket(object):
    def __init__(self, release_id = None, ticket_id = None, summary = None,
                 component = None, type = None, version = None):
        self.release_id = release_id
        self.ticket_id = ticket_id
        self.summary = summary
        self.component = component
        self.type = type
        self.version = version
        
    def __str__(self):
        return "<ReleaseTicket: id: %s>" % self.release_id

class ReleaseSignee(object):
    def __init__(self, id = None, user = None, date = None):
        self.release_id = id
        self.signature = user
        self.sign_date = date

    def __str__(self):
        return "<ReleaseSignee: id: %s; user: %s>" % (self.release_id, self.signature)


class InstallProcedures(object):
    def __init__(self, id = None, name = None, description = None, contain_files = None):
        self.id = id
        self.name = name
        self.description = description
        self.contain_files = contain_files
        
    def __str__(self):
        return "<InstallProcedures id=%s>" % (self.id)



class ReleaseInstallProcedure(object):
    def __init__(self, release_id = None, install_procedure = None, install_files = None):
        self.release_id = release_id
        self.install_procedure = install_procedure
        self.install_files = install_files

    def __str__(self):
        return "<ReleaseInstallProcedure: id: %s; proc: %s; files: %s>" % (
            self.release_id, str(self.install_procedure), str(self.install_files))

