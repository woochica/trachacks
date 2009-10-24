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

class StyleSheetProvider(Component):
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


class MacroBase(WikiMacroBase):
    """ Provides Macro Base. """
    long_format = False

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


class ListOfWikiPagesMacro(MacroBase):
    """ Provides Macro ListOfWikiPages. """


    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args( content )

        self.formatter = formatter
        #self.base_path = formatter.req.base_path
        self.href      = formatter.req.href
        getlist = self.env.config.getlist
        get     = self.env.config.get
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

        sqlcommand = " SELECT name,MAX(time),author " \
                     " FROM wiki WHERE author NOT IN ('%s') " \
                        % "','".join( ignoreusers ) \
                     + sql_wikis + \
                     " GROUP BY name "
        cursor.execute ( sqlcommand )

        cursor.execute(
            "SELECT name,time,author,MAX(version),comment FROM wiki WHERE author " \
            "NOT IN ('%s') "  % "','".join( ignoreusers ) + sql_wikis + \
            "GROUP BY name ORDER BY time DESC")
        rows = [ self.formatrow(n,name,time,version,comment,author)
              for n,[name,time,author,version,comment] in enumerate(cursor) ]

        if self.long_format:
          cols = ( "WikiPage", "Last Changed At", "By",
                   "Version", "Diff", "History", "Comment" )
        else:
          cols = ( "WikiPage", "Last Changed At", "By" )

        head  = tag.thead ( tag.tr(
          map(lambda x: tag.th(x, class_=x.replace(" ", "").lower() ), cols) ) )
        table = tag.table ( head, rows, class_ = 'listofwikipages' )
        return table


class LastChangesByMacro(MacroBase):
    """ Provides Macro LastChangesBy. """

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args( content )

        self.formatter = formatter
        #self.base_path = formatter.req.base_path
        self.href      = formatter.req.href
        section = 'listofwikipages'

        long_format = self.env.config.get(section, 'default_format', 
            'short').lower() == 'long'
        if 'format' in kwargs:
          long_format = kwargs['format'].lower() == 'long'
        self.long_format = long_format

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
              FROM wiki WHERE author = %s
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

        headline = "Last %s Change%s By: " % (count,s)
        head = tag.thead (
                tag.tr(
                    tag.th(headline, tag.strong(author),
                    colspan = len(cols) )
                ),
                tag.tr(
          map(lambda x: tag.th(x, class_=x.replace(" ", "").lower() ), cols)
        ) )
        table = tag.table( head, rows, class_ = 'lastchangesby' )
        return table

