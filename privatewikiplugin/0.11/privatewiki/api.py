# -*- coding: utf-8 -*-

from trac.core import *
from trac.perm import IPermissionRequestor, IPermissionGroupProvider,IPermissionPolicy,PermissionSystem
from trac.wiki.model import WikiPage
from trac.config import IntOption, ListOption

try:
    set = set
except NameError:
    from sets import Set as set

__all__ = ['PrivateWikiSystem']


class PrivateWikiSystem(Component):
    """Central tasks for the PrivateWiki plugin."""

    implements(IPermissionRequestor, IPermissionPolicy)

    group_providers = ExtensionPoint(IPermissionGroupProvider)

    wikis = ListOption('privatewikis', 'private_wikis', default='Private',
                       doc='Wikis to protect.')

    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        self.env.log.debug('Checking permission called with: action(%s), username(%s), resource(%s), perm(%s)' % (str(action), str(username), str(resource), str(perm)))
        if resource is None or resource.id is None:
            return None

        if username == 'anonymous' and resource.realm == 'wiki':
            wiki = WikiPage(self.env, resource.id)
            page = self._prep_page(wiki.name)
            if self._protected_page(page):
                return False

        if resource.realm == 'wiki' and action in ('WIKI_VIEW','WIKI_MODIFY'):
            wiki = WikiPage(self.env, resource.id)
            return self.check_wiki_access(perm, resource, action, wiki.name)
        return None

    # IPermissionRequestor methods
    def get_permission_actions(self):
        view_actions = ['PRIVATE_VIEW_' + a for a in self.wikis]
        edit_actions = ['PRIVATE_EDIT_' + a for a in self.wikis]
        return view_actions + edit_actions + \
               [('PRIVATE_VIEW_ALL', view_actions),
                ('PRIVATE_EDIT_ALL', edit_actions+view_actions)]

    def _prep_page(self, page):
        return page.upper().replace('/','_')

    def _protected_page(self, page):
        self.env.log.debug('Checking privacy of page %s' % (page))
        page = self._prep_page(page)
        member_of = []
        for base_page in self.wikis:
            if page.startswith(base_page + '_') or page == base_page:
                member_of.append(base_page)

        self.env.log.debug('Privacy check results %s' % str(member_of))
        return member_of
        
    # Public methods
    def check_wiki_access(self, perm, res, action, page):
        """Return if this req is permitted access to the given ticket ID."""

        try:
            page = self._prep_page(page)
            self.env.log.debug('Now checking for %s on %s' % (action, page))
            member_of = self._protected_page(page)
            if not member_of:
                self.env.log.debug('%s is not a private page' % page)
                return None
            for p in member_of:
                self.env.log.debug('Checking protected area: %s' % p)
                view_perm = 'PRIVATE_VIEW_%s' % p;
                edit_perm = 'PRIVATE_EDIT_%s' % p;

                if action == 'WIKI_VIEW':
                    self.env.log.debug('Protecting against VIEW')
                    if 'PRIVATE_ALL_VIEW' in perm(res) or \
                       view_perm in perm(res) or edit_perm in perm(res):
                        return True

                if action == 'WIKI_MODIFY':
                    self.env.log.debug('Protecting against MODIFY')
                    if 'PRIVATE_ALL_EDIT' in perm(res) or \
                       edit_perm in perm(res):
                        return True

        except TracError:
            return None

        return False
