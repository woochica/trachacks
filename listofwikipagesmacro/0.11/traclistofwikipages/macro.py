from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_oneliner
from genshi.builder import tag
from trac.util import format_datetime, pretty_timedelta
from urllib import quote_plus
from trac.web.api import IRequestFilter
from trac.web.chrome import add_stylesheet, ITemplateProvider

class ListOfWikiPagesMacro(WikiMacroBase):
    """ Provides Macro to list wiki pages with last changed date and author.
    """
    implements(IWikiMacroProvider,IRequestFilter,ITemplateProvider)

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


   # Macro methods
    def _formattime(self,time):
        """Return formatted time for ListOfWikiPages table."""
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

    def _formatrow(self,name,time,author):
        time = int(time)
        name = tag.a( name, href = self.base_path + '/wiki/' + name )
        if self.n:
            self.n = 0
        else:
            self.n = 1
        return tag.tr(
                  tag.td(name),
                  tag.td(self._formattime(time)),
                  tag.td(author),
                  class_ = ('even','odd')[ self.n ]
               )

    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        """ Provides Macro ListOfWikiPages.
        """
        largs, kwargs = parse_args( content )

        self.formatter = formatter
        self.base_path = formatter.req.base_path
        getlist = self.env.config.getlist
        get     = self.env.config.get
        section = 'listofwikipages'
        self.n  = 0

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
        rows = [ self._formatrow(name,time,author) for name,time,author in cursor ]

        head = tag.thead ( tag.tr(
                tag.th("WikiPage"),
                tag.th("Last Changed at"),
                tag.th("By")
            ) )
        table = tag.table( head, rows, class_ = 'listofwikipages' )
        return table



