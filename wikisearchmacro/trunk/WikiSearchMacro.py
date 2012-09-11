# -*- coding: utf-8 -*-

from trac.core import *
from trac.util.html import html
from trac.wiki import WikiSystem
from trac.wiki.macros import WikiMacroBase

revision="$Rev$"
url="$URL$"

class WikiSearchMacro(WikiMacroBase):
    """Performs a search in wiki content, and displays links to the pages.

    The first parameter is the search string, and its mandatory.

    The second parameter is an optional name prefix, only page names starting with this string will be included.

    The third parameter is an optional limit to the length of the returned list

    The fourth parameter is an optional name of a page to not include in the list
    """

    def render_macro(self, req, name, content):
        search = prefix = limit = skips = None
        if not content:
            return html.H2('Need to specify a search')

        if content:
            argv = [arg.strip() for arg in content.split(',')]
            if len(argv) < 1:
                return html.H2('Need to specify a search')
            search = argv[0]
            if len(argv) > 1:
                prefix = argv[1]
                if len(argv) > 2:
                    limit = argv[2]
                    if len(argv) > 3:
                        skips = argv[3]

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        sql = 'SELECT name, max_version FROM (' \
              'SELECT name as name, text as text, ' \
              '  max(version) AS max_version, ' \
              '  max(time) AS max_time ' \
              'FROM wiki '
        args = []
        if prefix:
            sql += 'WHERE name LIKE %s'
            args.append(prefix + '%')
        if skips:
            if prefix:
                sql += ' AND ';
            sql += 'name != %s'
            args.append(skips)
        sql += ' GROUP BY name ORDER BY max_time ASC'
        if limit:
            sql += ' LIMIT %s'
            args.append(limit)
        sql += ') AS temptable WHERE text LIKE %s'
        args.append('%' + search + '%')
        cursor.execute(sql, args)

        wiki = WikiSystem(self.env)
        return html.DIV(
            html.UL([html.LI(
                html.A(wiki.format_page_name(name), href=req.href.wiki(name)))
                      for name, version in cursor]))
