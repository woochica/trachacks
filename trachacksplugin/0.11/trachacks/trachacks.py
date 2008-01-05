# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
from trac.core import *
from trac.config import *
from acct_mgr.htfile import HtPasswdStore
from acct_mgr.api import IPasswordStore
from trac.wiki.model import WikiPage
from trac.util.compat import sorted
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_script, add_ctxtnav
from trac.resource import get_resource_url
from tractags.api import TagSystem
from tractags.macros import render_cloud
from tractags.query import Query
from tracvote import VoteSystem
from genshi.builder import tag as builder



def pluralise(n, word):
    """Return a (naively) pluralised phrase from a count and a singular
    word."""
    if n == 0:
        return 'No %ss' % word
    elif n == 1:
        return '%i %s' % (n, word)
    else:
        return '%i %ss' % (n, word)


def natural_sort(l):
  """Sort the given list in the way that humans expect."""
  convert = lambda text: int(text) if text.isdigit() else text
  alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
  return sorted(l, key=alphanum_key)


class TracHacksHandler(Component):
    """Trac-Hacks request handler."""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    limit = IntOption('trachacks', 'limit', 25,
        'Default maximum number of hacks to display.')

    path_match = re.compile(r'/hacks/?(new|cloud|list)?')
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)
    page_split = re.compile(r'(\w+)', re.I | re.UNICODE)

    # IRequestHandler methods
    def match_request(self, req):
        return self.path_match.match(req.path_info)

    def process_request(self, req):
        data = {}
        tag_system = TagSystem(self.env)

        match = self.path_match.match(req.path_info)
        view = 'cloud'
        if match.group(1):
            view = match.group(1)

        # Hack types
        types = [r.id for r, _ in tag_system.query(req, 'realm:wiki type')]
        # Trac releases
        releases = natural_sort([r.id for r, _ in
                                 tag_system.query(req, 'realm:wiki release')])

        data['types'] = types
        data['releases'] = releases

        if view != 'new':
            hacks = self.fetch_hacks(req, data, types)

        add_stylesheet(req, 'tags/css/tractags.css')
        add_stylesheet(req, 'hacks/css/trachacks.css')
        add_script(req, 'hacks/js/trachacks.js')

        views = ['cloud', 'list', 'new']
        for v in views:
            if v != view:
                if v != 'new':
                    args = req.args
                else:
                    args = {}
                add_ctxtnav(req, builder.a(v.title(),
                            href=req.href.hacks(v, **args)))
            else:
                add_ctxtnav(req, v.title())
        if view == 'list':
            return self.render_list(req, data, hacks)
        elif view == 'new':
            return self.render_new(req, data)
        return self.render_cloud(req, data, hacks)

    def render_new(self, req, data):
        add_script(req, 'common/js/wikitoolbar.js')
        return 'hacks_new.html', data, None

    def render_list(self, req, data, hacks):
        ul = builder.ul()
        for votes, rank, resource, tags, title in sorted(hacks, key=lambda h: h[2].id):
            li = builder.li(builder.a(resource.id,
                                      href=req.href.wiki(resource.id)),
                            ' - ', title)
            ul(li)
        data['body'] = ul
        return 'hacks_view.html', data, None

    def render_cloud(self, req, data, hacks):
        by_name = dict([(r[2].id, r) for r in hacks])

        def link_renderer(tag, count, percent):
            votes, rank, resource, tags, title = by_name[tag]
            href = req.href.wiki(resource.id)
            font_size = 10.0 + (percent * 20.0)
            colour = 128.0 - (percent * 128.0)
            colour = '#%02x%02x%02x' % ((colour,) * 3)
            a = builder.a(tag, rel='tag', title=title, href=href, class_='tag',
                style='font-size: %ipx; color: %s' % (font_size, colour))
            return a

        cloud_hacks = dict([(hack[2].id, hack[0]) for hack in hacks])
        data['body'] = render_cloud(self.env, req, cloud_hacks, link_renderer)

        return 'hacks_view.html', data, None

    def fetch_hacks(self, req, data, types):
        """Return a list of hacks in the form

        [votes, rank, resource, tags, title]
        """
        tag_system = TagSystem(self.env)
        vote_system = VoteSystem(self.env)

        tagged = tag_system.query(req, 'realm:wiki (' + ' or '.join(types) + ')')

        # Limit
        try:
            limit = int(req.args.get('limit', self.limit))
            data['limit_message'] = 'top %s' % limit
        except ValueError:
            data['limit_message'] = 'all'
            limit = 9999
        data['limit'] = limit

        # Query
        q = req.args.get('q', '')
        data['query'] = q
        query = Query(q.lower())

        # Build hacks list
        hacks = []
        for resource, tags in tagged:
            page = WikiPage(self.env, resource.id)
            if q:
                text = page.name.lower() + page.text.lower() + ' '.join(tags)
                if not query(text):
                    continue
            _, count, _ = vote_system.get_vote_counts(resource)
            match = self.title_extract.search(page.text)
            count_string = pluralise(count, 'vote')
            if match:
                title = '%s (%s)' % (match.group(1).strip(), count_string)
            else:
                title = '%s' % count_string
            hacks.append([count, None, resource, tags, title])

        # Rank
        total_hack_count = len(hacks)
        hacks = sorted(hacks, key=lambda i: -i[0])[:limit]

        # Navigation
        if len(hacks) >= limit:
            add_ctxtnav(req, builder.a('More', href='?limit=%i&q=%s' % (limit + 10, q)))
            limit = len(hacks)
            data['limit'] = data['limit_message'] = limit
        else:
            add_ctxtnav(req, 'More')
        if q or limit != self.limit:
            add_ctxtnav(req, builder.a('Default', href='?limit=%i' % self.limit))
        else:
            add_ctxtnav(req, 'Default')
        if total_hack_count > limit:
            add_ctxtnav(req, builder.a('All', href='?limit=all&q=' + q))
        else:
            add_ctxtnav(req, 'All')
        if limit > 10:
            limit = min(limit, len(hacks))
            add_ctxtnav(req, builder.a('Less', href='?limit=%i&q=%s' % (limit - 10 > 0 and limit - 10 or 0, q)))
        else:
            add_ctxtnav(req, 'Less')
        for i, hack in enumerate(hacks):
            hack[1] = i
        return hacks

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'hacks'

    def get_navigation_items(self, req):
        yield ('mainnav', 'hacks',
                builder.a('Hacks', href=req.href.hacks(), accesskey='H'))

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
        return [('hacks', resource_filename(__name__, 'htdocs'))]



class TracHacksAccountManager(HtPasswdStore):
    """ Do some basic validation on new users, and create a new user page. """
    implements(IPasswordStore)

    # IPasswordStore
    def config_key(self):
        return 'trachacks-htpasswd'

    def set_password(self, user, password):
        import re
        if len(user) < 3:
            raise TracError('user name must be at least 3 characters long')
        if not re.match(r'^\w+$', user):
            raise TracError('user name must consist only of alpha-numeric characters')
        if user not in self.get_users():
            from trac.wiki.model import WikiPage
            db = self.env.get_db_cnx()
            page = WikiPage(self.env, user, db=db)
            # User creation with existing page
            if page.exists:
                raise TracError('wiki page "%s" already exists' % user)
            else:
                from tractags.api import TagEngine
                tagspace = TagEngine(self.env).tagspace.wiki

                tagspace.add_tags(None, user, ['user'])
                page.text = '''= %(user)s =\n\n[[ListTagged(%(user)s)]]\n\n[[TagIt(user)]]''' % {'user' : user}
                page.save(user, 'New user %s registered' % user, None)
                self.env.log.debug("New user %s registered" % user)
        HtPasswdStore.set_password(self, user, password)

    def delete_user(self, user):
        HtPasswdStore.delete_user(self, user)
