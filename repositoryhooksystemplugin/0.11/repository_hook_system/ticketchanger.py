"""
annotes and closes tickets based on an SVN commit message;
port of http://trac.edgewall.org/browser/trunk/contrib/trac-post-commit-hook
"""

import os
import re
import sys

from datetime import datetime
from repository_hook_system.interface import IRepositoryHookSubscriber
from trac.config import BoolOption
from trac.config import ListOption
from trac.config import Option
from trac.core import *
from trac.perm import PermissionCache
from trac.ticket import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import utc

from trac.web.api import Request # XXX needed for the TicketManipulators

from StringIO import StringIO

class TicketChanger(Component):
    """annotes and closes tickets on repository commit messages"""

    implements(IRepositoryHookSubscriber)    

    ### options
    envelope_open = Option('ticket-changer', 'opener', default='',
                           doc='must be present before the action taken to take effect')
    envelope_close = Option('ticket-changer', 'closer', default='',
                            doc='must be present after the action taken to take effect')
    intertrac = BoolOption('ticket-changer', 'intertrac', default=False,
                           doc='enforce using ticket prefix from intertrac linking')
    cmd_close = ListOption('ticket-changer', 'close-commands',
                           default='close, closed, closes, fix, fixed, fixes',
                           doc='commit message tokens that indicate ticket close [e.g. "closes #123"]')
    cmd_refs = ListOption('ticket-changer', 'references-commands',
                          default='addresses, re, references, refs, see',
                          doc='commit message tokens that indicate ticket reference [e.g. "refs #123"]')
    
    def is_available(self, repository, hookname):
        return True

    def invoke(self, chgset):

        # regular expressions        
        ticket_prefix = '(?:#|(?:ticket|issue|bug)[: ]?)'
        if self.intertrac:  # TODO: split to separate function?
            # find intertrac links
            intertrac = {}
            aliases = {}
            for key, value in self.env.config.options('intertrac'):
                if '.' in key:
                    name, type_ = key.rsplit('.', 1)
                    if type_ == 'url':
                        intertrac[name] = value
                else:
                    aliases.setdefault(value, []).append(key)
            intertrac = dict([(value, [key] + aliases.get(key, [])) for key, value in intertrac.items()])
            project = os.path.basename(self.env.path)

            if '/%s' % project in intertrac: # TODO:  checking using base_url for full paths:
                ticket_prefix = '(?:%s):%s' % ( '|'.join(intertrac['/%s' % project]),
                                              ticket_prefix )
            else: # hopefully sesible default:
                ticket_prefix = '%s:%s' % (project, ticket_prefix)

        ticket_reference = ticket_prefix + '[0-9]+'
        ticket_command =  (r'(?P<action>[A-Za-z]*).?'
                           '(?P<ticket>%s(?:(?:[, &]*|[ ]?and[ ]?)%s)*)' %
                           (ticket_reference, ticket_reference))
        ticket_command = r'%s%s%s' % (re.escape(self.envelope_open), 
                                      ticket_command,
                                      re.escape(self.envelope_close))
        command_re = re.compile(ticket_command, re.IGNORECASE)
        ticket_re = re.compile(ticket_prefix + '([0-9]+)', re.IGNORECASE)

        # other variables
        msg = "(In [%s]) %s" % (chgset.rev, chgset.message)        
        now = chgset.date
        supported_cmds = {} # TODO: this could become an extension point
        supported_cmds.update(dict([(key, self._cmdClose) for key in self.cmd_close]))
        supported_cmds.update(dict([(key, self._cmdRefs) for key in self.cmd_refs]))

        cmd_groups = command_re.findall(msg)

        tickets = {}
        for cmd, tkts in cmd_groups:
            func = supported_cmds.get(cmd.lower(), None)
            if func:
                for tkt_id in ticket_re.findall(tkts):
                    tickets.setdefault(tkt_id, []).append(func)

        for tkt_id, cmds in tickets.iteritems():
            try:
                db = self.env.get_db_cnx()
                
                ticket = Ticket(self.env, int(tkt_id), db)
                for cmd in cmds:
                    cmd(ticket)

                # determine comment sequence number
                cnum = 0
                tm = TicketModule(self.env)
                for change in tm.grouped_changelog_entries(ticket, db):
                    if change['permanent']:
                        cnum += 1

                # validate the ticket

                # fake a request
                # XXX cargo-culted environ from 
                # http://trac.edgewall.org/browser/trunk/trac/web/tests/api.py
                environ = { 'wsgi.url_scheme': 'http',
                            'wsgi.input': StringIO(''),
                            'SERVER_NAME': '0.0.0.0',
                            'REQUEST_METHOD': 'POST',
                            'SERVER_PORT': 80,
                            'SCRIPT_NAME': '/' + self.env.project_name,
                            'REMOTE_USER': chgset.author,
                            'QUERY_STRING': ''
                            }
                req = Request(environ, None)
                req.args['comment'] = msg
                req.authname = chgset.author
                req.perm = PermissionCache(self.env, req.authname)
                for manipulator in tm.ticket_manipulators:
                    manipulator.validate_ticket(req, ticket)
                msg = req.args['comment']
                ticket.save_changes(chgset.author, msg, now, db, cnum+1)
                db.commit()

                tn = TicketNotifyEmail(self.env)
                tn.notify(ticket, newticket=0, modtime=now)

            except Exception, e:
                message = 'Unexpected error while processing ticket ID %s: %s' % (tkt_id, repr(e))
                print>>sys.stderr, message
                self.env.log.error('TicketChanger: ' + message)
            

    def _cmdClose(self, ticket):
        ticket['status'] = 'closed'
        ticket['resolution'] = 'fixed'

    def _cmdRefs(self, ticket):
        pass
