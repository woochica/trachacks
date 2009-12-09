#!/usr/bin/env python
"""
programmatic front end to trac-admin tasks
"""

import pkg_resources
import sys

from martini.config import ConfigMunger
from martini.utils import getlist
from optparse import OptionParser
from trac.admin.console import TracAdmin
from trac.env import open_environment
from trac.perm import PermissionSystem
from trac.ticket import model

class TracLegosAdmin(TracAdmin):
    """TracLegos front-end to Trac's command-line-admin interface"""

    def __init__(self, env):
        TracAdmin.__init__(self, env)
        self.env = open_environment(env)

        # new style, as of trac:changeset:7677
        # see trac:#7770
        # for now, support both use-cases
        if not hasattr(self, 'get_component_list'):
            # TODO: create these functions
            from trac.ticket.admin import ComponentAdminPanel
            from trac.ticket.admin import MilestoneAdminPanel
            from trac.wiki.admin import WikiAdmin

            self.ComponentAdminPanel = ComponentAdminPanel(self.env)
            self.get_component_list = self.ComponentAdminPanel.get_component_list
            self._do_component_remove = self.ComponentAdminPanel._do_remove
            self.MilestoneAdminPanel = MilestoneAdminPanel(self.env)
            self.get_milestone_list = self.MilestoneAdminPanel.get_milestone_list
            self._do_milestone_remove = self.MilestoneAdminPanel._do_remove
            self.WikiAdmin = WikiAdmin(self.env)
            self._do_wiki_load = self.WikiAdmin.load_pages

            
    def list(self, field):
        """
        list fields of a particular type
        """
        # XXX these fucntions are no longer in trunk
        list_functions = { 'component': self.get_component_list,
                           'milestone': self.get_milestone_list, 
                           }

        assert field in list_functions
        return list_functions[field]()

    def remove(self, field, name):
        """
        remove a field of a type with a particular name
        """
        # XXX these fucntions are no longer in trunk
        remove_functions = { 'component': self._do_component_remove,
                             'milestone': self._do_milestone_remove,
                             }

        assert field in remove_functions
        remove_functions[field](name)
        

    def delete_all(self, fields=('component', 'milestone')):
        """delete all default cruft"""
        
        for field in fields:
            for value in self.list(field):
                self.remove(field, value)

    def load_pages(self, pages_dir=None):
        if pages_dir is None:
            # default Trac wiki pages
            pages_dir = pkg_resources.resource_filename('trac.wiki', 
                                                        'default-pages') 
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        self._do_wiki_load(pages_dir, cursor) # should probably make this silent
        cnx.commit()

    def add_permissions(self, permissions):
        perm = PermissionSystem(self.env)
        for agent, p in permissions.items():
            for permission in p:
                try:
                    perm.grant_permission(agent, permission)
                except:
                    continue

    def remove_permissions(self, permissions):
        perm = PermissionSystem(self.env)
        for agent, p in permissions.items():
            if '*' in p:
                p = [ i for i, j in perm.get_user_permissions(agent).items() if j]
            for permission in p:
                
                try:
                    perm.revoke_permission(agent, permission)
                except:
                    continue


def apply_permissions(envs, ini):
    munger = ConfigMunger(*ini)
    
    if munger.has_section('permissions'):
        add_permissions = dict([(i, getlist(j)) 
                                for i, j in munger['permissions'].items()])
    else:
        add_permissions = None
    if munger.has_section('remove-permissions'):
        remove_permissions = dict([(i, getlist(j)) 
                                for i, j in munger['remove-permissions'].items()])
    else:
        remove_permissions = None

    for env in envs:
        admin = TracLegosAdmin(env)
        if add_permissions:
            admin.add_permissions(add_permissions)
        if remove_permissions:
            admin.remove_permissions(remove_permissions)

def main(args=sys.argv[1:]):
    parser = OptionParser("%prog -e /path/to/env [-e /path/to/env2] [...] permissions.ini [permissions2.ini] [...]")
    parser.add_option('-e', '--env', dest='env', action='append', 
                      help="trac environment(s)")
    options, args = parser.parse_args(args)
    if not args:
        parser.error("Please specify one or more permissions .ini files")
    if not options.env:
        parser.error("Please specify one or more Trac environments")

    apply_permissions(options.env, args)
    

if __name__ == '__main__':
    main()
