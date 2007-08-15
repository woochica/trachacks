from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki import model 
from trac.wiki import wiki_to_html, wiki_to_oneliner
from StringIO import StringIO
from tractags.api import TagEngine, ITagSpaceUser, sorted, set
import inspect
import re
import string

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
        from parseargs import parseargs
        add_stylesheet(req, 'tags/css/tractags.css')
        # Translate macro args into python args
        args = []
        kwargs = {}
        try:
            # Set default args from config
            _, config_args = parseargs(self.env.config.get('tags', '%s.args' % name.lower(), ''))
            kwargs.update(config_args)
            if content is not None:
                args, macro_args = parseargs(content)
                kwargs.update(macro_args)
        except Exception, e:
            raise TracError("Invalid arguments '%s' (%s %s)" % (content, e.__class__.__name__, e))

        return getattr(self, 'render_' + name.lower(), content)(req, *args, **kwargs)

    # Macro implementations
    def render_tagcloud(self, req, smallest=10, biggest=20, showcount=True, tagspace=None, mincount=1, tagspaces=[], **kwargs):
        """ This macro displays a [http://en.wikipedia.org/wiki/Tag_cloud tag cloud] (weighted list)
            of all tags.

            ||'''Argument'''||'''Description'''||
            ||`tagspace=<tagspace>`||Specify the tagspace the macro should operate on.||
            ||`tagspaces=(<tagspace>,...)`||Specify a set of tagspaces the macro should operate on.||
            ||`smallest=<n>`||The lower bound of the font size for the tag cloud.||
            ||`biggest=<n>`||The upper bound of the font size for the tag cloud.||
            ||`showcount=true|false`||Show the count of objects for each tag?||
            ||`mincount=<n>`||Hide tags with a count less than `<n>`.||
            """

        smallest = int(smallest)
        biggest = int(biggest)
        mincount = int(mincount)

        engine = TagEngine(self.env)
        # Get wiki tagspace
        if tagspace:
            tagspaces = [tagspace]
        else:
            tagspaces = tagspaces or engine.tagspaces
        cloud = {}

        for tag, names in engine.get_tags(tagspaces=tagspaces, detailed=True).iteritems():
            count = len(names)
            if count >= mincount:
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
            if showcount != 'false':
                count = ' <span class="tagcount">(%i)</span>' % cloud[tag]
            else:
                count = ''
            out.write('<li%s><a rel="tag" title="%s" style="font-size: %ipx" href="%s">%s</a>%s</li>\n' % (
                       cls,
                       taginfo[tag][1] + ' (%i)' % cloud[tag],
                       smallest + int(by_count[cloud[tag]] * scale),
                       taginfo[tag][0],
                       tag,
                       count))
        out.write('</ul>\n')
        return out.getvalue()

    def render_listtagged(self, req, *tags, **kwargs):
        """ List tagged objects. Optionally accepts a list of tags to match
            against.  The special tag '''. (dot)''' inserts the current Wiki page name.

            `[[ListTagged(<tag>, ...)]]`

            ||'''Argument'''||'''Description'''||
            ||`tagspace=<tagspace>`||Specify the tagspace the macro should operate on.||
            ||`tagspaces=(<tagspace>,...)`||Specify a set of tagspaces the macro should operate on.||
            ||`operation=intersection|union`||The set operation to perform on the discovered objects.||
            ||`showheadings=true|false`||List objects under the tagspace they occur in.||
            ||`expression=<expr>`||Match object tags against the given expression.||

            The supported expression operators are: unary - (not); binary +, -
            and | (and, and not, or). All values in the expression are treated
            as tags. Any tag not in the same form as a Python variable must be
            quoted.
            
            eg. Match all objects tagged with ticket and workflow, and not
            tagged with wiki or closed.
            
                (ticket+workflow)-(wiki|closed)

            If an expression is provided operation is ignored.
        """

        if 'tagspace' in kwargs:
            tagspaces = [kwargs.get('tagspace', None)]
        else:
            tagspaces = kwargs.get('tagspaces', '') or \
                        list(TagEngine(self.env).tagspaces)
        expression = kwargs.get('expression', None)
        showheadings = kwargs.get('showheadings', 'false')
        operation = kwargs.get('operation', 'intersection')
        if operation not in ('union', 'intersection'):
            raise TracError("Invalid tag set operation '%s'" % operation)

        engine = TagEngine(self.env)
        page_name = req.hdf.get('wiki.page_name')
        if page_name:
            tags = [tag == '.' and page_name or tag for tag in tags]

        tags = set(tags)
        taginfo = {}
        out = StringIO()
        out.write('<ul class="listtagged">\n')
        # If expression was passed as an argument, do a full walk, using the
        # expression as the predicate. Silently assumes that failed expressions
        # are normal tags.
        if expression:
            from tractags.expr import Expression
            try:
                expr = Expression(expression)
            except Exception, e:
                self.env.log.error("Invalid expression '%s'" % expression, exc_info=True)
                tags.update([x.strip() for x in re.split('[+,]', expression) if x.strip()])
                expression = None
            else:
                self.env.log.debug(expr.ast)
                tagged_names = {}
                tags.update(expr.get_tags())
                for tagspace, name, name_tags in engine.walk_tagged_names(tags=tags,
                        tagspaces=tagspaces, predicate=lambda ts, n, t: expr(t)):
                    tagged_names.setdefault(tagspace, {})[name] = name_tags
                tagged_names = [(tagspace, names) for tagspace, names in tagged_names.iteritems()]

        if not expression:
            tagged_names = [(tagspace, names) for tagspace, names in
                            engine.get_tagged_names(tags=tags, tagspaces=tagspaces,
                                operation=operation, detailed=True).iteritems()
                            if names]

        for tagspace, tagspace_names in sorted(tagged_names):
            if showheadings == 'true':
                out.write('<lh>%s tags</lh>' % tagspace)
            for name, tags in sorted(tagspace_names.iteritems()):
                if tagspace == 'wiki' and unicode(name).startswith('tags/'): continue
                tags = sorted(tags)
                taginfo = self._tag_details(taginfo, tags)
                href, link, title = engine.name_details(tagspace, name)
                htitle = wiki_to_oneliner(title, self.env, req=req)
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
        """ '''''Deprecated. Does nothing.''''' """
        return ''

    def render_listtags(self, req, *tags, **kwargs):
        """ List all tags.

            ||'''Argument'''||'''Description'''||
            ||`tagspace=<tagspace>`||Specify the tagspace the macro should operate on.||
            ||`tagspaces=(<tagspace>,...)`||Specify a set of tagspaces the macro should operate on.||
            ||`shownames=true|false`||Whether to show the objects that tags appear on ''(long)''.||
            """

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
            htitle = wiki_to_oneliner(title, self.env, req=req)
            out.write('<li><a href="%s" title="%s">%s</a> %s <span class="tagcount">(%i)</span>' % (href, title, tag, htitle, len(names)))
            if showpages == 'true':
                out.write('\n')
                out.write(self.render_listtagged(req, tag, tagspaces=tagspaces))
                out.write('</li>\n')

        out.write('</ul>\n')

        return out.getvalue()
