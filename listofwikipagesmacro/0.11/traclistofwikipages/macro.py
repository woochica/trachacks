from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_oneliner
from genshi.builder import tag
from trac.util import format_datetime, pretty_timedelta
from urllib import quote_plus
from trac.web.api import IRequestFilter
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.util.text import to_unicode
from time import time as unixtime

class ListOfWikiPagesStyleSheetProvider(Component):
    implements(IRequestFilter,ITemplateProvider)

   # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet( req, 'listofwikipages/style.css')
        return (template, data, content_type)


   # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('listofwikipages', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


class ListOfWikiPagesMacro(WikiMacroBase):
    """ Provides Macro ListOfWikiPages. """

    long_format = False

    tunits = {
        's': 1,
        'm': 60,
        'h': 60*60,
        'd': 60*60*24,
        'w': 60*60*24*7,
        'o': 60*60*24*30,
        'y': 60*60*24*365
    }
    tunits_name = {
        's': ' second',
        'm': ' minute',
        'h': ' hour',
        'd': ' day',
        'w': ' week',
        'o': ' month',
        'y': ' year'
    }

    def timeval(self, name, default):
      if name in self.kwargs:
        try:
          val = self.kwargs[name]
          try:
            val = int(val)
            text = \
                str(val) + self.tunits_name['s'] + ['s',''][val == 1]
          except:
            unit = val[-1].lower()
            val = float(val[:-1])
            text = \
                str(val).strip('.0') + self.tunits_name[unit] \
                + ['s',''][val == 1]
            val =  int( val * self.tunits[ unit ] )
          val = int(unixtime()) - val
        except:
          raise TracError("Invalid value '%s' for argument '%s'! "
              % (self.kwargs[name],name) )
        return (val,text)
      else:
        return default


    def formattime(self,time):
        """Return formatted time for ListOfWikiPages table."""
        time = int(time)
        return [ tag.span( format_datetime  ( time ) ),
                 tag.span(
                    " (", 
                    tag.a( pretty_timedelta ( time ),
                           href = self.href('timeline',
                                  precision='seconds', from_=
                                  quote_plus( format_datetime (time,'iso8601') )
                           ) ),
                    " ago)"
                 )
               ]

    def formatrow(self, n, name, time, version='', comment='', author=''):
        name = to_unicode(name)
        namelink = tag.a( name, href = self.href.wiki( name ) )
        cols = [ tag.td( namelink ), tag.td( self.formattime( time )) ]
        if author:
            cols.append ( tag.td( author )  )
        if self.long_format:
            cols.extend ([
              tag.td( tag.a(version,
                href=self.href.wiki( name, version=version)), class_='version'),
              tag.td( tag.a("Diff",
                href=self.href.wiki( name, action='diff', version=version) ) ),
              tag.td( tag.a("History",
                href=self.href.wiki( name, action='history') ) ),
              tag.td( comment ),
            ])
        return tag.tr(
                  cols,
                  class_ = ('even','odd')[ n % 2 ]
               )


    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args( content )

        self.href = formatter.req.href
        section = 'listofwikipages'

        long_format = self.env.config.get(section, 'default_format', 
            'short').lower() == 'long'
        if 'format' in kwargs:
          long_format = kwargs['format'].lower() == 'long'
        self.long_format = long_format

        ignoreusers = self.env.config.getlist(section, 'ignore_users', ['trac'])

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if largs:
            sql_wikis = " AND name IN ('"    \
                        + "','".join(largs) \
                        + "') "
        else:
            sql_wikis = ''

        self.kwargs = kwargs
        dfrom, fromtext = self.timeval('from', (0,''))
        dto, totext     = self.timeval('to',   (int(unixtime()),''))

        if 'from' in kwargs or 'to' in kwargs:
          sql_time = " time BETWEEN %d AND %d AND " % (dfrom,dto)
        else:
          sql_time = ''

        sqlcommand = " SELECT name,MAX(time),author " \
                     " FROM wiki WHERE author NOT IN ('%s') " \
                        % "','".join( ignoreusers ) \
                     + sql_wikis + \
                     " GROUP BY name "
        cursor.execute ( sqlcommand )

        cursor.execute(
            "SELECT name,time,author,MAX(version),comment FROM wiki WHERE " \
            + sql_time + \
            "author NOT IN ('%s') "  % "','".join( ignoreusers ) + sql_wikis + \
            "GROUP BY name ORDER BY time DESC")
        rows = [ self.formatrow(n,name,time,version,comment,author)
              for n,[name,time,author,version,comment] in enumerate(cursor) ]

        if self.long_format:
          cols = ( "WikiPage", "Last Changed At", "By",
                   "Version", "Diff", "History", "Comment" )
        else:
          cols = ( "WikiPage", "Last Changed At", "By" )

        if 'headline' in kwargs:
          headlinetag = tag.tr( tag.th( kwargs['headline'],
            colspan = len(cols) ) )
        else:
          headlinetag = tag()

        head  = tag.thead ( headlinetag, tag.tr(
          map(lambda x: tag.th(x, class_=x.replace(" ", "").lower() ), cols) ) )
        table = tag.table ( head, rows, class_ = 'listofwikipages' )

        self.href = None
        return table


class LastChangesByMacro(ListOfWikiPagesMacro):
    """ Provides Macro LastChangesBy. """

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args( content )

        #self.base_path = formatter.req.base_path
        self.href = formatter.req.href
        section = 'listofwikipages'

        long_format = self.env.config.get(section, 'default_format', 
            'short').lower() == 'long'
        if 'format' in kwargs:
          long_format = kwargs['format'].lower() == 'long'
        self.long_format = long_format

        self.kwargs = kwargs
        dfrom, fromtext = self.timeval('from', (0,''))
        dto, totext     = self.timeval('to',   (int(unixtime()),''))

        if 'from' in kwargs or 'to' in kwargs:
          sql_time = " AND time BETWEEN %d AND %d " % (dfrom,dto)
        else:
          sql_time = ''

        author = len(largs) > 0 and largs[0] or formatter.req.authname
        count  = len(largs) > 1 and largs[1] or 5
        try:
            count = int(count)
            if count < 1:
                raise
        except:
            raise TracError("Second list argument must be a positive integer!")

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute ( """
              SELECT name,time,MAX(version),comment
              FROM wiki WHERE author = %s """ + sql_time + """
              GROUP BY name
              ORDER BY time DESC
          """, (author,) )

        rows = [ self.formatrow(n,name,time,version,comment) for
              n,[name,time,version,comment] in enumerate(cursor) if n < count ]
        if count == 1:
            count = ''
            s = ''
        else:
            s = 's'

        if self.long_format:
          cols = ( "WikiPage", "Last Changed At",
                   "Version", "Diff", "History", "Comment" )
        else:
          cols = ( "WikiPage", "Last Changed At" )

        headline = "Last %s change%s by  " % (count,s)
        if sql_time:
          if fromtext:
            if totext:
              timetag = " between %s and %s ago" % (fromtext,totext)
            else:
              timetag = " in the last %s" % fromtext
          else:
            if totext:
              timetag = " before the last %s" % totext
            else:
              timetag = ""
        else:
          timetag = ''

        if 'headline' in kwargs:
          headlinetag = tag.tr(
              tag.th(kwargs['headline'],
              colspan = len(cols) ))
        else:
          headlinetag = tag.tr(
              tag.th(headline, tag.strong(author), timetag,
              colspan = len(cols) ))

        head = tag.thead ( headlinetag,
                tag.tr(
          map(lambda x: tag.th(x, class_=x.replace(" ", "").lower() ), cols)
        ) )
        table = tag.table( head, rows, class_ = 'lastchangesby' )

        self.href = None
        return table

