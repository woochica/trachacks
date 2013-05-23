"""
TicketMoverPlugin:
a plugin for Trac to move tickets from one Trac instance to another
See:
 * http://trac-hacks.org/wiki/DataMoverPlugin
 * http://trac.edgewall.org
"""

import os
import shutil

from trac.config import Option
from trac.core import Component, implements
from trac.env import open_environment
from trac.perm import PermissionSystem
from trac.ticket import Ticket

from tracsqlhelper import get_all_dict
from tracsqlhelper import insert_row_from_dict


class TicketMover(Component):

    permission = Option('ticket', 'move_permission', 'TICKET_ADMIN',
                        """permission needed to move tickets between
                           Trac projects""")

    ### Internal methods

    def projects(self, user):
        base_path, _project = os.path.split(self.env.path)
        _projects = [p for p in os.listdir(base_path)
                     if p != _project]
        projects = {}
        for project in _projects:
            path = os.path.join(base_path, project)
            try:
                env = open_environment(path, use_cache=True)
            except:
                continue
            perm = PermissionSystem(env)
            if self.permission in perm.get_user_permissions(user):
                projects[project] = env

        return projects
        
    def move(self, ticket_id, author, env, delete=False):
        """
        move a ticket to another environment
        
        env: environment to move to
        """
        tables = {'attachment': 'id',
                  'ticket_change': 'ticket'}

        # open the environment if it is a string
        if isinstance(env, basestring):
            base_path, _project = os.path.split(self.env.path)
            env = open_environment(os.path.join(base_path, env),
                                   use_cache=True)

        # get the old ticket
        old_ticket = Ticket(self.env, ticket_id)

        # make a new ticket from the old ticket values
        new_ticket = Ticket(env)
        new_ticket.values = old_ticket.values.copy()
        new_ticket.insert(when=old_ticket.time_created)

        # copy the changelog and attachment DBs
        for table, _id in tables.items():
            for row in get_all_dict(self.env,
                                    "SELECT * FROM %s WHERE %s=%%s"
                                    % (table, _id), str(ticket_id)):
                row[_id] = new_ticket.id
                insert_row_from_dict(env, table, row)

        # copy the attachments
        src_attachment_dir = os.path.join(self.env.path, 'attachments',
                                          'ticket', str(ticket_id))
        if os.path.exists(src_attachment_dir):
            dest_attachment_dir = os.path.join(env.path, 'attachments',
                                               'ticket')
            if not os.path.exists(dest_attachment_dir):
                os.makedirs(dest_attachment_dir)
            dest_attachment_dir = os.path.join(dest_attachment_dir,
                                               str(new_ticket.id))
            shutil.copytree(src_attachment_dir, dest_attachment_dir)

        # note the previous location on the new ticket
        new_ticket.save_changes(author, 'moved from %s'
                                        % self.env.abs_href('ticket',
                                                            ticket_id))

        # location of new ticket
        new_location = env.abs_href('ticket', new_ticket.id)

        if delete:
            old_ticket.delete()
        else:
            # close old ticket and point to new one
            old_ticket['status'] = u'closed'
            old_ticket['resolution'] = u'moved'
            old_ticket.save_changes(author, u'moved to %s' % new_location)
        
        # return the new location
        return new_location
