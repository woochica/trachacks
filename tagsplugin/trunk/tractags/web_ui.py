from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor
from trac.util import Markup
from StringIO import StringIO
from trac.wiki.web_ui import WikiModule
from trac.wiki.formatter import wiki_to_oneliner
import re
try:
    set = set
except:
    from sets import Set as set

_tag_split = re.compile('[,\s]+')

class TagsWikiModule(WikiModule):
    """ Replacement for the default Wiki module. Tag editing is much more
        intuitive now, as it no longer requires the TagIt macro and JavaScript
        magic. """

    def _do_save(self, req, db, page):
        # This method is overridden so the user doesn't get "Page not modified"
        # exceptions when updating tags but not wiki content.
        from tractags.api import TagEngine
        if 'tags' in req.args:
            newtags = set([t.strip() for t in
                          _tag_split.split(req.args.get('tags')) if t.strip()])
            wikitags = TagEngine(self.env).tagspace.wiki
            oldtags = wikitags.get_tags([page.name])

            if oldtags != newtags:
                wikitags.replace_tags(req, page.name, newtags)
                # No changes, just redirect
                if req.args.get('text') == page.text:
                    req.redirect(self.env.href.wiki(page.name))
                    return
        return WikiModule._do_save(self, req, db, page)

    def process_request(self, req):
        from tractags.api import TagEngine
        from trac.web.chrome import add_stylesheet

        add_stylesheet(req, 'tags/css/tractags.css')

        pagename = req.args.get('page', 'WikiStart')
        action = req.args.get('action', 'view')

        engine = TagEngine(self.env)
        wikitags = engine.tagspace.wiki
        tags = list(wikitags.get_tags([pagename]))
        tags.sort()

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
        result = WikiModule.process_request(self, req)
        if result is None:
            return None
        if result[0] == 'wiki.cs':
            return 'tagswiki.cs', None
        return result

class TagsModule(Component):
    """ Serve a /tags namespace. Top-level displays tag cloud, sub-levels
        display output of ListTagged(tag).

        The following configuration options are supported:

        [tags]
        # Use a tag list or cloud for the main index
        index = cloud|list
        # Show tagspace headings in the index
        index.showheadings = false|true
        # Minium font size for tag cloud index
        index.cloud.smallest = 10
        # Maximum font size for tag cloud index
        index.cloud.biggest = 30
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
        yield ('metanav', 'tags',
               Markup('<a href="%s" accesskey="T">Tag Index</a>',
                      self.env.href.tags()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/tags')

    def process_request(self, req):
        from tractags.macros import TagMacros
        from trac.web.chrome import add_stylesheet

        add_stylesheet(req, 'tags/css/tractags.css')
        req.hdf['trac.href.tags'] = self.env.href.tags()
        showheadings = self.config.getbool('tags', 'index.showheadings',
                                           'false') and 'true' or 'false'
        smallest = int(self.config.get('tags', 'index.cloud.smallest', 10))
        biggest = int(self.config.get('tags', 'index.cloud.biggest', 30))

        if req.path_info == '/tags':
            index = self.env.config.get('tags', 'index', 'cloud')
            if index == 'cloud':
                req.hdf['tag.body'] = Markup(
                    TagMacros(self.env).render_tagcloud(req, smallest=smallest, biggest=biggest))
            elif index == 'list':
                req.hdf['tag.body'] = Markup(
                    TagMacros(self.env).render_listtagged(req,
                        showheadings=showheadings))
            else:
                raise TracError("Invalid index style '%s'" % index)
        else:
            tag = req.path_info[6:]
            req.hdf['tag.name'] = tag
            req.hdf['tag.body'] = Markup(
                TagMacros(self.env).render_listtagged(
                    req, tag, showheadings=showheadings))
        return 'tags.cs', None

# XXX I think this is planned for some AJAX goodness, commenting out for now. (Alec) XXX
#class TagsLi(Component):
#    implements(IRequestHandler)
#    
#    # IRequestHandler methods
#    def match_request(self, req):
#        return req.path_info == '/tagli'
#                
#    def process_request(self, req):
#        db = self.env.get_db_cnx()
#        cursor = db.cursor()
#        cs = db.cursor()
#        tag = req.args.get('tag')
#        req.send_response(200)
#        req.send_header('Content-Type', 'text/plain')
#        req.end_headers()
#        buf = StringIO()
#        if tag:
#            buf.write('WHERE tag LIKE \'%s%s\'' % (tag,'%'))
#            
#        cursor.execute('SELECT DISTINCT tag FROM tags %s ORDER BY tag' % (buf.getvalue()))
#
#        msg = StringIO()
#
#        msg.write('<ul>')
#        while 1:
#            row = cursor.fetchone()
#            if row == None:
#                 break
#
#            t = row[0]
#            msg.write('<li>')
#            msg.write(t)
#            msg.write('</li>')
#
#        msg.write('</ul>')
#        req.write(msg.getvalue())
