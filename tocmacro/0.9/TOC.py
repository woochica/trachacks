# vim: expandtab tabstop=4
from StringIO import StringIO
import re
import string
import os
from trac.util import escape
from trac.wiki.formatter import Formatter, wiki_to_oneliner

rules_re = re.compile(r"""(?P<heading>^\s*(?P<hdepth>=+)\s(?P<header>.*)\s(?P=hdepth)\s*$)""")

def parse_toc(env, out, page, body, max_depth=999, min_depth=1, title_index=False):
    current_depth = min_depth
    in_pre = False
    first_li = True
    seen_anchors = []

    if title_index:
        min_depth = 1
        max_depth = 1

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
            formatted_header = wiki_to_oneliner(header, env)
            new_depth = len(match.group('hdepth'))
            if new_depth < min_depth:
                continue
            elif new_depth < current_depth:
                while new_depth < current_depth:
                    current_depth -= 1
                    if current_depth < max_depth:
                        out.write("</ol>")
                out.write("<li>")
            elif new_depth >= current_depth:
                i = current_depth
                while new_depth > i :
                    i += 1
                    if i <= max_depth:
                        out.write("<ol>")
                if i <= max_depth:
                    out.write("<li>")
                if first_li:
                    first_li = False
                current_depth = new_depth
            if title_index:
                out.write('<a href="%s">%s</a> : %s</li>\n' % (env.href.wiki(page), page, formatted_header))
                break
            else:
                default_anchor = anchor = Formatter._anchor_re.sub("", header.decode('utf-8'))
                anchor_n = 1
                while anchor in seen_anchors:
                    anchor = default_anchor + str(anchor_n)
                    anchor_n += 1
                seen_anchors.append(anchor)
                link = page
                if current_depth <= max_depth:
                    out.write('<a href="%s#%s">%s</a></li>\n' % (env.href.wiki(link), anchor, formatted_header))
    while current_depth > min_depth:
        if current_depth <= max_depth:
            out.write("</ol>\n")
        current_depth -= 1

def execute(hdf, args, env):
    db = env.get_db_cnx()
    if not args:
        args = ''
    pre_pages = re.split('\s*,\s*', args)
    # Options
    inline = False
    heading_def = 'Table of Contents'
    heading = ''
    pages = []
    root = ''
    params = { }
    title_index = False
    # Global options
    for page in pre_pages:
        if page == 'inline':
            inline = True
        elif page == 'noheading':
            heading = None
        elif page == 'notitle':
            params['min_depth'] = 2     # Skip page title
        elif page == 'titleindex':
            params['title_index'] = True
            heading_def = None
            title_index = True
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
        pages.append(hdf.getValue('wiki.page_name', 'WikiStart'))
        root = ''
        params['min_depth'] = 2     # Skip page title

    out = StringIO()
    if not inline:
        out.write("<div class='wiki-toc'>\n")
    if heading == '':
        heading = heading_def
    if heading:
        out.write("<h4>%s</h4>\n" % heading)
    out.write("<ol>\n")
    for page in pages:
        if title_index:
            cursor = db.cursor()
            prefix = os.path.split(page)[0]
            prefix = prefix.replace('\'', '\'\'')
            sql = 'SELECT DISTINCT name FROM wiki '
            if prefix:
                sql += 'WHERE name LIKE \'%s/%%\' ' % prefix
            sql += 'ORDER BY name'
            cursor.execute(sql)
            i = 0
            while 1:
                page_row = cursor.fetchone()
                if page_row == None:
                    if i == 0:
                        out.write('<div class="system-message"><strong>Error: No page matching %s found</strong></div>' % prefix)
                    break
                i += 1
                cursor2 = db.cursor()
                cursor2.execute("SELECT text FROM wiki WHERE name='%s' ORDER BY version desc LIMIT 1" % page_row[0])
                text_row = cursor2.fetchone()
                parse_toc(env, out, page_row[0], text_row[0], **params)

        else:
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
    out.write("</ol>\n")
    if not inline:
        out.write("</div>\n")
    return out.getvalue()
