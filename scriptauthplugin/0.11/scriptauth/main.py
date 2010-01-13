# -*- coding: utf-8 -*-

# Copyright (c) 2010 Carsten Fuchs Software <info@cafu.de> <http://www.cafu.de>
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

import urllib
import re

from trac.core import Component, implements
from trac.config import Option
from acct_mgr.api import IPasswordStore


class ScriptAuthStore(Component):
    """ IPasswordStore implementation for authentication against web script result.
        Developed by Carsten Fuchs Software <http://www.cafu.de>
    """

    implements(IPasswordStore)

    # The account manager configuration page will pick this up.
    script_auth_url = Option('account-manager', 'script_auth_url', None,
        'The script URL pattern that will be fetched for the authentication result. '
        'Example: http://www.example.com/my_auth.php?u=<USERNAME>&p=<PASSWORD> '
        'Note that the <USERNAME> and <PASSWORD> strings will automatically be replaced by the proper user details.')


    def check_password(self, user, password):
        user_email = ""

        try:
            f = urllib.urlopen(self.script_auth_url.replace('<USERNAME>', user).replace('<PASSWORD>', password))
            auth_result = f.readline().rstrip()
            user_email  = f.readline().rstrip()
            f.close()

            # Attribute getcode() is not available in Python 2.4.
            # if f.getcode()!=200: return False;
            if auth_result!="ok": return False;

        except IOError:
            return None

        # Only use the email address if it meets a (very gross) validity test.
        if re.match("^.+@.+\\..+$", user_email)!=None:
            cnx = self.env.get_db_cnx()

            # ### FIXME: Is it ok to leave this out?? What are the consequences? ###

            # # Kind of ugly.
            # # First try to insert a new session record.
            # # If it fails, don't worry, means it's already there.
            # try:
            #     cnx.cursor().execute('INSERT INTO session (sid, authenticated, last_visit) VALUES (%s, 1, %s)', (user, lastvisit))
            #     cnx.commit()
            # except:
            #     cnx.rollback()

            # Second, insert the email address session attribute.
            # If it fails, don't worry, it's already there.
            try:
                cnx.cursor().execute("INSERT INTO session_attribute (sid, authenticated, name, value) VALUES (%s, 1, 'email', %s)", (user, user_email))
                cnx.commit()
            except:
                cnx.rollback()

            cnx.close()

        # The remote script authenticated the user.
        return True

    def get_users(self):
        return []

    def has_user(self, user):
        return False
