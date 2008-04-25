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

import hashlib

from trac.core import Component, implements
from trac.config import Option
from acct_mgr.api import IPasswordStore

# When adding option to auth against TG in a different db
# use the following
# cnx = TgDatabaseManager(self.env).get_connection()

class TracAuthStore(Component):
    """ IPasswordStore implementation for authentication against TG """

    implements(IPasswordStore)

    tg_schema = Option('account-manager', 'tg_schema',  
                         'Schema containing TG tables.')

    def config_key(self):
        """ Deprecated """

    def get_users(self, populate_session=True):
        """ Pull list of current users from PhpBB3 """
        cnx = self.env.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT user_name, email_address, created'
                    '  FROM tg_user WHERE active = True')
        userinfo = [u for u in cur]
        cnx.close()
        if populate_session:
            self._populate_user_session(userinfo)
        return [u[0] for u in userinfo]

    def has_user(self, user):
        """ Check for a user in TG """
        cnx = self.env.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT user_name FROM tg_user WHERE active = True'
                    ' AND user_name = %s', (user,))
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
        return hashlib.sha1(password).hexdigest() == hashed

    def delete_user(self, user):
        """ Delete the user """
        # Imlement later
        return False

    def _get_pwhash(self, user):
        """ Return the password hash from the database """
        cnx = self.env.get_db_cnx()
        cur = cnx.cursor()
        cur.execute('SELECT password'
                    '  FROM tg_user'
                    ' WHERE active = True'
                    '   AND user_name = %s', (user,))
        result = cur.fetchone()
        pwhash = result and result[0] or None
        cnx.close()
        return pwhash

    def _populate_user_session(self, userinfo):
        """ Create user session entries and populate email and last visit """

        # Kind of ugly.  First try to insert a new session record.  If it
        # fails, don't worry, means it's already there.  Second, insert the
        # email address session attribute.  If it fails, don't worry, it's
        # already there.
        cnx = self.env.get_db_cnx()
        for uname, email, lastvisit in userinfo:
            try:
                cur = cnx.cursor()
                cur.execute('INSERT INTO session (sid, authenticated, '
                            'last_visit) VALUES (%s, 1, %s)',
                            (uname, lastvisit))
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
            continue
        cnx.close()
         


class TgDatabaseManager(DatabaseManager):
    """ Class providing access to the PHP databse """

    connection_uri = Option('account-manager', 'phpbb_database', None, 
                            'Database URI for the phpBB database to auth ' \
                            'against')

    
