#! /usr/bin/env python

# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/SqliteToPgScript
#
# Basically, it boils down to: feel free to use/modify/distribute/etc.
# However, give me credit where due.  Also, if you like the script and
# find it useful, buy me a soda or candy bar or something if ever we
# meet. Thanks and enjoy.
#
# Author: John Hampton <pacopablo@asylumware.com>
#
# * 02/27/2008
#
#  Renewed for mysql.
#
# http://trac-hacks.org/wiki/SqliteToMySqlScript
#
# Author: Kyosuke Takayama <support@mc.neweb.ne.jp>

import os, os.path, sys
from trac.env import Environment
from trac.db import DatabaseManager
from optparse import OptionParser
from MySQLdb import ProgrammingError

class TableMigration(object):
    """
        Class to conatin all table migration functions
    """
    def __init__(self, sqlenv, myenv, opts):
        """ Create a TableMigration instance.  Required are SQLite and
            MySQL environment objects
        """
        self.sqlenv = sqlenv
        self.myenv = myenv
        self.opts = opts
        self.sdb = self.sqlenv.get_db_cnx()
        self.mydb = self.myenv.get_db_cnx()
        pass

    def lookupMethod(self, table):
        """ Get a reference to the function that handles migration for the
            specified table
        """
        m = getattr(self, ''.join(['migrate_', table.upper()]), None)
        if not m:
            m = self.default_copy 
        return m

    def cleanTable(self, table):
        """ Clear the contents of the table """
        cur = self.mydb.cursor()
        delete_from = "DELETE FROM %s" % table
        cur.execute(delete_from)

    def migrateTable(self, table):
        """ Migrate the table specified. """
        if not self.opts.noclean:
            self.cleanTable(table)
        m = getattr(self, ''.join(['migrate_', table.upper()]), None)
        if not m:
            rc = self.default_copy(table)
        else:
            rc = m()
        return rc

    def default_copy(self, table):
        """ Copy the table from the sqlite db to the mysql db """
        select_all = "SELECT * FROM %s" % table
        scur = self.sdb.cursor()
        mycur = self.mydb.cursor()
        scur.execute(select_all)
        cols = scur.description
        if not cols:
            return True
        subs = ["%s" for x in range(len(cols))]
        insert_into = ''.join([ "INSERT INTO ", table, " VALUES (",
                                ','.join(subs), ")"])
        rows = row_exists = 0
        for row in scur:
            rows += 1
            try:
                mycur.execute(insert_into, row)
            except (ProgrammingError, IntegrityError):
                row_exists += 1
            continue
        if row_exists:
            print "%s of %s rows already existed in the %s table" % \
                  (str(row_exists), str(rows), table)
        self.mydb.commit()
        return row_exists > 0

    def migrate_PERMISSION(self):
        """
            Migrate permission table
        """
        scur = self.sdb.cursor()
        mycur = self.mydb.cursor()
        rows = row_exists = 0
        if not self.opts.plist:
            sql_select = "SELECT * FROM permission"
        else:
            subs = []
            for x in range(len(self.opts.plist)):
                subs.append("%s")
                continue
            sql_select = ''.join([  "SELECT * FROM permission ",
                                    "WHERE username NOT IN (",
                                    ','.join(subs),
                                    ")",
                                 ])

        scur.execute(sql_select, self.opts.plist)
        sql_insert = "INSERT INTO permission VALUES (%s, %s)"
        for row in scur:
            rows += 1
            try:
                mycur.execute(sql_insert, row)
            except (ProgrammingError, IntegrityError):
                row_exists += 1
            continue
        if row_exists:
            print "%s of %s rows already existed in the permission table" % (str(row_exists), str(rows))
        self.mydb.commit()
        return row_exists > 0

    def migrate_WIKI(self):
        """
            Migrate wiki table
        """
        scur = self.sdb.cursor()
        mycur = self.mydb.cursor()
        rows = row_exists = 0
        if not self.opts.wlist:
            sql_select = "SELECT * FROM wiki"
        else:
            subs = []
            for x in range(len(self.opts.wlist)):
                subs.append("%s")
                continue
            sql_select = ''.join([  "SELECT * FROM wiki ",
                                    "WHERE name NOT IN (",
                                    ','.join(subs),
                                    ")",
                                 ])

        scur.execute(sql_select, self.opts.wlist)
        sql_insert = "INSERT INTO wiki VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        for row in scur:
            rows += 1
            try:
                mycur.execute(sql_insert, row)
            except (ProgrammingError, IntegrityError):
                row_exists += 1
            continue
        if row_exists:
            print "%s of %s rows already existed in the wiki table" % (str(row_exists), str(rows))
        self.mydb.commit()
        return row_exists > 0

def getAllTables(env):
    """ Queries the MySQL database for a list of tables """
    cnx = env.get_db_cnx()
    cur = cnx.cursor()
    select_tables = "show tables;"
    cur.execute(select_tables)
    cnx.commit()
    return [table[0] for table in cur]

def getSQLiteEnvironment(opts): 
    """ Create an Environment connected to the SQLite database """

    dburi = opts.sqlite_uri
    env = Environment(opts.tracenv)
    env.config.set('trac', 'database', dburi)
    return env

def getMySQLEnvironment(opts):
    dburi = opts.mysql_uri
    env = Environment(opts.tracenv)
    env.config.set('trac', 'database', dburi)
 
    try:
        cnx = env.get_db_cnx()
        cur = cnx.cursor()
        cur.execute("select value from system where name = 'database_version'");
    except ProgrammingError:
       cnx.rollback()
       DatabaseManager(env).init_db()
       DatabaseManager(env).shutdown()
 
#    if env.needs_upgrade():
#        env.upgrade()
    return env

def main(opts):
    rc = 0
 
    sqlenv = getSQLiteEnvironment(opts)
    myenv = getMySQLEnvironment(opts)
    tmigration = TableMigration(sqlenv, myenv, opts)
    if not opts.tlist:
        opts.tlist = getAllTables(myenv)
    for tname in opts.tlist:
        try:
            rc = tmigration.migrateTable(tname) or rc
        except AttributeError:
            print "Migration of %s has not been implemented" % tname
            pass
        continue
    
    return rc

def getArgs():
    usage ="usage: %prog [options] [site]"
    description="%prog is used to migrate data from SQLite to MySQL."

    parser = OptionParser(usage=usage, description=description)

    parser.add_option("-e", "--tracenv", dest="tracenv", type="string",
                        help="Path to trac environment",
                        metavar="<path>")
    parser.add_option("-m", "--migrate", dest="migrate", type="string",
                        help="Comma separated list of tables to migrate",
                        metavar="<list>", default=None)
    parser.add_option("", "--exclude_perms", dest="perms_exclude", 
                        type="string", help="Comma separated list of users to "
                        "exclude from permission migration", metavar="<list>")
    parser.add_option("-w", "--wikipages", dest="wikipages", type="string",
                        help="Comma separated list of wiki page names to "
                        "ommit from the migration", metavar="<list>")
    parser.add_option("-p", "--mysql_uri", dest="mysql_uri", type="string",
                        help="DB URI for MySQL database",
                        metavar="<uri>")
    parser.add_option("-s", "--sqlite_uri", dest="sqlite_uri", type="string",
                        help="DB URI for SQLite database",
                        metavar="<uri>", default="sqlite:db/trac.db")
    parser.add_option("", "--noclean", dest="noclean", action="store_true",
                        help="Do not clear MySQL tables before transfer",
                        default=False)

    (options, args) = parser.parse_args()
    if not options.tracenv:
        if  not options.tracbase:
            print ("You must specify the --tracenv or the --tracbase option")
            sys.exit(1)
        else:
            if len(args) < 1:
                print ("You must specify a project name\n")
                sys.exit(1)
            options.project = args[0]
            options.tracenv = os.path.join(options.tracbase, args[0])

    if not options.mysql_uri.startswith('mysql://'):
        print ("You must specify a valid URI for the MySQL database.")
        print ("  eg. mysql://user:password@localhost/dbname")
        sys.exit(1)

    if not options.sqlite_uri.startswith('sqlite:'):
        print ("You must specify a valid URI for the SQLite database.")
        print ("  eg. sqlite:db/trac.db")
        sys.exit(1)

    options.args = args
    options.tlist = options.migrate and \
                    [t.strip() for t in options.migrate.strip().split(',')]
    options.wlist = options.wikipages and \
                    [w.strip() for w in options.wikipages.strip().split(',')] \
                    or []
    options.plist = options.perms_exclude and \
                    [p.strip() for p in options.perms_exclude.strip().split(',')] \
                    or []

    return options

if __name__ == '__main__':
   main(getArgs())
   sys.exit(0)
