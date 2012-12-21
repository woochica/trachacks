# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martin Aspeli <optilude@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from pkg_resources import resource_filename
from StringIO import StringIO

from trac.core import implements
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.macros import WikiMacroBase
from trac.util.html import Markup

class SQLScalar(WikiMacroBase):
    """Output a number from a scalar (1x1) SQL query.
     
    Examples:
    {{{
        {{{
        #!SQLScalar
            SELECT count(id) as 'Number of Tickets'
            FROM ticket
        }}}
    }}}
    """

    # IWikiMacroBase methods
    def expand_macro(self, formatter, name, content):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(content)

        value = "Unknown"
        for row in cursor:
            value = unicode(row[0])
            break

        out = StringIO()
        print >> out, u"<span class='wikiscalar'>%s</span>" % value

        add_stylesheet(formatter.req, 'wikitable/css/wikitable.css')
        return Markup(out.getvalue())
