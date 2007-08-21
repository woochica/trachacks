import re
from tractags.api import TagEngine
from StringIO import StringIO
from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, add_stylesheet
from trac.web.api import ITemplateStreamFilter
from trac.wiki.api import IWikiPageManipulator
from trac.util.html import Markup, escape
from trac.util.compat import set
from trac.wiki.web_ui import WikiModule
from tractags.expr import Expression
from genshi.builder import tag as T
from genshi.filters.transform import Transformer


_tag_split = re.compile('[,\s]+')


class TagsUserInterface(Component):
    implements(ITemplateStreamFilter, IWikiPageManipulator)

    # Internal methods
    def _page_tags(self, req):
        pagename = req.args.get('page', 'WikiStart')

        engine = TagEngine(self.env)
        wikitags = engine.tagspace.wiki
        current_tags = list(wikitags.get_tags([pagename]))
        current_tags.sort()
        return current_tags

    def _wiki_view(self, req, stream):
        engine = TagEngine(self.env)
        add_stylesheet(req, 'tags/css/tractags.css')
        li = []
        for tag in self._page_tags(req):
            href, title = engine.get_tag_link(tag)
            li.append(T.li(T.a(title=title, href=href)(tag), ' '))

        insert = T.ul(class_='tags')(T.lh('Tags'), li)

        return stream | Transformer('//div[@class="buttons"]').before(insert)

    def _update_tags(self, req, page):
        newtags = set([t.strip() for t in
                      _tag_split.split(req.args.get('tags')) if t.strip()])
        wikitags = TagEngine(self.env).tagspace.wiki
        oldtags = wikitags.get_tags([page.name])

        if oldtags != newtags:
            wikitags.replace_tags(req, page.name, newtags)

    def _wiki_edit(self, req, stream):
        insert = T.div(class_='field')(
            T.label(
                'Tag under: (', T.a('view all tags', href=req.href.tags()), ')',
                T.br(),
                T.input(id='tags', type='text', name='tags', size='30',
                        value=req.args.get('tags', ' '.join(self._page_tags(req)))),
                )
            )
        return stream | Transformer('//div[@id="changeinfo1"]').append(insert)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'wiki_view.html':
            return self._wiki_view(req, stream)
        elif filename == 'wiki_edit.html':
            return self._wiki_edit(req, stream)
        return stream

    # IWikiPageManipulator methods
    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        if req and req.path_info.startswith('/wiki') and 'save' in req.args:
            self._update_tags(req, page)
        return []

#class TagsWikiModule(WikiModule):
#    """ Replacement for the default Wiki module. Tag editing is much more
#        intuitive now, as it no longer requires the TagIt macro and JavaScript
#        magic. """
#
#    def _do_save(self, req, db, page):
#        # This method is overridden so the user doesn't get "Page not modified"
#        # exceptions when updating tags but not wiki content.
#        from tractags.api import TagEngine
#        if 'tags' in req.args:
#            newtags = set([t.strip() for t in
#                          _tag_split.split(req.args.get('tags')) if t.strip()])
#            wikitags = TagEngine(self.env).tagspace.wiki
#            oldtags = wikitags.get_tags([page.name])
#
#            if oldtags != newtags:
#                wikitags.replace_tags(req, page.name, newtags)
#                # No changes, just redirect
#                if req.args.get('text') == page.text:
#                    req.redirect(self.env.href.wiki(page.name))
#                    return
#        return WikiModule._do_save(self, req, db, page)
#
#    def process_request(self, req):
#        from tractags.api import TagEngine
#        from trac.web.chrome import add_stylesheet
#
#        add_stylesheet(req, 'tags/css/tractags.css')
#
#        pagename = req.args.get('page', 'WikiStart')
#        action = req.args.get('action', 'view')
#
#        engine = TagEngine(self.env)
#        wikitags = engine.tagspace.wiki
#        tags = list(wikitags.get_tags([pagename]))
#        tags.sort()
#
#        if action == 'edit':
#            req.hdf['tags'] = req.args.get('tags', ', '.join(tags))
#        elif action == 'view':
#            hdf_tags = []
#            for tag in tags:
#                href, title = engine.get_tag_link(tag)
#                hdf_tags.append({'name': tag,
#                                 'href': href,
#                                 'title': title})
#            req.hdf['tags'] = hdf_tags
#        result = WikiModule.process_request(self, req)
#        if result is None:
#            return None
#        if result[0] == 'wiki.cs':
#            return 'tagswiki.cs', None
#        return result

class TagsModule(Component):
    """ Serve a /tags namespace. Top-level displays tag cloud, sub-levels
        display output of ListTagged(tag).

        The following configuration options are supported:

        [tags]
        # Use a tag list or cloud for the main index
        index = cloud|list
        # The keyword arguments to pass to the TagCloud or ListTags macros that
        # is being used for the index.
        index.args = ...
        # Keyword arguments to pass to the listing for each tag under the
        # /tags/ URL space.
        listing.args = ...
    """
    implements(IRequestHandler, INavigationContributor, ITemplateProvider)

    def _prepare_wiki(self, req):
        from tractags.api import TagEngine
        page = req.path_info[6:] or 'WikiStart'
        engine = TagEngine(self.env)
        wikitags = engine.tagspace.wiki
        tags = list(wikitags.get_tags(page))
        tags.sort()

        action = req.args.get('action', 'view')
        if action == 'edit':
            req.hdf['tags'] = req.args.get('tags', ', '.join(tags))
        elif action == 'view':
            hdf_tags = []
            for tag in tags:
                href, title = engine.get_tag_link(tag)
                hdf_tags.append({'name': tag,
                                 'href': href,
                                 'title': title})
            req.hdf['tags'] = hdf_tags

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('tags', resource_filename(__name__, 'htdocs'))]
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'tags'

    def get_navigation_items(self, req):
        from trac.web.chrome import Chrome
        yield ('mainnav', 'tags',
               Markup('<a href="%s" accesskey="T">Tags</a>',
                      self.env.href.tags()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/tags')

    def process_request(self, req):
        from tractags.macros import TagMacros
        from tractags.parseargs import parseargs
        from trac.web.chrome import add_stylesheet

        add_stylesheet(req, 'tags/css/tractags.css')
        req.hdf['trac.href.tags'] = self.env.href.tags()

        def update_from_req(args):
            for k in req.args.keys():
                args[k] = unicode(req.args.get(k))

        if not req.args.has_key('e') and re.match('^/tags/?$', req.path_info):
            index = self.env.config.get('tags', 'index', 'cloud')
            index_kwargs = {'smallest': 10, 'biggest': 30}
            _, config_kwargs = parseargs(self.env.config.get('tags', 'index.args', ''))
            index_kwargs.update(config_kwargs)
            update_from_req(index_kwargs)

            if index == 'cloud':
                req.hdf['tag.body'] = Markup(
                    TagMacros(self.env).render_tagcloud(req, **index_kwargs))
            elif index == 'list':
                req.hdf['tag.body'] = Markup(
                    TagMacros(self.env).render_listtagged(req, **index_kwargs))
            else:
                raise TracError("Invalid index style '%s'" % index)
        else:
            _, args = parseargs(self.env.config.get('tags', 'listing.args', ''))
            if req.args.has_key('e'):
                expr = req.args.get('e')
            else:
                expr = req.path_info[6:]
            req.hdf['tag.title'] = Markup('Objects matching the expression <i>%s</i>' % escape(expr))
            req.hdf['tag.expression'] = expr
            try:
                Expression(expr)
            except Exception, e:
                req.hdf['tag.expression.error'] = unicode(e).replace(' (line 1)', '')
            args['expression'] = expr
            tags = []
            update_from_req(args)
            req.hdf['tag.body'] = Markup(
                TagMacros(self.env).render_listtagged(req, *tags, **args))
        return 'tags.cs', None
