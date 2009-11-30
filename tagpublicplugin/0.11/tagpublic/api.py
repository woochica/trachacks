from trac.core import *
from trac.perm import IPermissionPolicy
from trac.util.compat import set

__all__ = ['TagPublic']


class TagPublic(Component):
    """Central tasks for the TagPublic plugin."""
    
    implements(IPermissionPolicy)

    tags_to_publish = ['public']
    
    # IPermissionPolicy(Interface)
    def check_permission(self, action, username, resource, perm):
        if (username != 'anonymous'):
	    return None
#        self.env.log.debug('FFFFFFFOOOOOOOOOOOOOO action=%s username=%s, resource=%s, perm=%s' % (action, username, resource, perm))
	if action not in ['WIKI_VIEW','BLOG_VIEW','TICKET_VIEW','TAGS_VIEW','SEARCH_VIEW','TIMELINE_VIEW','ATTACHMENT_VIEW']:
	    return None
	if (resource is None):
#	    self.env.log.debug('precheck1=! -> allow')
	    return True
	if (resource.realm is None):
#	    self.env.log.debug('precheck2?! -> allow')
            return True

#	self.env.log.debug('FNORDDDDDDDD resource.id = "%s" resource.realm = "%s"' % (resource.id, resource.realm))

	if (resource.id is None):
#	    self.env.log.debug('resource.id is none -> allow')
            return True

	tags = self.get_tags(resource)
#	self.env.log.debug('BAAAAAR ressource tags ="%s"' % tags)
#	if tags is None:
#	   return None
	for bla in self.tags_to_publish:
		if (bla in tags):
#			self.env.log.debug('HOOORAY! bla = %s' % bla)
			return True
#	self.env.log.debug('FRACK!!')
	return None

    def get_tags_res(self, resource):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
	if resource.realm == "wiki":
	        cursor.execute('SELECT tag FROM tags WHERE tagspace=%s AND name=%s',
        	               (resource.realm, resource.id))
	elif resource.realm == "ticket":
		cursor.execute('SELECT keywords FROM ticket WHERE id=%s', (resource.id,))
	elif resource.realm == "blog":
		cursor.execute('SELECT categories,max(version) from fullblog_posts where name=%s', (resource.id,))
#	elif resource.realm = "tag":
#	elif resource.realm = "attachment": 
	else:
		return
	for row in cursor:
		self.env.log.debug(row[0])
#		self.env.log.debug(type(row[0]))
		foo = str(row[0])
		for part in foo.split(" "):
			yield part

    def get_tags(self, resource):
        """Get tags for resource."""
        return set(self.get_tags_res(resource))
