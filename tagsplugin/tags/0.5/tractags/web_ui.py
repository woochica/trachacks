import re
from tractags.api import TagEngine
from StringIO import StringIO
from trac.core import *
from trac.perm import IPermissionRequestor
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
    implements(ITemplateStreamFilter, IWikiPageManipulator, IPermissionRequestor)

    # Internal methods
    def _page_tags(self, req):
        pagename = req.args.get('page', 'WikiStart')

        engine = TagEngine(self.env)
        wikitags = engine.tagspace.wiki
        current_tags = list(wikitags.get_tags([pagename]))
        current_tags.sort()
        return current_tags

    def _wiki_view(self, req, stream):
        tags = self._page_tags(req)
        if not tags:
            return stream
        engine = TagEngine(self.env)
        add_stylesheet(req, 'tags/css/tractags.css')
        li = []
        for tag in tags:
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

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['TAGS_VIEW', 'TAGS_MODIFY']

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'wiki_view.html' and 'TAGS_VIEW' in req.perm:
            return self._wiki_view(req, stream)
        elif filename == 'wiki_edit.html' and 'TAGS_MODIFY' in req.perm:
            return self._wiki_edit(req, stream)
        return stream

    # IWikiPageManipulator methods
    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        if req and 'TAGS_MODIFY' in req.perm and req.path_info.startswith('/wiki') \
                and 'save' in req.args:
            self._update_tags(req, page)
        return []


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

    # This method is never really called by anything.... Remove?
    # def _prepare_wiki(self, req):
    #     from tractags.api import TagEngine
    #     page = req.path_info[6:] or 'WikiStart'
    #     engine = TagEngine(self.env)
    #     wikitags = engine.tagspace.wiki
    #     tags = list(wikitags.get_tags(page))
    #     tags.sort()
    # 
    #     action = req.args.get('action', 'view')
    #     if action == 'edit':
    #         req.hdf['tags'] = req.args.get('tags', ', '.join(tags))
    #     elif action == 'view':
    #         hdf_tags = []
    #         for tag in tags:
    #             href, title = engine.get_tag_link(tag)
    #             hdf_tags.append({'name': tag,
    #                              'href': href,
    #                              'title': title})
    #         req.hdf['tags'] = hdf_tags

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
        if 'TAGS_VIEW' in req.perm:
            return 'tags'

    def get_navigation_items(self, req):
        from trac.web.chrome import Chrome
        if 'TAGS_VIEW' in req.perm:
            yield ('mainnav', 'tags',
                   Markup('<a href="%s" accesskey="T">Tags</a>',
                          req.href.tags()))

    # IRequestHandler methods
    def match_request(self, req):
        return 'TAGS_VIEW' in req.perm and req.path_info.startswith('/tags')

    def process_request(self, req):
        from tractags.macros import TagMacros
        from tractags.parseargs import parseargs
        from trac.web.chrome import add_stylesheet

        req.perm.require('TAGS_VIEW')

        add_stylesheet(req, 'tags/css/tractags.css')
        data = {}

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
                data['tag_body'] = Markup(
                    TagMacros(self.env).render_tagcloud(req, **index_kwargs))
            elif index == 'list':
                data['tag_body'] = Markup(
                    TagMacros(self.env).render_listtagged(req, **index_kwargs))
            else:
                raise TracError("Invalid index style '%s'" % index)
        else:
            _, args = parseargs(self.env.config.get('tags', 'listing.args', ''))
            if req.args.has_key('e'):
                expr = req.args.get('e')
            else:
                expr = req.path_info[6:]
            data['tag_title'] = Markup('Objects matching the expression <i>%s</i>' % escape(expr))
            data['tag_expression'] = expr
            try:
                Expression(expr)
            except Exception, e:
                data['tag_expression_error'] = unicode(e).replace(' (line 1)', '')
            args['expression'] = expr
            tags = []
            update_from_req(args)
            data['tag_body'] = Markup(
                TagMacros(self.env).render_listtagged(req, *tags, **args))
        return 'tags.html', data, None
