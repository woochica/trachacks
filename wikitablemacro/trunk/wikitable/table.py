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
from trac.wiki.formatter import system_message, format_to_html
from trac.wiki.macros import WikiMacroBase
from trac.util.html import Markup
from trac.util.text import exception_to_unicode
from trac.util.translation import _

class SQLTable(WikiMacroBase):
    """Draw a table from a SQL query in a wiki page.

    Examples:
    {{{
        {{{
        #!SQLTable
            SELECT count(id) as 'Number of Tickets'
            FROM ticket
        }}}
    }}}
    """

    implements(ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('wikitable', resource_filename(__name__, 'htdocs'))]

    # IWikiMacroBase methods
    def expand_macro(self, formatter, name, content):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute(content)
        except Exception, e:
            return system_message(_("Invalid SQL"), exception_to_unicode(e))

        out = StringIO()
        print >> out, "<table class='listing wikitable'>"
        print >> out, " <thead>"
        print >> out, "  <tr>"
        for desc in cursor.description:
            print >> out, "<th>%s</th>" % desc[0]
        print >> out, "  </tr>"
        print >> out, " </thead>"
        print >> out, " <tbody>"

        for idx, row in enumerate(cursor):
            css_class = (idx % 2 == 0) and 'odd' or 'even'
            print >> out, "  <tr class='%s'>" % css_class
            for col in row:
                print >> out, "<td>%s</td>" % \
                    format_to_html(self.env, formatter.context, col)
            print >> out, "  </tr>"

        print >> out, " </tbody>"
        print >> out, "</table>"

        add_stylesheet(formatter.req, 'wikitable/css/wikitable.css')
        return Markup(out.getvalue())
