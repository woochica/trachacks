from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome 
from trac.web.chrome import INavigationContributor 
from trac.util import escape, Markup, format_date, format_datetime
#from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiMacroProvider
from tractags.api import TagEngine
from webadmin.web_ui import IAdminPageProvider

import os
import os.path
import time
from pkg_resources import resource_filename

__all__ = ['TracBlogPlugin']

class TracBlogPlugin(Component):
    """
        Provides functions related to registration
    """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor,
               IWikiMacroProvider, IPermissionRequestor)

    # IPermissionRequestor
    def get_permission_actions(self):
        return ['BLOG_ADMIN']

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'blog'
                
    def get_navigation_items(self, req):
        req.hdf['trac.href.blog'] = req.href.blog()
        yield 'mainnav', 'blog', Markup('<a href="%s">Blog</a>',
                                         req.href.blog())

    # IWikiMacroProvider
    def get_macros(self):
        return ["BlogShow", "BlogPost"]

    def get_macro_description(self, name):
        desc =  "Embeds a Blog into a Wiki page\n\n" \
                "[[TracBlog()]] - embed the default blog\n"\
                "[[TracBlog(tag1,tag2)]] - embed a blog that corresponds to\n"\
                "                          the specified tags"
        return desc

    def render_macro(self, req, name, content):
        """ Display the blog in the wiki page """
        add_stylesheet(req, 'blog/css/blog.css')
        m = getattr(self, ''.join(['_render_', name]))
        return m(req, name, content)

    def _split_macro_args(self, argv):
        """Return a list of arguments and a dictionary of keyword arguements

        """
        argv = argv or ''
        parms = [x.strip() for x in argv.split(',') if x]
        self.log.debug("parms: %s" % str(parms))
        kargs = [x for x in parms if x.find('=') >= 0]
        self.log.debug("kargs: %s" % str(kargs))
        args = [x for x in parms if x not in kargs]
        self.log.debug("args: %s" % str(args))
        kwargs = {}
        for x in kargs:
            key, value = x.split('=')
            key = key.strip()
            value = value.strip()
            if isinstance(key, unicode):
                key = key.encode('ascii')
                value = value.encode('ascii')
            if kwargs.has_key(key):
                if isinstance(key, list):
                    kwargs[key].append(value)
                else:
                    kwargs[key] = [kwargs[key], value]
            else:
                kwargs[key] = value
        self.log.debug("kwargs: %s" % str(kwargs))
        return args, kwargs

    def _render_BlogPost(self, req, name, content):
        args, kwargs = self._split_macro_args(content)
        self.log.debug("link: %s" % req.href.blog('new', **kwargs))
        return Markup('<a href="%s">New Blog Post</a>', 
                      req.href.blog('new',**kwargs))

    def _render_BlogShow(self, req, name, content):
        tags, kwargs = self._split_macro_args(content)
        if not tags:
            tags = ['blog']
        self._generate_blog(req, *tags, **kwargs)
        req.hdf['blog.macro'] = True
        return req.hdf.render('blog.cs')

    def match_request(self, req):
        self.log.info(str(req.args))
        return req.path_info == '/blog' or req.path_info == '/blog/new'

    def process_request(self, req):
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
        if req.path_info == '/blog':
            self._generate_blog(req, 'blog')
            return 'blog.cs', None
        else:
            self._new_blog_post(req)
            return 'new_blog.cs', None

    def _new_blog_post(self, req):
        """ Generate a new blog post

        """
        action = req.args.get('action', 'edit')
        pg_name_fmt = self.env.config.get('blog', 'page_format', 
                                          '%Y/%m/%d/%H.%M')
        self.log.debug("page format: %s" % pg_name_fmt)
        pagename = req.args.get('pagename', time.strftime(pg_name_fmt))
        self.log.debug("page name: %s" % pagename)
        if req.method == 'POST':
            if action == 'edit':
                if req.args.has_key('cancel'):
                    req.redirect(self.env.href.blog())
                page = WikiPage(self.env, pagename, None)
                tags = TagEngine(self.env).tagspace.wiki
                if req.args.has_key('preview'):
                    req.hdf['blog.action'] = 'preview'
                    self._render_editor(req, page, self.env.get_db_cnx(),
                                        preview=True) 
                else:
                    title = req.args.get('blogtitle')
                    titleline = ' '.join(["=", title, "=\n"])
                    if title:
                        page.text = ''.join([titleline, req.args.get('text')])
                    else:
                        page.text = req.args.get('text')
                    page.readonly = int(req.args.has_key('readonly'))
                    page.save(req.authname, req.args.get('comment'), 
                              req.remote_addr)
                    taglist = [x.strip() for x in req.args.get('tags').split(',') if x]
                    for t in taglist:
                        tags.add(req, pagename, t)
                    req.redirect(self.env.href.blog())
        else:
            req.hdf['blog.pagename'] = pagename
            req.hdf['blog.edit_rows'] = 20
            tlist = req.args.getlist('tag')
            req.hdf['tags'] = ', '.join(tlist)
            pass

    def _render_editor(self, req, page, db, preview=False):
        title = req.args.get('blogtitle')
        titleline = ' '.join(["=", title, "=\n"])
        if req.args.has_key('text'):
            page.text = req.args.get('text')
        if preview:
            page.readonly = req.args.has_key('readonly')

        author = req.authname
        comment = req.args.get('comment', '')
        editrows = req.args.get('editrows')
        tags = req.args.get('tags')
        req.hdf['tags'] = tags
        if editrows:
            pref = req.session.get('wiki_editrows', '20')
            if editrows != pref:
                req.session['wiki_editrows'] = editrows
        else:
            editrows = req.session.get('wiki_editrows', '20')

        req.hdf['title'] = page.name + ' (edit)'
        info = {
            'pagename': page.name,
            'page_source': page.text,
            'author': author,
            'comment': comment,
            'readonly': page.readonly,
            'edit_rows': editrows,
            'scroll_bar_pos': req.args.get('scroll_bar_pos', '')
        }
        if preview:
            if title:
                info['page_htm'] = wiki_to_html(''.join([titleline, 
                                                req.args.get('text')]),
                                                self.env, req, db)
            else:
                info['page_html'] = wiki_to_html(page.text, self.env, req, db)
            info['readonly'] = int(req.args.has_key('readonly'))
        req.hdf['blog'] = info

    def _generate_blog(self, req, *args, **kwargs):
        """
            Generate the blog and fill the hdf.

            *args is a list of tags to use to limit the blog scope
            **kwargs are any aditional keyword arguments that are needed
        """
        tags = TagEngine(self.env).tagspace.wiki
        try:
            union = kwargs['union']
        except KeyError:
            union = False
        # Formatting
        read_post = "[wiki:%s Read Post]"
        entries = {}
        if (not union) and (len(args) > 1):
            tag_group = {}
            for tag in args:
                tag_group[tag] = tags.get_tagged_names(tag)
            tag_set = tag_group[args[0]]
            for tag in args[1:]:
                tag_set = tag_set.intersection(tag_group[tag])
            blog = tag_set
        elif not len(args):
            blog = tags.get_tagged_names('blog') 
        else:
            blog = tags.get_tagged_names(*args) 
        
        for blog_entry in blog:
            page = WikiPage(self.env, name=blog_entry)
            version, wtime, author, comment, ipnr = page.get_history().next()
            time_format = self.env.config.get('blog', 'date_format') or '%x %X'
            timeStr = format_datetime(wtime, format=time_format) 
            data = {
                    'wiki_link' : wiki_to_oneliner(read_post % blog_entry,
                                                   self.env),
                    'time'      : timeStr,
                    'author'    : author,
                    'wiki_text' : wiki_to_html(page.text, self.env, req),
                    'comment'   : wiki_to_oneliner(comment, self.env),
                   }
            entries[wtime] = data
            continue
        tlist = entries.keys()
        tlist.sort(reverse=True)
        req.hdf['blog.entries'] = [entries[x] for x in tlist]
        pass

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
        return [('blog', resource_filename(__name__, 'htdocs'))]


