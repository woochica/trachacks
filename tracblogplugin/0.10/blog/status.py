from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome 
from trac.web.chrome import INavigationContributor 
from trac.util import escape, Markup, format_date, format_datetime
#from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiMacroProvider
from tractags.api import TagEngine

import os
import os.path
from pkg_resources import resource_filename

__all__ = ['StatusPage']

class StatusPage(Component):
    """
        Provides functions related to registration
    """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor,
               IWikiMacroProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'blog'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'blog', Markup('<a href="%s">blog</a>',
                                         req.href.blog())

    # IWikiMacroProvider
    def get_macros(self):
        yield "TracBlog"

    def get_macro_description(self, name):
        desc =  "Embeds a Blog into a Wiki page\n\n" \
                "[[TracBlog()]] - embed the default blog\n"\
                "[[TracBlog(tag1,tag2)]] - embed a blog that corresponds to\n"\
                "                          the specified tags"
        return desc

    def render_macro(self, req, name, content):
        """ Display the blog in the wiki page """
        parms = [x.strip() for x in content.split(',')]
        kwargs = [x for x in parms if x.find('=') < 0]
        tags = [x for x in parms if x not in kwargs]
        if not tags:
            tags = ['blog']
        self._generate_blog(req, *tags)
        req.hdf['blog.macro'] = True
        return req.hdf.render('blog.cs')

    def match_request(self, req):
        self.log.info(str(req.args))
        return req.path_info == '/blog'


    def _generate_blog(self, req, *args, **kwargs):
        """
            Generate the blog and fill the hdf.

            *args is a list of tags to use to limit the blog scope
            **kwargs are any aditional keyword arguments that are needed
        """
        tags = TagEngine(self.env).tagspace.wiki

        # Formatting
        read_post = "[wiki:%s Read Post]"
        entries = {}
        for blog_entry in tags.get_tagged_names(*args):
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
            entries[time] = data
            continue
        tlist = entries.keys()
        tlist.sort(reverse=True)
        req.hdf['blog.entries'] = [entries[x] for x in tlist]
        pass


    def process_request(self, req):
#        add_stylesheet(req, 'pyrus/css/pyrus.css')
        add_stylesheet(req, 'common/css/wiki.css')
        self._generate_blog(req, 'blog')
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


