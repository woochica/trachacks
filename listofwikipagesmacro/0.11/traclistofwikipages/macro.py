from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_oneliner
from genshi.builder import tag
from trac.util import format_datetime, pretty_timedelta
from urllib import quote_plus
from trac.web.api import IRequestFilter
from trac.web.chrome import add_stylesheet, ITemplateProvider


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

    def formattime(self,time):
        """Return formatted time for ListOfWikiPages table."""
        time = int(time)
        return [ tag.span( format_datetime  ( time ) ),
                 tag.span(
                    " (", 
                    tag.a( pretty_timedelta ( time ),
                           href = self.base_path
                                  + '/timeline?precision=seconds&from='
                                  + quote_plus( format_datetime ( time, 'iso8601' ) )
                         ),
                    " ago)"
                 )
               ]

    def formatrow(self, n, name, time, author=''):
        name = tag.a( name, href = self.wiki_path + str(name) )
        cols = [ tag.td( name ), tag.td( self.formattime( time )) ]
        if author:
            cols.append ( tag.td( author )  )
        return tag.tr(
                  cols,
                  class_ = ('even','odd')[ n % 2 ]
               )


class ListOfWikiPagesMacro(MacroBase):
    """ Provides Macro ListOfWikiPages. """

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args( content )

        self.formatter = formatter
        self.base_path = formatter.req.base_path
        self.wiki_path = formatter.req.href.wiki('/')
        getlist = self.env.config.getlist
        get     = self.env.config.get
        section = 'listofwikipages'


        ignoreusers = getlist(section, 'ignore_users', ['trac'])

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
        rows = [ self.formatrow(n,name,time,author) for n,[name,time,author] in
                    enumerate(cursor) ]

        head = tag.thead ( tag.tr(
                tag.th("WikiPage"),
                tag.th("Last Changed at"),
                tag.th("By")
            ) )
        table = tag.table( head, rows, class_ = 'listofwikipages' )
        return table


class LastChangesByMacro(MacroBase):
    """ Provides Macro LastChangesBy. """

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args( content )

        self.formatter = formatter
        self.base_path = formatter.req.base_path
        self.wiki_path = formatter.req.href.wiki('/')

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

        sqlcommand = " SELECT name,MAX(time) " \
                     " FROM wiki WHERE author == '%s' " \
                     " GROUP BY name " \
                     " ORDER BY time DESC " % (author)
        cursor.execute ( sqlcommand )

        rows = [ self.formatrow(n,name,time) for n,[name,time]
                    in enumerate(cursor) if n < count ]
        if count == 1:
            count = ''
            s = ''
        else:
            s = 's'

        headline = "Last %s Change%s By: " % (count,s)
        head = tag.thead (
                tag.tr(
                    tag.th(headline, tag.strong(author),
                    colspan = 2 )
                ),
                tag.tr(
                tag.th("WikiPage"),
                tag.th("Last Changed at")
            ) )
        table = tag.table( head, rows, class_ = 'lastchangesby' )
        return table

