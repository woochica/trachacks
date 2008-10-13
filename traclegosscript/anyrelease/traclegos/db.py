#!/usr/bin/env python
"""
database interfaces for making new trac projects with TracLegos
"""

# XXX there is heavy overlap between here and repository.py
# maybe these can be abstracted

import pkg_resources
import subprocess

from paste.script.templates import var

class DatabaseSetup(object):
    """interface defining database setup using TracLegos"""

    options = []

    def __init__(self):
        self.name = self.__class__.__name__
        if not hasattr(self, 'description'):
            self.description = self.__doc__ 

    def enabled(self):
        """
        is this type of database capable of being created
        on this computer?
        """
        return False

    def db_string(self, **vars):
        """returns the string as needed for trac.ini's
        
        [trac]
        database = sqlite:db/trac.db

        parameter
        """
        # XXX could return more general options a la repository.py
        raise NotImplementedError
    

    def setup(self, **vars):
        """initial creation and setup of the database, if necessary"""
        return


class SQLite(DatabaseSetup):
    """trac sqlite database"""

    def enabled(self):
        return True

    def db_string(self, **vars):
        return 'sqlite:db/trac.db'


class MySQL(DatabaseSetup):
    """MySQL database"""
    prefix = 'trac_' # prefix to prepend database names with
    options = [ var('database_user', 'name of the database user',
                    default='trac'),
                var('database_password', 'user password for the database'),
                var('database_admin', 'name of database root user (admin)',
                    default='root'),
                var('database_admin_password', 'password for the admin user'),
                var('mysql_port', 'port where MySQL is served',
                    default='3306')
                ]

    def enabled(self):
        try:
            subprocess.call(['mysql', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except OSError:
            return False

    def db_string(self, **vars):
        return 'mysql://${database_user}:${database_password}@localhost:${mysql_port}/${project}'

    def setup(self, **vars):
        """create and grant priveleges on a MySQL db"""

        vars = vars.copy()
        vars['database'] = self.prefix + vars['project']

        sql = """create database %(database)s;
grant all privileges on %(database)s.* to %(database_user)s@localhost identified by '%(database_password)s';
""" % vars

        command = ['mysql', '-u', vars['database_admin']]
        password = vars['database_admin_password']
        if password:
            command.append('--password=%s' % password)

        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        process.communicate(input=sql)


# TODO: postgresql


def available_databases():
    """return installed and enabled database setup methods"""
    databases = []
    for entry_point in pkg_resources.iter_entry_points('traclegos.database'):
        try:
            database = entry_point.load()
        except:
            continue
        database = database()
        if database.enabled():
            databases.append(database)
    return dict((database.name, database) for database in databases)


if __name__ == '__main__':
    print 'Available databases:'
    for name, database in available_databases().items():
        print '%s: %s' % (name, database.description)
