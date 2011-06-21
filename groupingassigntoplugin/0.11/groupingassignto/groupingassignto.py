from trac.core import *
from trac.util.compat import sorted
from trac.config import Option
from flexibleassignto import IValidOwnerProvider, SimpleUser, getlist

class GroupingAssignTo(Component):
    implements(IValidOwnerProvider)
 
    owner_group = None

    def __init__(self):
        config = self.config.get('groupingassignto', 'owner_group', '')
        if config:
            self.owner_group = [x.strip() for x in config.split('|')]

    def getUsers(self, next_action):
        allowed_group = getlist(next_action, 'owner_group', sep='|')
        if not allowed_group:
            allowed_group = self.owner_group
        users_dict = {}
        for name in self._get_users(allowed_group):
            u = GroupedSimpleUser()
            u.setUsername(name)
            u.setOptionValue(name)
            u.setOptionDisplay(name)
            users_dict.update({name:u})
        return sorted(users_dict.values())

    def _query_groups(self, groups, seen):
        query = 'select username from permission'
        if groups:
            query += ' where action in ('
            query += ','.join(["'%s'" % x for x in groups])
            query += ')'
        result = {}
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(query)
        for name, in cursor:
            if name in seen:
                continue
            if name.islower() or groups:
                result.update({name:1})
        return result.keys()

    def _get_users(self, groups):
        seen = {}
        result = {}
        limit = 5
        while True:
            if limit < 1:
                break
            limit = limit - 1
            nextgroups = {}
            for name in self._query_groups(groups, seen):
                if name.islower():
                    result.update({name:1})
                    continue
                nextgroups.update({name:1})
            if groups:
                for group in groups:
                    seen.update({group:1})
            if not nextgroups:
                break
            groups = nextgroups.keys()
        return result.keys()

class GroupedSimpleUser(SimpleUser):
    def __cmp__(self, other):
        return cmp(self.username, other.username)

    def __repr__(self):
        return "<GroupedSimpleUser instance - %s>" % self.username

