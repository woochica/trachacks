# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2011 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from genshi.builder import Markup, tag
from genshi.filters.transform import Transformer
from trac.core import Component, ExtensionPoint, implements
from trac.mimeview.api import Context
from trac.resource import Resource, render_resource_link, get_resource_url
from trac.util.compat import sorted
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_stylesheet
from trac.wiki.api import IWikiChangeListener, IWikiPageManipulator, \
                          IWikiSyntaxProvider
from trac.wiki.model import WikiPage

from tractags.api import DefaultTagProvider, TagSystem, _
from tractags.macros import TagTemplateProvider


class WikiTagProvider(DefaultTagProvider):
    """Tag provider for Trac wiki."""
    realm = 'wiki'

    first_head = re.compile('=\s+([^=\n]*)={0,1}')

    def check_permission(self, perm, operation):
        map = {'view': 'WIKI_VIEW', 'modify': 'WIKI_MODIFY'}
        return super(WikiTagProvider, self).check_permission(perm, operation) \
            and map[operation] in perm

    def describe_tagged_resource(self, req, resource):
        if not self.check_permission(req.perm(resource), 'view'):
            return ''
        page = WikiPage(self.env, resource.id)
        if page.exists:
            ret = self.first_head.search(page.text)
            return ret and ret.group(1) or ''
        return ''


class WikiTagInterface(TagTemplateProvider):
    """Implement the user interface for tagging Wiki pages."""
    implements(IRequestFilter, ITemplateStreamFilter,
               IWikiChangeListener, IWikiPageManipulator)

    PAGE_TEMPLATES_PREFIX = 'PageTemplates/'

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.method == 'GET' and req.path_info.startswith('/wiki/') and \
                req.args.get('action') == 'edit' and \
                req.args.get('template') and 'tags' not in req.args:
            # Retrieve template resource to be queried for tags.
            template_page = WikiPage(self.env,''.join(
                                     [self.PAGE_TEMPLATES_PREFIX,
                                      req.args.get('template')]))
            if template_page and template_page.exists and \
                    'TAGS_VIEW' in req.perm(template_page.resource):
                ts = TagSystem(self.env)
                tags = sorted(ts.get_tags(req, template_page.resource))
                # Prepare tags as content for the editor field.
                tags_str = ' '.join(tags)
                self.env.log.debug("Tags retrieved from template: '%s'" \
                                   % unicode(tags_str).encode('utf-8'))
                # DEVEL: More arguments need to be propagated here?
                req.redirect(req.href(req.path_info,
                                      action='edit', tags=tags_str,
                                      template=req.args.get('template')))
        return (template, data, content_type)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        page_name = req.args.get('page', 'WikiStart')
        resource = Resource('wiki', page_name)
        if filename == 'wiki_view.html' and 'TAGS_VIEW' in req.perm(resource):
            return self._wiki_view(req, stream)
        elif filename == 'wiki_edit.html' and 'TAGS_MODIFY' in req.perm(resource):
            return self._wiki_edit(req, stream)
        return stream

    # IWikiPageManipulator methods
    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        # If we're saving the wiki page, and can modify tags, do so
        if req and 'TAGS_MODIFY' in req.perm(page.resource) \
                and req.path_info.startswith('/wiki') and 'save' in req.args:
            page_modified = req.args.get('text') != page.old_text or \
                    page.readonly != int('readonly' in req.args)
            # Always save tags if the page has been otherwise modified
            if page_modified:
                self._update_tags(req, page)
            elif page.version > 0:
                # If the page hasn't been otherwise modified, save the tags
                # and redirect so we don't get the "page has not been modified"
                # warning
                if self._update_tags(req, page):
                    req.redirect(get_resource_url(self.env, page.resource, req.href, version=None))
        return []

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        pass

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_renamed(self, page, old_name):
        """Called when a page has been renamed (since Trac 0.12)."""
        new_resource = Resource('wiki', page.name)
        old_resource = Resource('wiki', old_name)
        self.log.debug("Moving tags from %s to %s",
                       old_resource.id, new_resource.id)
        tag_system = TagSystem(self.env)
        # XXX Ugh. Hopefully this will be sufficient to fool any endpoints.
        from trac.test import Mock, MockPerm
        req = Mock(authname='anonymous', perm=MockPerm())
        tag_system.reparent_tags(req, old_resource, new_resource)

    def wiki_page_deleted(self, page):
        tag_system = TagSystem(self.env)
        # XXX Ugh. Hopefully this will be sufficient to fool any endpoints.
        from trac.test import Mock, MockPerm
        req = Mock(authname='anonymous', perm=MockPerm())
        tag_system.delete_tags(req, page.resource)

    def wiki_page_version_deleted(self, page):
        pass

    # Internal methods
    def _page_tags(self, req):
        pagename = req.args.get('page', 'WikiStart')

        tag_system = TagSystem(self.env)
        resource = Resource('wiki', pagename)
        tags = sorted(tag_system.get_tags(req, resource))
        return tags

    def _wiki_view(self, req, stream):
        add_stylesheet(req, 'tags/css/tractags.css')
        tags = self._page_tags(req)
        if not tags:
            return stream
        tag_system = TagSystem(self.env)
        li = []
        for tag_ in tags:
            resource = Resource('tag', tag_)
            anchor = render_resource_link(self.env,
                Context.from_request(req, resource), resource)
            anchor = anchor(rel='tag')
            li.append(tag.li(anchor, ' '))

        # TRANSLATOR: Header label text for tag list at wiki page bottom.
        insert = tag.ul(class_='tags')(tag.li(_("Tags"), class_='header'), li)
        return stream | Transformer('//div[contains(@class,"wikipage")]').after(insert)

    def _update_tags(self, req, page):
        tag_system = TagSystem(self.env)
        newtags = tag_system.split_into_tags(req.args.get('tags', ''))
        oldtags = tag_system.get_tags(req, page.resource)

        if oldtags != newtags:
            tag_system.set_tags(req, page.resource, newtags)
            return True
        return False

    def _wiki_edit(self, req, stream):
        # TRANSLATOR: Label text for link to '/tags'.
        link = tag.a(_("view all tags"), href=req.href.tags())
        # TRANSLATOR: ... (view all tags)
        insert = tag(Markup(_("Tag under: (%(tags_link)s)", tags_link=link)))
        insert(
            tag.br(),
            tag.input(id='tags', type='text', name='tags', size='50',
                value=req.args.get('tags', ' '.join(self._page_tags(req))))
        )
        insert = tag.div(tag.label(insert), class_='field')
        return stream | Transformer('//div[@id="changeinfo1"]').append(insert)


class TagWikiSyntaxProvider(Component):
    """Provide tag:<expr> links."""

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        yield (r'''\[tag(?:ged)?:(?P<tlpexpr>(?:'.*?'|".*?"|\S)+)\s+(?P<tlptitle>.*?]*)\]''',
               lambda f, n, m: self._format_tagged(f,
                                    m.group('tlpexpr'),
                                    m.group('tlptitle')))
        yield (r'''(?P<tagsyn>tag(?:ged)?):(?P<texpr>(?:'.*?'|".*?"|\S)+)''',
               lambda f, n, m: self._format_tagged(f,
                                    m.group('texpr'),
                                    '%s:%s' % (m.group('tagsyn'), m.group('texpr'))))

    def get_link_resolvers(self):
        return []

    def _format_tagged(self, formatter, target, label):
        if label:
            href = formatter.context.href
            url = get_resource_url(self.env, Resource('tag', target), href)
            return tag.a(label, href=url)
        return render_resource_link(self.env, formatter.context,
                                    Resource('tag', target))

