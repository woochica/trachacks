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
	if username == 'anonymous' or resource is None or resource.id is None:
		return None

	if resource.realm == 'wiki' and action in ('WIKI_VIEW','WIKI_MODIFY'):
		wiki = WikiPage(self.env, resource.id)
		return self.check_wiki_access(perm, resource, action, wiki.name)
	return None;

    # IPermissionRequestor methods
    def get_permission_actions(self):
        view_actions = ['PRIVATE_VIEW_' + a for a in self.wikis]
	edit_actions = ['PRIVATE_EDIT_' + a for a in self.wikis]
        return view_actions + edit_actions + \
               [('PRIVATE_VIEW_ALL', view_actions),('PRIVATE_EDIT_ALL', edit_actions+view_actions)]

    def _prep_page(self, page):
	return page.upper().replace('/','_')

    def _protected_page(self, page):
	page = self._prep_page(page)
	member_of = []
	for base_page in self.wikis:
		if page.startswith(base_page + '_') or page == base_page:
			member_of.append(base_page)
	def compare_len(a, b):
		return cmp(len(b), len(a))

	return sorted(member_of, compare_len)
	
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
			if perm.has_permission('PRIVATE_ALL_VIEW') or \
			   perm.has_permission(view_perm):
        	            return True
	    
		    if action == 'WIKI_MODIFY':
			self.env.log.debug('Protecting against MODIFY')
                	if perm.has_permission('PRIVATE_ALL_EDIT') or \
			   perm.has_permission(edit_perm):
        	            return True
        except TracError:
            return None

        return False

