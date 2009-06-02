#!/usr/bin/env python
"""
database interfaces for making new trac projects with TracLegos
"""

# XXX there is heavy overlap between here and repository.py
# maybe these can be abstracted

import pkg_resources
import subprocess

from paste.script.templates import var

class DatabaseCreationError(Exception):
    """marker exception for errors on database creation"""

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

    def config(self):
        """return template form of the db_string"""
        # XXX maybe this should just replace db_string?
        return { 'trac': { 'database': self.db_string() } }

    def db_string(self):
        """returns the string as needed for trac.ini:
        
        [trac]
        database = sqlite:db/trac.db
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

    def db_string(self):
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
        except OSError:
            return False
        try:
            import MySQLdb
        except ImportError:
            return False
        return True

    def db_string(self):
        return 'mysql://${database_user}:${database_password}@localhost:${mysql_port}/%s${project}' % self.prefix

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


class PostgreSQL(DatabaseSetup):
    """PostgreSQL database using psycopg2 bindings"""
    # see:
    # * http://trac.edgewall.org/wiki/DatabaseBackend#Postgresql
    # * http://trac.edgewall.org/wiki/PostgresqlRecipe

    # XXX unfinished
    prefix = 'trac_' # prefix to prepend database names with
    options = [ var('database_user', 'name of the database user',
                    default='trac'),
                var('database_admin', 'name of database root user (admin)',
                    default='postgres'),
#                var('postgres_port', 'port where MySQL is served',
#                    default='5432')
                ]

    
    def enabled(self):

        # ensure the psycopg2 python library is installed
        try: 
            import psycopg2
        except ImportError:
            return False

        # ensure that the necessary commands are installed
        for command in ["createuser", "createdb"]:
            if subprocess.call([command, "--help"], stdout=subprocess.PIPE):
                return False

        return True
                
    def db_string(self):
        """trac.ini string to connect to the PostgreSQL DB"""
#        return 'postgres://${database_user}:${database_password}@localhost:${postgres_port}/%s${project}?schema=schemaname' %  self.prefix
        return 'postgres://${database_user}:@/%s${project}' %  self.prefix

    def setup(self, **vars):
        """create a postgres db"""

        # commands to create the database
        commands = [ ["createuser", "--username", vars['database_admin'], "--createdb", "--superuser", "--createrole", vars['database_user'],],
                     
                     ["createdb", "-E", "UTF8", "--owner", vars['database_user'], self.prefix + vars['project']]
                     ]

        # run the commands
        for command in commands:
            retval = subprocess.call(command)
            if retval:
                raise DatabaseCreationError('PostgreSQL: Error executing command: "%s"' % ' '.join(command))


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
