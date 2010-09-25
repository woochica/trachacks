#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User renamer for the Trac Watchlist Plugin.
Version 1.0 from 24th Sep 2010
Renames a users name in all DB tables created by the watchlist plugin.

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

def rename_user(envpath, oldname, newname):
    """Deletes all watchlist DB entries => Uninstaller"""
    from  trac.env   import  Environment
    try:
        env = Environment(envpath)
    except:
        print "Given path '%s' seems not to be a Trac environment." % envpath
        sys.exit(3)

    db = env.get_db_cnx()
    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE watchlist
            SET wluser=%s
            WHERE wluser=%s
        """, (newname,oldname))
        cursor.execute("""
            UPDATE watchlist_settings
            SET wluser=%s
            WHERE wluser=%s
        """, (newname,oldname))
        print "Renamed user '%s' to '%s'." % (oldname,newname)
        db.commit()
    except Exception as e:
        db.rollback()
        print "Could not rename user: " + unicode(e)
        print "Does the new user already exists?"
        sys.exit(3)

    db.commit()
    print "Finished."


def usage():
    """Trac Watchlist Plugin User Renamer v1.0 from 24th Sep 2010
     Usage: python uninstall.py [options] /path/to/trac/environment oldname newname
     Options:
       -h,--help      This help text
       -V,--version   Prints version number and copyright statement
    """
    print usage.__doc__


def main(argv):
    envpath = None
    try:
        opts, args = getopt.gnu_getopt(argv, 'hV',
                ['help', 'version'])
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
    if len(args) != 3:
        print "ERROR: wrong number of arguments!"
        usage()
        sys.exit(2)
    else:
        envpath = args[0]
        oldname, newname = args[1:]

    print "This will rename watchlist user '%s' to '%s'" % (oldname,newname)
    sys.stdout.write("Are you sure? y/N: ")
    if sys.stdin.readline().strip().lower() == 'y':
        rename_user(envpath, oldname, newname)
    sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])

# EOF
