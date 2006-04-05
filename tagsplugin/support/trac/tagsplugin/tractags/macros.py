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
    sorted = sorted
except NameError:
    def sorted(iterable, cmp=None, key=str, reverse=False):
        lst = [(key(i), i) for i in iterable]
        lst.sort()
        if reverse:
            lst = reversed(lst)
        return [i for __, i in lst]

try:
    set = set
except:
    from sets import Set as set

class TagMacros(Component):
    """ Versions of the old Wiki-only macros using the new tag API. """

    implements(IWikiMacroProvider)

    def _page_titles(self, pages):
        """ Extract page titles, if possible. """
        titles = {}
        tagspace = TagEngine(self.env).tagspace.wiki
        for pagename in pages:
            href, link, title = tagspace.name_details(pagename)
            titles[pagename] = title
        return titles

    def _tag_details(self, links, tags):
        """ Extract dictionary of tag:(href, title) for all tags. """
        for tag in tags:
            if tag not in links:
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
        return pydoc.getdoc(getattr(self, 'render_' + name.lower()))

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
        smallest = int(smallest)
        biggest = int(biggest)
        engine = TagEngine(self.env)
        # Get wiki tagspace
        if tagspace:
            tagspaces = [tagspace]
        else:
            tagspaces = tagspaces or engine.tagspaces
        cloud = {}

        for tag, names in engine.get_tags(tagspaces=tagspaces, detailed=True).iteritems():
            cloud[tag] = len(names)

        tags = cloud.keys()

        # No tags?
        if not tags: return ''

        # by_count maps tag counts to an index in the set of counts
        by_count = list(set(cloud.values()))
        by_count.sort()
        by_count = dict([(c, float(i)) for i, c in enumerate(by_count)])

        taginfo = self._tag_details({}, tags)
        tags.sort()
        rlen = float(biggest - smallest)
        tlen = float(len(by_count))
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
                       smallest + int(by_count[cloud[tag]] * scale),
                       taginfo[tag][0],
                       tag,
                       cloud[tag]))
        out.write('</ul>\n')
        return out.getvalue()

    def render_listtagged(self, req, *tags, **kwargs):
        """ List tagged objects. Takes a list of tags to match against.
            The special tag '.' inserts the current Wiki page name.

            Optional keyword arguments are tagspace=wiki,
            tagspaces=(wiki, title, ...) and showheadings=true.

            By default displays the intersection of objects matching each tag.
            By passing operation=union this can be modified to display
            the union of objects matching each tag.
        """

        if 'tagspace' in kwargs:
            tagspaces = [kwargs.get('tagspace', None)]
        else:
            tagspaces = kwargs.get('tagspaces', '') or \
                        list(TagEngine(self.env).tagspaces)
        showheadings = kwargs.get('showheadings', 'false')
        operation = kwargs.get('operation', 'intersection')
        if operation not in ('union', 'intersection'):
            raise TracError("Invalid tag set operation '%s'" % operation)

        engine = TagEngine(self.env)
        page_name = req.hdf.get('wiki.page_name')
        if page_name:
            tags = [tag == '.' and page_name or tag for tag in tags]

        taginfo = {}
        out = StringIO()
        out.write('<ul class="listtagged">')
        for tagspace, tagspace_names in sorted(engine.get_tagged_names(tags=tags, tagspaces=tagspaces, operation=operation, detailed=True).iteritems()):
            if showheadings == 'true':
                out.write('<lh>%s tags</lh>' % tagspace)
            for name, tags in sorted(tagspace_names.iteritems()):
                if tagspace == 'wiki' and unicode(name).startswith('tags/'): continue
                tags = sorted(tags)
                taginfo = self._tag_details(taginfo, tags)
                href, link, title = engine.name_details(tagspace, name)
                htitle = wiki_to_oneliner(title, self.env)
                name_tags = ['<a href="%s" title="%s">%s</a>'
                              % (taginfo[tag][0], taginfo[tag][1], tag)
                              for tag in tags]
                if not name_tags:
                    name_tags = ''
                else:
                    name_tags = ' (' + ', '.join(sorted(name_tags)) + ')'
                out.write('<li>%s %s%s</li>\n' %
                          (link, htitle, name_tags))
        out.write('</ul>')

        return out.getvalue()

    def render_tagit(self, req, *tags):
        """ Tag the current page and display them (deprecated). """
        return ''

    def render_listtags(self, req, *tags, **kwargs):
        """ List tags. For backwards compatibility, can accept a list of tags.
            This will simply call ListTagged. Optional keyword arguments are
            tagspace=wiki, tagspaces=(wiki, ticket, ...) and shownames=true. """
        if tags:
            # Backwards compatibility
            return self.render_listtagged(req, *tags, **kwargs)

        page = self._current_page(req)
        engine = TagEngine(self.env)

        showpages = kwargs.get('showpages', None) or kwargs.get('shownames', 'false')

        if 'tagspace' in kwargs:
            tagspaces = [kwargs['tagspace']]
        else:
            tagspaces = kwargs.get('tagspaces', []) or \
                        list(TagEngine(self.env).tagspaces)

        out = StringIO()
        out.write('<ul class="listtags">\n')
        tag_details = {}
        for tag, names in sorted(engine.get_tags(tagspaces=tagspaces, detailed=True).iteritems()):
            href, title = engine.get_tag_link(tag)
            htitle = wiki_to_oneliner(title, self.env)
            out.write('<li><a href="%s" title="%s">%s</a> %s <span class="tagcount">(%i)</span>' % (href, title, tag, htitle, len(names)))
            if showpages == 'true':
                out.write('\n')
                out.write(self.render_listtagged(req, tag, tagspaces=tagspaces))
                out.write('</li>\n')

        out.write('</ul>\n')

        return out.getvalue()
