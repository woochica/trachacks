from trac.core import *
from trac.admin.api import IAdminCommandProvider
import os
from ConfigParser import ConfigParser
import sys
import shutil
import re
from zipfile import ZipFile
from trac.attachment import Attachment
from trac.util.text import unicode_unquote

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
 - `plugin replace <plugin_name>`: Replaces plugin(s) with plugin name (without version)
 - `plugin replaceall`: Replaces all (!) plugins (dangerous!)
 
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
# replaces plugin TracAccountManager
trac-admin </path/to/projenv> plugin replace TracAccountManager
# removes all plugins (and made a backup) 
# then copies all plugin of current directory into plugins-directory  
trac-admin </path/to/projenv> plugin replaceall
}}}
"""
    implements(IAdminCommandProvider)
    
    # IAdminCommandProvider methods
    def get_admin_commands(self):
        yield ('component removeall', '<pattern>',
               'Remove all components with a specific pattern [settingsplugin]',
               None, self._do_remove_all_components)
        yield ('milestone removeall', '<pattern>',
               'Remove all milestones with a specific pattern [settingsplugin]',
               None, self._do_remove_all_milestones)
        yield ('version removeall', '<pattern>',
               'Remove all versions with a specific pattern [settingsplugin]',
               None, self._do_remove_all_versions)
        yield ('permission removeall', '<user_pattern>',
               'Remove all permissions of users with a specific pattern [settingsplugin]',
               None, self._do_remove_all_permissions)
        yield ('ticket_type removeall', '<pattern>',
               'Remove all ticket_types with a specific pattern [settingsplugin]',
               None, self._do_remove_all_ticket_types)
        yield ('priority removeall', '<pattern>',
               'Remove all priorities with a specific pattern [settingsplugin]',
               None, self._do_remove_all_prioritys)
        yield ('config setall', '<path_to_file>',
               'Sets all configs from a file [settingsplugin]',
               None, self._set_config_all)
        yield ('plugin replace', '<plugin_name>',
               "Replaces plugin(s) with plugin name (without version) [settingsplugin]",
               None, self._replace_plugin)
        yield ('plugin replaceall', None,
               'Replaces all (!) plugins (dangerous!) [settingsplugin]',
               None, self._replace_all_plugins)
        yield ('attachment unused', '<options>',
               'Removes unused attachments (dangerous!); options: [list | remove] [settingsplugin]',
               None, self._do_remove_attachments)
    
    
    def _do_remove_attachments(self, options):
        """Hack for removing attachments.

See Trac-ticket 10313 for detail discussion 
(http://trac.edgewall.org/ticket/10313#comment:67).
"""
        if options: 
            self._do_remove_unused_attachments(options)
        else:
            print "No option set!"
            print "Please specify one of these options: [unreachable | unused]" 
    
        
    def _do_remove_unused_attachments(self, options):
        """Backups and removes unused attachments.
        
Attachments could be unreachable (and thus unused):
- if file name has some special character, e.g. '~' in file2.~pdd
- if anyone has created (sub-) directories in tickets attachments 
(because of migration of old system, for example) 
- if file(s) has been renamed / moved 
"""
        @self.env.with_transaction()
        def do_remove(db):
            cnt = 0
            backup = None
            
            if options == 'remove':
                if not os.access(self.env.path, os.W_OK):
                    out.write( "cannot write into %s and therefore cannot make a backup!" % self.env.path)
                else:
                    backup = ZipFile(self.env.path + '/backup_unused_attachments.zip', 'w')
                
            att_path = os.path.join(self.env.path, 'attachments')
            tkt_id = -1
            
            for dir, dirs, files in os.walk(os.path.join(att_path, 'ticket')):
                try:
                    head, tail = os.path.split(dir)
                    tkt_id = int(tail)
                except: 
                    tkt_id = -1
                
                if tkt_id > 0:
                    if len(files) > 0:
                        for f in files:
                            file_path = os.path.join(dir, f)
                            if str(file_path).find("~") > -1:
                                print "Has special char: %s" % file_path
                                if backup:
                                    backup.write( file_path )
                                    os.remove(file_path)
                                    self.__remove_db_entry(f, tkt_id)
                                cnt += 1
                            elif not self.__has_db_entry( dir, f, tkt_id ):
                                print "No DB entry: %s" % file_path
                                if backup:
                                    backup.write( file_path )
                                    os.remove(file_path)
                                cnt += 1
                    
                    if len(dirs) > 0:
                         for d in dirs:
                            file_path = os.path.join(dir, d)
#                            print "Contains sub-directory: %s" % file_path
                            cnt += self.__backup_dir(backup, file_path, tkt_id)
            print "SUMMARY - removed files: %s" % cnt
    
    def __backup_dir(self, backup, dir_path, tkt_id):
        count = 0
        for dir, dirs, files in os.walk(dir_path):
            for f in files:
                file_path = os.path.join(dir, f)
                if backup:
                    backup.write( file_path )
                    os.remove( file_path )
                    head, tail = os.path.split(dir)
                    fn = os.path.join(tail, f)
                    self.__remove_db_entry(fn, tkt_id)
                print "Resides in sub-directory: %s" % file_path
                count += 1
        return count
            
    def __remove_db_entry(self, filename, tkt_id):
        try:
            fn = "%%%s" % unicode_unquote(filename)
#            print "[__remove_db_entry] fn: %s" % fn
        except:
#            print "exception using filename: %s" % filename
            fn = filename
        
        cnt = 0
        for row in self.env.db_query("""
                    SELECT count(id) FROM attachment 
                    WHERE filename like '%%%s' and id='%s'""" % (fn, tkt_id) ):
            cnt += row[0]
        
        if cnt == 1:
            sql = "DELETE FROM attachment WHERE type='%s' AND id='%s' AND filename like '%s'" % ('ticket', tkt_id, fn)
            try:
                with self.env.db_transaction as db:
                    db(sql)
            except Exception, e:
                print "SQL %s caused Exception: %s" % (sql, e)

            
    def __has_db_entry(self, dir, filename, tkt_id):
        try:
            fn = unicode_unquote(filename)
        except:
#            print "exception using filename: %s" % filename
            fn = filename
        
        for row in self.env.db_query("""
                SELECT id FROM attachment 
                WHERE filename='%s' and id='%s' ORDER BY type, id, filename""" % (fn, tkt_id) ):
            return True
        return False
            
    
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
        
        
    def _replace_all_plugins(self):
        self._do_replace_plugins('%', 'all')
        
    def _replace_plugin(self, plugin_name):
        self._do_replace_plugins(plugin_name, None)
        
    def _do_replace_plugins(self, plugin_name, flags):
        out = sys.stdout
        
        if not plugin_name:
            self.log.warning( "plugin_name is not set" )
            return
        
        if not self.env.path:
            self.log.error( "no env.path set" )
            return
        
        path_to_plugin = "%s/plugins/" % self.env.path
        if not os.access(path_to_plugin, os.W_OK):
#            self.log.warning( "cannot write into %s" % path_to_plugin )
            out.write( "ERROR: cannot write into %s \n" % path_to_plugin )
            return
        elif not os.access('.', os.R_OK):
            out.write( "ERROR: cannot access current folder \n" )
            
        # pattern to find plugin name, including version
        pattern = "%s-[a-z0-9\\-_\\.]+-py2\\.[456]\\.egg" % plugin_name
        if plugin_name == '%' and flags and flags == 'all':
            pattern = ".+-[a-z0-9\\-_\\.]+-py2\\.[456]\\.egg"
            out.write( "remove all plugins with pattern: %s \n" % pattern )
        
        full_plugin_name = None
        for file in os.listdir('.'):
            if file and re.match(pattern, file):
                full_plugin_name = file
                
        if not full_plugin_name or not os.access(full_plugin_name, os.R_OK):
#            self.log.warning( "cannot access file %s" % full_plugin_name )
            out.write( "ERROR: cannot access file %s \n" % full_plugin_name ) 
            return
        
        backup = None
        has_removed = False
        if not os.access(self.env.path, os.W_OK):
            out.write( "cannot write into %s and therefore cannot make a backup!" % self.env.path)
        else:
            backup = ZipFile(self.env.path + '/backup_plugins.zip', 'w')
        
        for file in os.listdir(path_to_plugin):
            if file and re.match(pattern, file):
                if backup:
                    backup.write(path_to_plugin + file)
                os.remove(path_to_plugin + file)
                has_removed = True
                out.write( "removed plugin: %s\n" % file )
                self.log.info( "removed plugin %s" % file )
        
        if plugin_name == '%' and flags and flags == 'all':
            for file in os.listdir('.'):
                if file and re.match(pattern, file):
                    shutil.copy(file, path_to_plugin + "/" + file)
                    self.log.info( "successfully copied plugin %s" % file )
                    out.write( "copied plugin:  %s \n" % file )
        else:
            shutil.copy(full_plugin_name, path_to_plugin + "/" + full_plugin_name)
            self.log.info( "successfully copied plugin %s" % full_plugin_name )
            out.write( "copied plugin:  %s \n" % full_plugin_name )
        
        out.write("\n")
        if backup and has_removed:
            self.log.info( "successfully made backup of removed plugins at %s" % backup.filename )
            out.write( "made backup of removed plugins at %s \n" % backup.filename )
              
        out.write( "---> Please restart server to apply changes !! \n" )
        