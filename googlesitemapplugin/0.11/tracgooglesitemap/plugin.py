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
    """ Generates a Google compatible sitemap with all wiki pages and/or tickets.

     The sitemap can be compressed with the `compress_sitemap` option. In this case the XML file can be sent compressed in two different ways:
       * If the XML file (.xml) is requested it will be send with a gzip `content-encoding` if the requesting HTTP client supports it,
         i.e. sent a `accept-encoding` header with either includes '`gzip`' or indentical to '`*`'.
       * If a gzipped XML file is requested (.xml.gz) directly the compressed sitemap will be sent as gzip file (mime-type `application/x-gzip`).
         This is also done if the `sitemappath` ends in '`.gz`'.
    """
    implements ( IRequestHandler )

    rev = __revision__
    date = __date__

    sitemappath = Option('googlesitemap', 'sitemappath', 'sitemap.xml', 'Path of sitemap relative to Trac main URL (default: "sitemap.xml"). '
                                                                        'If this path ends in `.gz` the sidemap will automatically be compressed.')
    ignoreusers = ListOption('googlesitemap', 'ignore_users', 'trac', doc='Do not list wiki pages from this users (default: "trac")')
    ignorewikis = ListOption('googlesitemap', 'ignore_wikis', '', doc='List of wiki pages to not be included in sitemap')
    listrealms  = ListOption('googlesitemap', 'list_realms', 'wiki,ticket', doc='Which realms should be listed. Supported are "wiki" and "ticket".')
    compress_sitemap = BoolOption('googlesitemap', 'compress_sitemap', False, doc='Send sitemap compressed. Useful for larger sitemaps.')
    compression_level = IntOption('googlesitemap', 'compression_level', 6, doc='Compression level. Value range: 1 (low) to 9 (high). Default: 6')
    changefreq = Option('googlesitemap', 'change_frequency', '', 'Change frequency of URLs. Valid values: always, hourly, daily, weekly, monthly, yearly, never. Disabled if empty.')

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
        path = '/' + self.sitemappath
        return req.path_info == path or (self.compress_sitemap and req.path_info == path + '.gz')

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
              #self.log.debug(sql)
              cursor.execute(sql)
              urls = [ tag.url(
                              tag.loc( self.env.abs_href.wiki(name) ),
                              tag.lastmod( self._fixtime(format_datetime (time,'iso8601')) ),
                              self.changefreq and tag.changefreq( self.changefreq ) or ''
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

            accept_enc  = req.get_header('accept-encoding')
            accept_gzip = accept_enc and ( accept_enc.find('gzip') != -1 or accept_enc == '*' )
            compressed  = self.sitemappath.endswith('.gz') or req.path_info == '/' + self.sitemappath + '.gz'
            if compressed or (self.compress_sitemap and accept_gzip):
              import StringIO
              from gzip import GzipFile
              gzbuf = StringIO.StringIO()
              gzfile = GzipFile(mode='wb', fileobj=gzbuf, compresslevel=self.compression_level)
              gzfile.write(content)
              gzfile.close()
              zcontent = gzbuf.getvalue()
              gzbuf.close()

              req.send_response(200)
              req.send_header('Cache-control', 'must-revalidate')
              if compressed:
                req.send_header('Content-Type', 'application/x-gzip')
              else:
                req.send_header('Content-Type', 'text/xml;charset=utf-8')
                req.send_header('Content-Encoding', 'gzip')
              req.send_header('Content-Length', len(zcontent))
              req.end_headers()

              if req.method != 'HEAD':
                  req.write(zcontent)
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



