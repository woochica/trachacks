from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome 
from trac.web.chrome import INavigationContributor 
from trac.util import escape, Markup, format_date, format_datetime
#from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
from trac.wiki.model import WikiPage
from tractags.api import TagEngine

import os
import os.path
from pkg_resources import resource_filename

__all__ = ['StatusPage']

class StatusPage(Component):
    """
        Provides functions related to registration
    """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'blog'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'blog', Markup('<a href="%s">blog</a>',
                                         req.href.blog())

    def match_request(self, req):
        self.log.info(str(req.args))
        return req.path_info == '/blog'

    def process_request(self, req):
#        add_stylesheet(req, 'pyrus/css/pyrus.css')
        add_stylesheet(req, 'common/css/wiki.css')
        tags = TagEngine(self.env).tagspace.wiki

        # Formatting
        read_post = "[wiki:%s Read Post]"
        entries = []
        for blog_entry in tags.get_tagged_names('blog'):
            page = WikiPage(self.env, name=blog_entry)
            version, time, author, comment, ipnr = page.get_history().next()
            timeStr = format_datetime(time) 
            data = {
                    'wiki_link' : wiki_to_oneliner(read_post % blog_entry,
                                                   self.env),
                    'time'      : timeStr,
                    'author'    : author,
                    'wiki_text' : wiki_to_html(page.text, self.env, req),
                    'comment'   : wiki_to_oneliner(comment, self.env),
                   }
            entries.append(data)
        req.hdf['blog.entries'] = entries

        return 'blog.cs', None

    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('pyrus', resource_filename(__name__, 'htdocs'))]


