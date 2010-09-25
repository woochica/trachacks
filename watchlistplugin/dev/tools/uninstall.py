#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Uninstaller for the Trac Watchlist Plugin.
Version 1.0 from 24th Sep 2010
Removes all DB tables created by the watchlist plugin.

Plugin website:  http://trac-hacks.org/wiki/WatchlistPlugin
Trac website:    http://trac.edgewall.org/

Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the GNU General Public License see
<http://www.gnu.org/licenses/>.

$Id$
"""

import sys
import getopt

def delete_watchlist_tables(envpath, tables=('watchlist','watchlist_settings','system'), user=None):
    """Deletes all watchlist DB entries => Uninstaller"""
    from  trac.env   import  Environment
    try:
        env = Environment(envpath)
    except:
        print "Given path '%s' seems not to be a Trac environment." % envpath
        sys.exit(3)

    db = env.get_db_cnx()

    if user is not None:
        cursor = db.cursor()
        if 'watchlist' in tables:
            try:
                cursor.execute("DELETE FROM watchlist WHERE wluser=%s", (user,))
                print "Deleted user entries from 'watchlist' table."
            except Exception as e:
                db.rollback()
                print "Could not delete user entry from 'watchlist' table: "\
                    + unicode(e)
        cursor = db.cursor()
        if 'watchlist_settings' in tables:
            try:
                cursor.execute("DELETE FROM watchlist_settings WHERE wluser=%s", (user,))
                print "Deleted user entries from 'watchlist_settings' table."
            except Exception as e:
                db.rollback()
                print "Could not delete user entry from 'watchlist_settings' table: "\
                    + unicode(e)

        db.commit()
        print "Finished."
        return


    if 'watchlist' in tables:
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE watchlist")
            print "Deleted 'watchlist' table."
        except:
            db.rollback()
            print "No 'watchlist' table for deletion found."

    if 'watchlist_settings' in tables:
        cursor = db.cursor()
        try:
            cursor.execute("DROP TABLE watchlist_settings")
            print "Deleted 'watchlist_settings' table."
        except:
            db.rollback()
            print "No 'watchlist_settings' table for deletion found."

    if 'system' in tables:
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM system WHERE name='watchlist_values'")
            print "Deleted watchlist version entry from system table."
        except Exception as e:
            db.rollback()
            print "Could not delete 'watchlist_version' from 'system' table: "\
                  + unicode(e)

    db.commit()
    print "Finished."


def usage():
    """Trac Watchlist Plugin Uninstaller v1.0 from 24th Sep 2010
     Usage: python uninstall.py [options] /path/to/trac/environment [options]
     Options:
       -h,--help      This help text
       -V,--version   Prints version number and copyright statement
       -u,--user <user>
                      Only remove entries of given user
       -t,--tables <tables>
                      Only removes/uninstalls given tables (default: all).
     Tables:
       watchlist, watchlist_settings, system
    """
    print usage.__doc__


def main(argv):
    envpath = None
    tables = ['watchlist','watchlist_settings','system']
    user = None
    try:
        opts, args = getopt.gnu_getopt(argv, 'hVt:u:',
                ['help', 'version', 'tables=', 'user='])
    except getopt.GetoptError as e:
        print unicode(e)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-V', '--version'):
            print __doc__
            sys.exit()
        elif opt in ('-t', '--tables'):
            tables = arg.split(',')
        elif opt in ('-u', '--user'):
            user = arg
    if len(args) < 1:
        print "Error: No trac environment given!"
        usage()
        sys.exit(2)
    else:
        envpath = args[0]

    wtables = [ t for t in tables if t != 'system' ]
    U = ''
    if user is not None:
        U = "all entries of user '%s' from " % user
    print "This will delete " + U + "the following tables: " + ', '.join(wtables or ['none'])
    if 'system' in tables and not U:
        print "and remove the 'watchlist_version' from the 'system' table."
    sys.stdout.write("Are you sure? y/N: ")
    if sys.stdin.readline().strip().lower() == 'y':
        delete_watchlist_tables(envpath, tables, user)
    sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
