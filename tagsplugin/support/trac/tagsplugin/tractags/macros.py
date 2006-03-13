from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki import model 
from trac.util import Markup
from trac.wiki import wiki_to_html, wiki_to_oneliner
from StringIO import StringIO
from tractags.api import TagEngine, ITagSpaceUser
import inspect
import re
import string
try:
    set()
except:
    from sets import Set as set

class TagMacros(Component):
    """ Versions of the old Wiki-only macros using the new tag API. """

    implements(IWikiMacroProvider)

    def _page_titles(self, pages):
        """ Extract page titles, if possible. """
        titles = {}
        for pagename in pages:
            href, link, title = TagEngine(self.env).wiki.name_link(pagename)
            titles[pagename] = title
        return titles

    def _tag_details(self, tags):
        """ Extract dictionary of tag:(href, title) for all tags. """
        links = {}
        for tag in tags:
            links[tag] = TagEngine(self.env).get_tag_link(tag)
        return links

    def _current_page(self, req):
        return req.hdf.getValue('wiki.page_name', '')

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'TagCloud'
        yield 'ListTagged'
        yield 'TagIt'
        yield 'ListTags'

    def get_macro_description(self, name):
        import pydoc
        return pydoc.getdoc(getattr(self, 'render_' + name))

    def render_macro(self, req, name, content):
        from trac.web.chrome import add_stylesheet
        add_stylesheet(req, 'tags/css/tractags.css')
        # Translate macro args into python args
        args = []
        kwargs = {}
        if content is not None:
            try:
                from parseargs import parseargs
                args, kwargs = parseargs(content)
            except Exception, e:
                raise TracError("Invalid arguments '%s' (%s %s)" % (content, e.__class__.__name__, e))
        return getattr(self, 'render_' + name.lower(), content)(req, *args, **kwargs)

    # Macro implementations
    def render_tagcloud(self, req, smallest=10, biggest=20, tagspace=None, tagspaces=[]):
        """ Display a summary of all tags, with the font size reflecting the
            number of pages the tag applies to. Font size ranges from 10 to 22
            pixels, but this can be overridden by the smallest=n and biggest=n
            macro parameters. By default, all tagspaces are displayed, but this
            can be overridden with tagspaces=(wiki, ticket) or tagspace=wiki."""
        range = (int(smallest), int(biggest))
        # Get wiki tagspace
        if tagspace:
            tagspaces = [tagspace]
        else:
            tagspaces = tagspaces or TagEngine(self.env).tagspaces
        cloud = {}
        min, max = 9999, 0

        for tagspace in tagspaces:
            tagsystem = TagEngine(self.env).get_tagsystem(tagspace)
            for tag in tagsystem.get_tags():
                count = tagsystem.count_tagged_names(tag)
                if tag in cloud:
                    count += cloud[tag]
                cloud[tag] = count
                if count < min: min = count
                if count > max: max = count

        tags = cloud.keys()

        # No tags?
        if not tags: return ''

        taginfo = self._tag_details(tags)
        tags.sort()
        rlen = float(range[1] - range[0])
        tlen = float(max - min)
        scale = 1.0
        if tlen:
            scale = rlen / tlen
        out = StringIO()
        out.write('<ul class="tagcloud">\n')
        last = tags[-1]
        for tag in tags:
            if tag == last:
                cls = ' class="last"'
            else:
                cls = ''
            out.write('<li%s><a rel="tag" title="%s" style="font-size: %ipx" href="%s">%s</a> <span class="tagcount">(%i)</span></li>\n' % (
                       cls,
                       taginfo[tag][1],
                       range[0] + int((cloud[tag] - min) * scale),
                       taginfo[tag][0],
                       tag,
                       cloud[tag]))
        out.write('</ul>\n')
        return out.getvalue()

    def render_listtagged(self, req, *tags, **kwargs):
        """ List tagged objects. Takes a list of tags to match against.
            The special tag '.' inserts the current Wiki page name.

            Optional keyword arguments are tagspace=wiki,
            tagspaces=(wiki, title, ...) and showheadings=true."""

        if 'tagspace' in kwargs:
            tagspaces = [kwargs.get('tagspace', None)]
        else:
            tagspaces = kwargs.get('tagspaces', '') or \
                        list(TagEngine(self.env).tagspaces)
        showheadings = kwargs.get('showheadings', 'false')
        alltags = set()
        tags = set([str(x) for x in tags])
        if '.' in tags:
            page = self._current_page(req)
            if page:
                tags.add(page)
            tags.remove('.')

        names = {}

        for tagspace in tagspaces:
            tagsystem = TagEngine(self.env).get_tagsystem(tagspace)
            for name in tagsystem.get_tagged_names(*tags):
                if tagspace == 'wiki' and name.startswith('tags/'):
                    continue
                ntags = list(tagsystem.get_tags(name))
                alltags.update(ntags)
                names.setdefault((tagspace, name), {
                    'tags': ntags,
                    'tagsystem': tagsystem,
                })

        # Get tag page titles, if any
        taginfo = self._tag_details(alltags)

        # List names and tags
        keys = names.keys()
        keys.sort()
        current_ns = None
        out = StringIO()
        out.write('<ul class="listtagged">')
        for tagspace, name in keys:
            if showheadings == 'true' and tagspace != current_ns:
                out.write('<lh>%s tags</lh>' % tagspace)
                current_ns = tagspace
            details = names[(tagspace, name)]
            tagsystem = details['tagsystem']
            href, link, title = tagsystem.name_link(name)
            hlink = wiki_to_oneliner(link, self.env)
            htitle = wiki_to_oneliner(title, self.env)
            name_tags = ['<a href="%s" title="%s">%s</a>'
                          % (taginfo[tag][0], taginfo[tag][1], tag)
                          for tag in details['tags'] if tag not in tags]
            if not name_tags:
                name_tags = ''
            else:
                name_tags = ' (' + ', '.join(name_tags) + ')'
            out.write('<li><a href="%s" title="%s">%s</a> %s%s</li>\n' %
                      (href, title, hlink, htitle, name_tags))
        out.write('</ul>')

        return out.getvalue()

    def render_tagit(self, req, *tags):
        """ Tag the current page and display the current tags. """
        page = self._current_page(req)
        if not page: return

        wiki = TagEngine(self.env).wiki
        wiki.replace_tags(req, page, *tags)

        out = StringIO()
        taginfo = self._tag_details(tags)
        out.write('<ul class="tagit">\n')
        for tag in tags:
            out.write('<li><a href="%s" title="%s">%s</a></li>\n' % (taginfo[tag][0], taginfo[tag][1], tag))
        out.write('</ul>\n')
        return out.getvalue()

    def render_listtags(self, req, *tags, **kwargs):
        """ List tags. For backwards compatibility, can accept a list of tags.
            This will simply call ListTagged. Optional keyword arguments are
            tagspace=wiki, tagspaces=(wiki, ticket, ...) and shownames=true. """
        if tags:
            # Backwards compatibility
            return self.render_listtagged(req, *tags, **kwargs)

        page = self._current_page(req)
        wiki = TagEngine(self.env).wiki

        showpages = kwargs.get('showpages', None) or kwargs.get('shownames', 'false')

        if 'tagspace' in kwargs:
            tagspaces = [kwargs['tagspace']]
        else:
            tagspaces = kwargs.get('tagspaces', []) or \
                        list(TagEngine(self.env).tagspaces)

        tags = {}
        for tagspace in tagspaces:
            tagsystem = TagEngine(self.env).get_tagsystem(tagspace)
            for tag in tagsystem.get_tags():
                count = tags.get(tag, 0) + tagsystem.count_tagged_names(tag)
                tags[tag] = count
            
        out = StringIO()
        out.write('<ul class="listtags">\n')
        keys = tags.keys()
        taginfo = self._tag_details(keys)
        keys.sort()
        for tag in keys:
            href, title = taginfo[tag]
            htitle = wiki_to_oneliner(title, self.env)
            out.write('<li><a href="%s" title="%s">%s</a> %s (%i)' % (href, title, tag, htitle, tags[tag]))
            if showpages == 'true':
                out.write('\n')
                out.write(self.render_listtagged(req, tag, tagspaces=tagspaces))
                out.write('</li>\n')
        out.write('</ul>\n')

        return out.getvalue()
