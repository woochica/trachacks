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
		return self.check_wiki_access(perm, resource, action)
	return None;

    # IPermissionRequestor methods
    def get_permission_actions(self):
        view_actions = ['PRIVATE_'+a+'_VIEW' for a in self.wikis]
	edit_actions = ['PRIVATE_'+a+'_EDIT' for a in self.wikis]
        return view_actions + edit_actions + \
               [('PRIVATE_ALL_VIEW', view_actions),('PRIVATE_ALL_EDIT', edit_actions)]

    # Public methods
    def check_wiki_access(self, perm, res, action):
        """Return if this req is permitted access to the given ticket ID."""

        try:
            wiki = WikiPage(self.env, res.id)
	    self.env.log.debug('Now accessing %s,%s' % (wiki.name,action))
	    if not (wiki.name in self.wikis):
		self.env.log.debug('Not a protected page')
		return True
	    if action == 'WIKI_VIEW':
		self.env.log.debug('Protecting against VIEW')
		if perm.has_permission('PRIVATE_ALL_VIEW') or \
		   perm.has_permission('PRIVATE_ALL_EDIT'):
                    return True
		if perm.has_permission('PRIVATE_' + wiki.name + '_VIEW') or \
		   perm.has_permission('PRIVATE_' + wiki.name + '_EDIT'):
		    return True
	    if action == 'WIKI_MODIFY':
		self.env.log.debug('Protecting against MODIFY')
                if perm.has_permission('PRIVATE_ALL_EDIT'):
                    return True
                if perm.has_permission('PRIVATE_' + wiki.name + '_EDIT'):
                    return True
	    return False
        except TracError:
            return True # Ticket doesn't exist

        return False

