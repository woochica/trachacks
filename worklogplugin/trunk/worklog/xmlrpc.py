# -*- coding: utf-8 -*-

import xmlrpclib
import posixpath

from manager import WorkLogManager

from trac.core import *
from trac.perm import IPermissionRequestor
from tracrpc.api import IXMLRPCHandler, expose_rpc

class WorlLogRPC(Component):
    """ Interface to the [http://trac-hacks.org/wiki/WorkLogPlugin Work Log Plugin] """
    implements(IXMLRPCHandler)

    def __init__(self):
        pass

    def xmlrpc_namespace(self):
        return 'worklog'

    def xmlrpc_methods(self):
        yield ('WIKI_VIEW', ((int,),), self.getRPCVersionSupported)
        yield ('WIKI_VIEW', ((str, int),), self.startWork)
        yield ('WIKI_VIEW', ((str,), (str, str), (str, str, int),), self.stopWork)
        yield ('WIKI_VIEW', ((dict,), (dict, str),), self.getLatestTask)
        yield ('WIKI_VIEW', ((dict,), (dict, str),), self.getActiveTask)
        yield ('WIKI_VIEW', ((str, int,),), self.whoIsWorkingOn)
        yield ('WIKI_VIEW', ((str, int,),), self.whoLastWorkedOn)

    def getRPCVersionSupported(self, req):
        """ Returns 1 with this version of the Work Log XMLRPC API. """
        return 1

    def startWork(self, req, ticket):
        """ Start work on a ticket. Returns the string 'OK' on success or an explanation on error (requires authentication)"""
        mgr = WorkLogManager(self.env, self.config, req.authname)
        if mgr.start_work(ticket):
            return 'OK'
        return mgr.get_explanation()
            
    def stopWork(self, req, comment='', stoptime=None):
        """ Stops work. Returns the string 'OK' on success or an explanation on error (requires authentication, stoptime is seconds since epoch) """
        mgr = WorkLogManager(self.env, self.config, req.authname)
        if mgr.stop_work(stoptime, comment):
            return 'OK'
        return mgr.get_explanation()

    def getLatestTask(self, req, username=None):
        """ Returns a structure representing the info about the latest task. """
        if username:
            mgr = WorkLogManager(self.env, self.config, username)
        else:
            mgr = WorkLogManager(self.env, self.config, req.authname)
        return mgr.get_latest_task()
        
    def getActiveTask(self, req, username=None):
        """ Returns a structure representing the info about the active task (identical to getLatestTask but does not return anything if the work has stopped). """
        if username:
            mgr = WorkLogManager(self.env, self.config, username)
        else:
            mgr = WorkLogManager(self.env, self.config, req.authname)
        return mgr.get_active_task()
        
    def whoIsWorkingOn(self, req, ticket):
        """ Returns the username of the person currently working on the given ticket """
        mgr = WorkLogManager(self.env, self.config, req.authname)
        (who, when) = mgr.who_is_working_on(ticket)
        return who
            
    def whoLastWorkedOn(self, req, ticket):
        """ Returns the username of the person last worked on the given ticket """
        mgr = WorkLogManager(self.env, self.config, req.authname)
        return mgr.who_last_worked_on(ticket)
            
