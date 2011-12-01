# -*- coding: utf-8 -*-

from datetime import datetime
import inspect
import re
import sys
import time

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

revision="$Rev$"
url="http://trac-hacks.org/wiki/UserStatsMacro"

class UserStatsMacro(WikiMacroBase):
    """Produces a table with username, last login, elapsed time since last
    login for each user.

    Usage:
    {{{
    [[UserStats]]
    }}}

    """

    def expand_macro(self, formatter, name, content):

        dt = self.get_users_last_login()
        content = format_to_html(self.env, formatter.context, dt)
        content = '<div class="component-list">%s</div>' % content
        return content

    def get_user_last_login(self,user):

        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT last_visit FROM session "
                       "WHERE sid=%s AND authenticated=%s",
                       (user, 1))
        row = cursor.fetchone()
        if not row:
            return

        when = time.localtime(int(row[0]))
        last = datetime.fromtimestamp(int(row[0]))
        now = datetime.fromtimestamp(time.time())
        how_long = now - last
        last_date = time.strftime("%Y/%m/%d %H:%M:%S", when)
        if how_long.days>0:
            return "|| [query:?status=assigned&status=new&status=reopened&group=milestone&order=priority&col=id&col=summary&col=status&col=owner&col=type&col=priority&col=component&col=due_close&type=task&owner=%s %s] || %s || %s day(s)||\n" % (user, user, last_date, how_long.days)
        else:
            return "|| [query:?status=assigned&status=new&status=reopened&group=milestone&order=priority&col=id&col=summary&col=status&col=owner&col=type&col=priority&col=component&col=due_close&type=task&owner=%s %s]|| %s || <24h ||\n" % (user, user,last_date)
    
    def get_users_last_login(self):

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        result = set()
        dt = "||'''User'''||'''Last Login'''||'''How long ago'''||\n"
        users = set([u[0] for u in self.env.get_known_users()])
        for user in sorted(users):
            dt += self.get_user_last_login(user) 
        return dt

