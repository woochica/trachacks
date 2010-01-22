#!/usr/bin/env python

"""
RenameTracUsers:
a plugin for Trac to rename users
http://trac.edgewall.org
"""

# TODO : Changing the cc fields -- ticket.cc || WHERE ticket_change.field = cc
#  cc fields are lists, containing other logins/e-mails as well
#  $query .= 'UPDATE ticket SET cc = REPLACE("cc", "' . $oldlogin .  '", "' . $newlogin . '") WHERE cc LIKE "%' . $oldlogin . '%";';

import os
import sys
from optparse import OptionParser
from trac.core import *
from trac.env import open_environment

class RenameTracUsers(object):

    tables = { 'attachment': 'author',
               'component': 'owner',
               'permission': 'username',
               'revision': 'author',
               'session': 'sid',
               'session_attribute': 'sid',
               'ticket': ['owner', 'reporter'],
               'ticket_change': 'author',
               'ticket_time': ['worker', 'submitter'],
               'wiki': 'author',
               }

    unique = { 'auth_cookie': ['name'],
               'permission': ['username'],
               'session': ['sid'],
               'session_attribute': ['sid'],
               }

    def __init__(self, env):
        self.env = env

    def rename(self, old_login, new_login):
        """
        rename one user
        """

        # ticket_change require special attention
        db = self.env.get_db_cnx()
        cur = db.cursor()
        cur.execute("UPDATE ticket_change SET  oldvalue='%s' WHERE field='owner' AND oldvalue='%s'" % (new_login, old_login))
        cur.execute("UPDATE ticket_change SET  newvalue='%s' WHERE field='owner' AND newvalue='%s'" % (new_login, old_login))
        db.commit()
        db.close()

        for table, fields in self.tables.items():

            try:
                db = self.env.get_db_cnx()
                cur = db.cursor()
                cur.execute("SELECT * FROM %s LIMIT 1" % table)
                db.commit()
                db.close()
            except:
                continue
            

            if isinstance(fields, basestring):
                fields = [ fields ] 

            for field in fields:

                if field in self.unique.get(table, []):
                    db = self.env.get_db_cnx()
                    cur = db.cursor()
                    cur.execute("DELETE FROM %s WHERE %s='%s'" % (table, field, old_login))
                    db.commit()
                    db.close()

                try:
                    db = self.env.get_db_cnx()
                    cur = db.cursor()
                    
                    # XXX this should work, but it doesn't, so instead do this the retarded way (thank you, SQL!)
                    # cur.execute("UPDATE %s SET %s=%s WHERE %s=%s", (table, field, new_login, field, old_login))
                    
                    cur.execute("UPDATE %s SET %s='%s' WHERE %s='%s'" % (table, field, new_login, field, old_login))
                    db.commit()
                    db.close()
                except:
                    # i hate SQL
                    raise
                    import pdb; pdb.set_trace()

    def rename_users(self, users):
        """
        rename several users;
        * users: a dictionary of old_login, new_login
        """
        for old_login, new_login in users.items():
            self.rename(old_login, new_login)

def main(args=sys.argv[1:]):
    parser = OptionParser('%prog [options] project <project2> <project3> ...')
    parser.add_option('-d', '--dict', dest='dict', default=None,
                      help="python file mapping of old user, new user")
    options, args = parser.parse_args(args)

    # if no projects, print usage
    if not args:
        parser.print_help()
        sys.exit(0)

    # get the environments
    envs = []
    for arg in args:
        env = open_environment(arg)
        envs.append(env)

    # get the users
    assert options.dict
    assert os.path.exists(options.dict)
    users = eval(file(options.dict).read())
    assert isinstance(users, dict)
    if not users:
        sys.exit(0) # nothing to do

    # change the permissions
    for env in envs:
        renamer = RenameTracUsers(env)
        renamer.rename_users(users)

if __name__ == '__main__':
    main()
    
    


