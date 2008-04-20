# -*- coding: utf-8 -*-

# Copyright (c) 2008 John Hampton <pacopablo@pacopablo.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Sponsored by Cobra <http://cobra-language.com>

from trac.core import Component, implements
from trac.db.api import DatabaseManager
from acct_mgr.api import IPasswordStore

from phpbbauth.phpass import crypt_private

class PhpBBAuthStore(Component):
    """ IPasswordStore implementation for authentication against PhpBB3

    Sponsored by Cobra <http://cobra-language.com>
    """

    implements(IPasswordStore)

    hash_prefix = Option('account-manager', 'phpbb_hash_prefix', '$H$', 
                         'Hash prefix used for phpBB passwords.')

    def config_key(self):
        """ Deprecated """

    def get_users(self):
        """ Pull list of current users from PhpBB3 """
        cnx = PhpDatabaseManager(self.env).get_connection()
        cur = cnx.cursor()
        cur.execute('SELECT username FROM phpbb_users WHERE user_type <> 2')
        cnx.close()
        return cur and [u for u in cur] or []

    def has_user(self, user):
        """ Check for a user in PhpBB3 """
        cnx = PhpDatabaseManager(self.env).get_connection()
        cur = cnx.cursor()
        cur.execute('SELECT username FROM phpbb_users WHERE user_type <> 2'
                    ' AND username = %s', (user,))
        cnx.close()
        return cur and True or False

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
        return crypt_private(password, hashed, self.hash_prefix) == hashed

    def delete_user(self, user):
        """ Delete the user """
        # Imlement later
        return False

    def _get_pwhash(self, user):
        """ Return the password hash from the database """
         


class PhpDatabaseManager(DatabaseManager):
    """ Class providing access to the PHP databse """

    connection_uri = Option('account-manager', 'phpbb_database', None, 
                            'Database URI for the phpBB database to auth ' \
                            'against')

    
