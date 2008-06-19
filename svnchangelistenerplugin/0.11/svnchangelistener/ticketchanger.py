"""
annotes and closes tickets based on an SVN commit message;
port of http://trac.edgewall.org/browser/trunk/contrib/trac-post-commit-hook
to work with SVN Change Listener 
"""

import re
import sys

from datetime import datetime
from interface import ISVNChangeListener
from trac.core import *
from trac.ticket import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import utc

# TODO: look only for tickets that match 
# `projectname:#|(ticket|issue|bug)`
# according to configuration
# (which also means moving the regex to the class TicketChanger)

ticket_prefix = '(?:#|(?:ticket|issue|bug)[: ]?)'
ticket_reference = ticket_prefix + '[0-9]+'
ticket_command =  (r'(?P<action>[A-Za-z]*).?'
                   '(?P<ticket>%s(?:(?:[, &]*|[ ]?and[ ]?)%s)*)' %
                   (ticket_reference, ticket_reference))

envelope = False # TODO: move this to configuration and re-enable
if envelope:
    ticket_command = r'\%s%s\%s' % (options.envelope[0], ticket_command,
                                    options.envelope[1])

command_re = re.compile(ticket_command)
ticket_re = re.compile(ticket_prefix + '([0-9]+)')

class TicketChanger(Component):
    implements(ISVNChangeListener)

    _supported_cmds = {'close':      '_cmdClose',
                       'closed':     '_cmdClose',
                       'closes':     '_cmdClose',
                       'fix':        '_cmdClose',
                       'fixed':      '_cmdClose',
                       'fixes':      '_cmdClose',
                       'addresses':  '_cmdRefs',
                       're':         '_cmdRefs',
                       'references': '_cmdRefs',
                       'refs':       '_cmdRefs',
                       'see':        '_cmdRefs'}

    def on_change(self, env, chgset):
        self.env = env
        self.author = chgset.author
        self.rev = chgset.rev        
        self.msg = "(In [%s]) %s" % (self.rev, chgset.message)        
        self.now = chgset.date

        cmd_groups = command_re.findall(self.msg)

        tickets = {}
        for cmd, tkts in cmd_groups:
            funcname = self._supported_cmds.get(cmd.lower(), '')
            if funcname:
                for tkt_id in ticket_re.findall(tkts):
                    func = getattr(self, funcname)
                    tickets.setdefault(tkt_id, []).append(func)

        for tkt_id, cmds in tickets.iteritems():
            try:
                db = self.env.get_db_cnx()
                
                ticket = Ticket(self.env, int(tkt_id), db)
                for cmd in cmds:
                    cmd(ticket)

                # determine sequence number... 
                cnum = 0
                tm = TicketModule(self.env)
                for change in tm.grouped_changelog_entries(ticket, db):
                    if change['permanent']:
                        cnum += 1
                
                ticket.save_changes(self.author, self.msg, self.now, db, cnum+1)
                db.commit()
                
                tn = TicketNotifyEmail(self.env)
                tn.notify(ticket, newticket=0, modtime=self.now)
            except Exception, e:
                # import traceback
                # traceback.print_exc(file=sys.stderr)
                print>>sys.stderr, 'Unexpected error while processing ticket ' \
                                   'ID %s: %s' % (tkt_id, e)
            

    def _cmdClose(self, ticket):
        ticket['status'] = 'closed'
        ticket['resolution'] = 'fixed'

    def _cmdRefs(self, ticket):
        pass
