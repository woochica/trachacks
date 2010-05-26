"""
 Copyright (c) 2010 by Martin Scharrer <martin@scharrer-online.de>
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = ur"$Rev$"[6:-2]
__date__     = ur"$Date$"[7:-2]


from  trac.core       import  *
from  genshi.builder  import  tag
from  trac.web.api    import  IRequestHandler, RequestDone
from  trac.util.text  import  to_unicode
from  trac.config     import  Option, ListOption, BoolOption, IntOption
from  trac.util       import  format_datetime

class GoogleSitemapPlugin(Component):
    implements ( IRequestHandler )

    rev = __revision__
    date = __date__

    sitemappath = Option('googlesitemap', 'sitemappath', '/sitemap.xml', 'Path of sitemap (default: "/sitemap.xml")')
    ignoreusers = ListOption('googlesitemap', 'ignore_users', 'trac', doc='Do not list wiki pages from this users (default: "trac")')
    ignorewikis = ListOption('googlesitemap', 'ignore_wikis', '', doc='List of wiki pages to not be included in sitemap')
    listrealms  = ListOption('googlesitemap', 'list_realms', 'wiki,ticket', doc='Which realms should be listed. Supported are "wiki" and "ticket".')
    compress_sitemap = BoolOption('googlesitemap', 'compress_sitemap', False, doc='Send sitemap compressed. Useful for larger sitemaps.')
    compression_level = IntOption('googlesitemap', 'compression_level', 6, doc='Compression level. Value range: 1 (low) to 9 (high). Default: 6')

    _urlset_attrs = {
              'xmlns':"http://www.sitemaps.org/schemas/sitemap/0.9",
              'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance",
              'xsi:schemaLocation':"http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd" 
            }

    def _get_sql_exclude(self, list):
      import re
      if not list:
        return ''
      star  = re.compile(r'(?<!\\)\*')
      ques  = re.compile(r'(?<!\\)\?')
      sql_excludelist = []
      sql_excludepattern = ''
      for pattern in list:
        pattern = pattern.replace('%',r'\%').replace('_',r'\_')
        npattern = star.sub('%', pattern)
        npattern = ques.sub('_', npattern)
        if pattern == npattern:
          sql_excludelist.append(pattern)
        else:
          sql_excludepattern = sql_excludepattern + " AND name NOT LIKE '%s' " % npattern
      sql_excludename = " AND name NOT in ('%s') " % "','".join(sql_excludelist)
      return sql_excludename + sql_excludepattern


   # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == self.sitemappath

    def _fixtime(self, timestring):
        if not timestring.endswith('Z') and timestring[-3] != ':':
            return timestring[:-2] + ':' + timestring[-2:]

    def process_request(self, req):
        try:
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            if 'wiki' in self.listrealms:
              sql_exclude = self._get_sql_exclude(self.ignorewikis)

              sql = "SELECT name,time,version FROM wiki AS w1 WHERE " \
                    "author NOT IN ('%s') "  % "','".join( self.ignoreusers ) + sql_exclude + \
                    "AND version=(SELECT MAX(version) FROM wiki AS w2 WHERE w1.name=w2.name) ORDER BY name "
              self.log.debug(sql)
              cursor.execute(sql)
              urls = [ tag.url(
                              tag.loc( req.base_url + req.href.wiki(name) ),
                              tag.lastmod( self._fixtime(format_datetime (time,'iso8601')) )
                        ) for n,[name,time,version] in enumerate(cursor) ]
            else:
              urls = []

            if 'ticket' in self.listrealms:
              cursor.execute(
                  "SELECT id,changetime FROM ticket"
              )
              urls.append( [ tag.url(
                              tag.loc( req.base_url + req.href.ticket(ticketid) ),
                              tag.lastmod( self._fixtime(format_datetime (changetime,'iso8601')) )
                        ) for n,[ticketid,changetime] in enumerate(cursor) ] )

            xml = tag.urlset(urls, **self._urlset_attrs)
            content = xml.generate().render('xml','utf-8')

            if self.compress_sitemap:
              from zlib import compress
              zcontent = compress(content, self.compression_level)

              self.send_response(200)
              self.send_header('Cache-control', 'must-revalidate')
              self.send_header('Content-Type', 'text/xml;charset=utf-8')
              self.send_header('Content-Encoding', 'gzip')
              self.send_header('Content-Length', len(zcontent))
              self.end_headers()

              if self.method != 'HEAD':
                  self.write(zcontent)
              raise RequestDone
            else:
              req.send( content, content_type='text/xml', status=200)

        except RequestDone:
            pass
        except Exception, e:
            self.log.error(e)
            req.send_response(500)
            req.end_headers()
        raise RequestDone



