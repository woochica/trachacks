# vim: expandtab tabstop=4
from StringIO import StringIO
import re
import string
from trac.util import escape

rules = re.compile(r"""(?P<heading>^\s*(?P<hdepth>=+)\s(?P<header>.*)\s(?P=hdepth)\s*$)""")
anchor = re.compile('[^\w\d]+')

def parse_toc(env, out, page, body):
    depth = 1
    for line in body.splitlines():
        line = escape(line)
        match = rules.match(line)
        if match:
            header = match.group('header')
            new_depth = len(match.group('hdepth'))
            if new_depth < depth:
                while new_depth < depth:
                    depth -= 1
                    out.write("</li></ol><li>\n")
            elif new_depth > depth:
                while new_depth > depth:
                    depth += 1
                    out.write("<ol><li>\n")
            else:
                out.write("</li><li>\n")
            link = page + "#" + anchor.sub("", header)
            out.write('<a href="%s">%s</a>' % (env.href.wiki(link), header))
    while depth > 1:
        out.write("</li></ol>\n")
        depth -= 1

def execute(hdf, args, env):
    db = env.get_db_cnx()
    out = StringIO()
    out.write("<div class='wiki-toc'>\n<ol>\n")
    out.write("<h4>Table of Contents</h4>\n")
    # Has the user supplied a list of pages?
    if args:
        pages = re.split('\s*,\s*', args)
        for page in pages:
            cursor = db.cursor()
            cursor.execute("SELECT text FROM wiki WHERE name='%s' ORDER BY version desc LIMIT 1" % page)
            row = cursor.fetchone()
            if row:
                parse_toc(env, out, page, row[0])
            else:
                out.write('<div class="system-message"><strong>Error: Page %s does not exist</strong></div>' % page)
    else:
        # return current page
        page = hdf.getValue("args.page", "WikiStart")
        parse_toc(env, out, page, hdf.getValue("wiki.page_source", ""))
    out.write("</ol>\n</div>\n")
    return out.getvalue()
