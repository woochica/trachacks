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
    # Has the user supplied a list of pages?
    if not args:
        args = ''
    pre_pages = re.split('\s*,\s*', args)
    # Options
    inline = False
    heading = 'Table of Contents'
    pages = []
    root = ''
    params = { }
    # Global options
    for page in pre_pages:
        if page == 'inline':
            inline = True
        elif page == 'noheading':
            heading = None
        elif page[:8] == 'heading=':
            heading = page[8:]
        elif page == '':
            continue
        elif page[:6] == 'depth=':
            params['max_depth'] = int(page[6:])
        elif page[:5] == 'root=':
            root = page[5:]
        else:
            pages.append(page)
    # Has the user supplied a list of pages?
    if not pages:
        pages.append(hdf.getValue("args.page", "WikiStart"))
        root = ''
        #params['min_depth'] = 2     # Skip page title
    out = StringIO()
    if not inline:
        out.write("<div class='wiki-toc'>\n")
    if heading:
        out.write("<h4>%s</h4>\n" % heading)
    for page in pages:
        # Override arguments
        if page[:6] == 'depth=':
            params['max_depth'] = int(page[6:])
        elif page[:5] == 'root=':
            root = page[5:]
        else:
            page = root + page
            cursor = db.cursor()
            cursor.execute("SELECT text FROM wiki WHERE name='%s' ORDER BY version desc LIMIT 1" % page)
            row = cursor.fetchone()
            if row:
                parse_toc(env, out, page, row[0], **params)
            else:
                out.write('<div class="system-message"><strong>Error: Page %s does not exist</strong></div>' % page)
    if not inline:
        out.write("</div>\n")
    return out.getvalue()
