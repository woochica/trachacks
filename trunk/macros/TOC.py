# vim: expandtab tabstop=4
from StringIO import StringIO
import re
import string
from trac.util import escape

rules_re = re.compile(r"""(?P<heading>^\s*(?P<hdepth>=+)\s(?P<header>.*)\s(?P=hdepth)\s*$)""")
anchor_re = re.compile('[^\w\d]+')

def parse_toc(env, out, page, body, max_depth = 999):
    current_depth = 1
    in_pre = False
    seen_anchors = []

    for line in body.splitlines():
        line = escape(line)

        # Skip over wiki-escaped code, e.g. code examples (Steven N.
        # Severinghaus <sns@severinghaus.org>)
        if in_pre:
            if line == '}}}':
                in_pre = False
            else:
                continue
        if line == '{{{':
            in_pre = True
            continue

        match = rules_re.match(line)
        if match:
            header = match.group('header')
            new_depth = len(match.group('hdepth'))
            if new_depth < current_depth:
                while new_depth < current_depth:
                    current_depth -= 1
                    if current_depth == max_depth:
                        out.write("</li><li>\n")
                    elif current_depth < max_depth:
                        out.write("</li></ol><li>\n")
            elif new_depth > current_depth:
                while new_depth > current_depth:
                    current_depth += 1
                    if current_depth <= max_depth:
                        out.write("<ol><li>\n")
            else:
                if current_depth <= max_depth:
                    out.write("</li><li>\n")
            default_anchor = anchor = anchor_re.sub("", header)
            anchor_n = 1
            while anchor in seen_anchors:
                anchor = default_anchor + str(anchor_n)
                anchor_n += 1
            seen_anchors.append(anchor)
            link = page + "#" + anchor
            if current_depth <= max_depth:
                out.write('<a href="%s">%s</a>' % (env.href.wiki(link), header))
    while current_depth > 1:
        if current_depth <= max_depth:
            out.write("</li></ol>\n")
        current_depth -= 1

def execute(hdf, args, env):
    db = env.get_db_cnx()
    out = StringIO()
    out.write("<div class='wiki-toc'>\n<ol>\n")
    out.write("<h4>Table of Contents</h4>\n")
    # Has the user supplied a list of pages?
    if not args:
        args = hdf.getValue("args.page", "WikiStart")
    pages = re.split('\s*,\s*', args)
    args = {}
    for page in pages:
        # Override arguments
        if page[:6] == 'depth=':
            args['max_depth'] = int(page[6:])
            continue

        cursor = db.cursor()
        cursor.execute("SELECT text FROM wiki WHERE name='%s' ORDER BY version desc LIMIT 1" % page)
        row = cursor.fetchone()
        if row:
            parse_toc(env, out, page, row[0], **args)
        else:
            out.write('<div class="system-message"><strong>Error: Page %s does not exist</strong></div>' % page)
    out.write("</ol>\n</div>\n")
    return out.getvalue()
