"""

Trac Sitemap Plugin 0.1 - Implements the Sitemaps protocol, specified at:

    http://www.sitemaps.org/protocol.php

"""

### TODO:
### Convert to a sitemap index, with multiple sitemaps, one for each
###     type of data (wiki, attachment, etc). Remember: 50,000/10MB is
###     the limit for an individual sitemap, so we might want to solve
###     that in a more general manner at the same time.
###
### Add walking of the SVN repository.

import time
from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor


class TracSitemapPlugin(Component):
    implements(IRequestHandler)

    def match_request(self, req):
        return req.path_info == '/sitemap.xml'

    def process_request(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/xml')
        req.end_headers()

        url_list = [ ]

        # Connect to the database.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Walk the wiki pages.
        cursor.execute('SELECT DISTINCT name,MAX(time) FROM wiki GROUP BY name ORDER BY name')
        for row in cursor:
            url_list.append((req.href('wiki', row[0]), row[1],))
            # Special case for the WikiStart page.
            ### TODO: Should we include all three, or just a "canonical" page?
            if row[0] == 'WikiStart':
                url_list.append((req.href('wiki'), row[1],))
                url_list.append(('', row[1],))

        # Walk the tickets.
        cursor.execute('SELECT id,changetime FROM ticket ORDER BY id')
        for row in cursor:
            url_list.append((req.href('ticket', row[0]), row[1],))

        # Walk the reports.
        url_list.append((req.href('report'), None))
        cursor.execute('SELECT id FROM report ORDER BY id')
        for row in cursor:
            url_list.append((req.href('report', row[0]), None,))

        # Walk the milestones.
        url_list.append((req.href('roadmap'), None))
        cursor.execute('SELECT name FROM milestone ORDER BY name')
        for row in cursor:
            url_list.append((req.href('milestone', row[0]), None),)

        # Walk the attachments.
        cursor.execute('SELECT type,id,filename,time FROM attachment')
        for row in cursor:
            url_list.append((req.href('attachment', row[0], row[1], row[2]), row[3],))

        # Mention a few other pages.
        url_list.append((req.href('browser'), None,))
        url_list.append((req.href('timeline'), None,))
        url_list.append((req.href('about'), None,))

        # All done.
        url_list.sort()
        port = '' if req.server_port == 80 else ':%s' % (req.server_port,)
        base_url = '%s://%s%s' % (req.scheme, req.server_name, port,)
        req.write("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
""")
        for url,timestamp in url_list:
            req.write("<url>\n")
            req.write("    <loc>%s%s</loc>\n" % (base_url, url,))
            if timestamp is not None:
                tzhour, tzmin = divmod(time.timezone / 60, 60)
                req.write("    <lastmod>%s%+03d:%02d</lastmod>\n" % (time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(timestamp)), tzhour, tzmin,))
            req.write("</url>\n")

        req.write('</urlset>')
        db.commit()
