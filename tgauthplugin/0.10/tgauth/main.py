# -*- coding: utf-8 -*-

# Copyright (C) 2008 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try:
    from hashlib import sha1
except ImportError:
     from sha import new as sha1

import time

from trac.core import Component, implements
from trac.config import Option
from trac.db.api import DatabaseManager
from acct_mgr.api import IPasswordStore

def epochtime(t):
    """ Return seconds from epoch from a datetime object """
    return int(time.mktime(t.timetuple()))

# When adding option to auth against TG in a different db
# use the following
# cnx = TgDatabaseManager(self.env).get_connection()

class TgAuthStore(Component):
    """ IPasswordStore implementation for authentication against TG """

    implements(IPasswordStore)

    tg_schema = Option('account-manager', 'tg_schema', None,
                         'Schema containing TG tables.')

    # This is here so that the account manager Configuratino page will pick 
    # it up.
    tg_database = Option('account-manager', 'tg_database', None, 
                            'Database URI for the TG database to auth ' \
                            'against')
    def __init__(self):
        self.table = self.tg_schema and self.tg_schema + '.tg_user' or \
                    'tg_user'

    def config_key(self):
        """ Deprecated """

    def get_users(self, populate_session=True):
        """ Pull list of current users from PhpBB3 """
        cnx = self.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT user_name, email_address, created, display_name'
                    '  FROM %s WHERE active = True' % self.table)
        userinfo = [u for u in cur]
        cnx.close()
        print userinfo
        if populate_session:
            self._populate_user_session(userinfo)
        return [u[0] for u in userinfo]

    def has_user(self, user):
        """ Check for a user in TG """
        cnx = self.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT user_name FROM %s WHERE active = True'
                    ' AND user_name = %%s' % self.table, (user,))
        result = [u for u in cur]
        cnx.close()
        return result and True or False

#    def set_password(self, user, password):
#        """ Set the password for the selected user. """
#        # Implement later

    def check_password(self, user, password):
        """ Checks the password for the user against PhpBB3

        phpBB3 uses the Portable PHP Password Hashing Framework
        from http://www.openwall.com/phpass/

        Fortunately, there is a python library for hashing provided
        by Alexander Chemeris.
        """
        hashed = self._get_pwhash(user)
        if not hashed:
            return False
        self._populate_user_session(self._get_userinfo(user))
        return sha1(password).hexdigest() == hashed

    def delete_user(self, user):
        """ Delete the user """
        # Imlement later
        return False

    def get_db_cnx(self):
        """ Return a connection to the database for TG access """
        if self.tg_database:
            cnx = TgDatabaseManager(self.env).get_connection()
        else:
            cnx = self.env.get_db_cnx()
        return cnx

    def _get_pwhash(self, user):
        """ Return the password hash from the database """
        cnx = self.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT password'
                    '  FROM %s'
                    ' WHERE active = True'
                    '   AND user_name = %%s' % self.table, (user,))
        result = cur.fetchone()
        pwhash = result and result[0] or None
        cnx.close()
        return pwhash

    def _get_userinfo(self, user):
        """ Pull user info from TG """
        cnx = self.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT user_name, email_address, created, display_name'
                    '  FROM %s WHERE active = True AND user_name = %%s'
                    % self.table, (user,))
        userinfo = [u for u in cur]
        cnx.close()
        return userinfo

    def _populate_user_session(self, userinfo):
        """ Create user session entries and populate email and last visit """

        # Kind of ugly.  First try to insert a new session record.  If it
        # fails, don't worry, means it's already there.  Second, insert the
        # email address session attribute.  If it fails, don't worry, it's
        # already there.
        cnx = self.get_db_cnx()
        for uname, email, lastvisit, name in userinfo:
            try:
                cur = cnx.cursor()
                cur.execute('INSERT INTO session (sid, authenticated, '
                            'last_visit) VALUES (%s, 1, %s)',
                            (uname, epochtime(lastvisit)))
                cnx.commit()
            except:
                cnx.rollback()
            try:
                cur = cnx.cursor()
                cur.execute("INSERT INTO session_attribute"
                            "    (sid, authenticated, name, value)"
                            " VALUES (%s, 1, 'email', %s)",
                            (uname, email))
                cnx.commit()
            except:
                cnx.rollback()
            try:
                cur = cnx.cursor()
                cur.execute("INSERT INTO session_attribute"
                            "    (sid, authenticated, name, value)"
                            " VALUES (%s, 1, 'name', %s)",
                            (uname, name))
                cnx.commit()
            except:
                cnx.rollback()
            continue
        cnx.close()
         


class TgDatabaseManager(DatabaseManager):
    """ Class providing access to the PHP databse """

    connection_uri = Option('account-manager', 'tg_database', None, 
                            'Database URI for the TG database to auth ' \
                            'against')

    
