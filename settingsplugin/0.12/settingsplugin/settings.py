from trac.core import *
from trac.admin.api import IAdminCommandProvider
import os
from ConfigParser import ConfigParser
import sys
import shutil

class SettingsAdmin(Component):
    """Provides extension for `trac-admin` for easy removing unneeded milestones, components, etc. 
and setting a bunch of config options from file.

Extends command `trac-admin` with some more commands:

 - `component removeall <pattern>`: Remove all components with a specific pattern
 - `milestone removeall <pattern>`: Remove all milestones with a specific pattern
 - `version removeall <pattern>`: Remove all versions with a specific pattern
 - `permission removeall <user_pattern>`: Remove all permissions of users with a specific pattern
 - `ticket_type removeall <pattern>`: Remove all ticket_types with a specific pattern
 - `priority removeall <pattern>`: Remove all priorities with a specific pattern
 - `config setall <path/to/file>`: Set all config options from file to `trac.ini`
 
Pattern can have wildcards (%). Examples usage of commands:
{{{#!sh
# removes all components starting with component
trac-admin </path/to/projenv> component removeall component%
# removes ALL (!) versions
trac-admin </path/to/projenv> version removeall %
# removes all permissions of user anonymous
trac-admin </path/to/projenv> permission removeall anonymous
# overrides and creates all config entries from `company.ini`
trac-admin </path/to/projenv> config setall company.ini
}}}
"""
    implements(IAdminCommandProvider)
    
    # IAdminCommandProvider methods
    def get_admin_commands(self):
        yield ('component removeall', '<pattern>',
               'Remove all components with a specific pattern (see settingsplugin)',
               None, self._do_remove_all_components)
        yield ('milestone removeall', '<pattern>',
               'Remove all milestones with a specific pattern (see settingsplugin)',
               None, self._do_remove_all_milestones)
        yield ('version removeall', '<pattern>',
               'Remove all versions with a specific pattern (see settingsplugin)',
               None, self._do_remove_all_versions)
        yield ('permission removeall', '<user_pattern>',
               'Remove all permissions of users with a specific pattern (see settingsplugin)',
               None, self._do_remove_all_permissions)
        yield ('ticket_type removeall', '<pattern>',
               'Remove all ticket_types with a specific pattern (see settingsplugin)',
               None, self._do_remove_all_ticket_types)
        yield ('priority removeall', '<pattern>',
               'Remove all priorities with a specific pattern (see settingsplugin)',
               None, self._do_remove_all_prioritys)
        yield ('config setall', '<path_to_file>',
               'Sets all configs from a file (see settingsplugin)',
               None, self._set_config_all)
    
    def _do_remove_all_components(self, pattern):
        @self.env.with_transaction()
        def do_remove(db):
            cursor = db.cursor()
            cursor.execute("delete from component where name like '%s'" % pattern)
            db.commit()
            print "successfully removed components with name like %s" % pattern
    
    def _do_remove_all_milestones(self, pattern):
        @self.env.with_transaction()
        def do_remove(db):
            cursor = db.cursor()
            cursor.execute("delete from milestone where name like '%s'" % pattern)
            db.commit()
            print "successfully removed milestones with name like %s" % pattern
    
    def _do_remove_all_versions(self, pattern):
        @self.env.with_transaction()
        def do_remove(db):
            cursor = db.cursor()
            cursor.execute("delete from version where name like '%s'" % pattern)
            db.commit()
            print "successfully removed versions with name like %s" % pattern
    
    def _do_remove_all_permissions(self, pattern):
        @self.env.with_transaction()
        def do_remove(db):
            cursor = db.cursor()
            cursor.execute("delete from permission where username like '%s'" % pattern)
            db.commit()
            print "successfully removed permissions with user name like %s" % pattern
    
    def _do_remove_all_prioritys(self, pattern):
        @self.env.with_transaction()
        def do_remove(db):
            cursor = db.cursor()
            cursor.execute("delete from enum where type='priority' and name like '%s'" % pattern)
            db.commit()
            print "successfully removed priorities with name like %s" % pattern
    
    def _do_remove_all_ticket_types(self, pattern):
        @self.env.with_transaction()
        def do_remove(db):
            cursor = db.cursor()
            cursor.execute("delete from enum where type='ticket_type' and name like '%s'" % pattern)
            db.commit()
            print "successfully removed ticket_types with name like %s" % pattern
            
    def _set_config_all(self, path_to_file):
        out = sys.stdout
        if not os.access(path_to_file, os.R_OK):
            self.log.warning( "cannot access file %s" % path_to_file )
            return
        elif not self.env.config:
            self.log.warning( "cannot access config file trac.ini" )
            return
        
        cfg = ConfigParser()
        cfg.read(path_to_file)
        
        if os.access(self.env.path, os.W_OK):
            path_to_trac_ini = os.path.join(self.env.path, 'conf', 'trac.ini')
            shutil.copy(path_to_trac_ini, path_to_trac_ini + '.bak')
            out.write( "created a backup of trac.ini to %s.bak" % path_to_trac_ini )
            out.write('\n')
        else:
            out.write( "could not create backup of trac.ini - continue anyway? [y|n] "  )
            input = sys.stdin.readline()
            if not input or not input.strip() == 'y':
                return
        
        for sect in cfg.sections():
            for opt in cfg.options(sect):
                self.config.set(sect, opt, cfg.get(sect, opt))
                out.write( "added config [%s] %s = %s" % (sect, opt, cfg.get(sect, opt)) )
                out.write('\n')
        self.config.save()

