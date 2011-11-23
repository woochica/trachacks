from trac.config import Option, BoolOption, ExtensionOption
from trac.core import *
from trac.perm import IPermissionGroupProvider
from trac.web.api import ITemplateStreamFilter
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider

from genshi.filters.transform import Transformer

from acct_mgr.api import IPasswordStore, IAccountChangeListener, del_user_attribute
from acct_mgr.pwhash import IPasswordHashMethod
from random import Random

import re

def generatePassword(passwordLength=10):
    rng = Random()
    righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
    lefthand = '789yuiophjknmYUIPHJKLNM'
    allchars = righthand + lefthand
    passwd=''
    for i in range(passwordLength):
        passwd+=rng.choice(allchars)
    return passwd


class SQLFlexibleAuthStore(Component):
    """
    This class implements SQL password store for Trac's AccountManager.
    """

    hash_method = ExtensionOption('account-manager', 'hash_method', IPasswordHashMethod, 'HtPasswdHashMethod')

    sql_read_only = BoolOption('account-manager', 'sql_read_only', True,
        """Is SQL table with authentication data read-only?""")
    sql_username_field = Option('account-manager','sql_username_field',"username",
        """Table field name which contains the username""")
    sql_groupname_field = Option('account-manager','sql_groupname_field',"groupname",
        """Table field name which contains the groupname""")
    sql_password_field = Option('account-manager','sql_password_field',"password",
        """Table field name which contains the password""")
    sql_all_users_query = Option('account-manager','sql_all_users_query',"SELECT DISTINCT $username_field$,$password_field$ FROM users",
        """SQL Query that selects all users from the database""")
    sql_group_membership_query = Option('account-manager','sql_group_membership_query',"SELECT DISTINCT $groupname_field$ FROM users,membership,groups WHERE membership.groupid=groups.groupid AND membership.userid=users.userid AND users.$username_field$='$username$'",
        """SQL Query that selects all groups of which username is a member""")
    sql_group_get_members_query = Option('account-manager','sql_group_get_members_query',"SELECT DISTINCT $username_field$ FROM users,membership,groups WHERE membership.groupid=groups.groupid AND membership.userid=users.userid AND groups.$groupname_field$='$groupname$'",
        """SQL Query that selects all users which are a member of groupname""")
    sql_update_password_query = Option('account-manager','sql_update_password_query',"UPDATE users SET $password_field$='$password$' WHERE $username_field$='$username$'",
        """SQL Query that updates the password for an existing user""")
    sql_create_user_query = Option('account-manager','sql_create_user_query',"INSERT INTO users ($username_field$,$password_field$) VALUES ('$username$','$password$')",
        """SQL Query that inserts a new user to the database""")
    sql_delete_user_query = Option('account-manager','sql_delete_user_query',"DELETE users.*,membership.* FROM users,membership WHERE membership.userid=users.userid AND users.$username_field$='$username$'",
        """SQL Query that deletes a user from the database""")
    sql_delete_group_query = Option('account-manager','sql_delete_group_query',"DELETE groups.*,membership.* FROM groups,membership WHERE membership.groupid=groups.groupid AND groups.$groupname_field$='$groupname$'",
        """SQL Query that deletes a group from the database""")
    sql_get_groups_query = Option('account-manager','sql_get_groups_query',"SELECT $groupname_field$ FROM groups",
        """SQL Query that retrieves all grous from the database""")
    sql_add_user_to_group_query = Option('account-manager','sql_add_user_to_group_query',"INSERT INTO membership SELECT DISTINCT userid,groupid FROM users,groups WHERE $username_field$='$username$' AND $groupname_field$='$groupname$'",
        """SQL Query that adds a user to a group""")
    sql_add_group_query = Option('account-manager','sql_add_group_query',"INSERT INTO groups ($groupname_field$) VALUES ('$groupname$')",
        """SQL Query that inserts a new group into the database""")
    sql_del_user_from_group_query = Option('account-manager','sql_del_user_from_group_query',"DELETE membership.* FROM groups,membership WHERE membership.groupid=groups.groupid AND groups.$groupname_field$='$groupname$'",
        """SQL Query that deletes a user from a group in the database""")

    query_re = re.compile('\$([a-zA-Z0-9_]+)\$')
    query_replace = r'%(\1)s'

    implements(IPasswordStore,IAccountChangeListener , IPermissionGroupProvider, ITemplateStreamFilter,ITemplateProvider,IAdminPanelProvider)

    #helpers

    def create_query(self,query,args):
        return self.query_re.sub(self.query_replace,query)%args

    def check_prereqs(self):
        if not self.sql_all_users_query:
            self.log.debug("sqlflexibleauthstore: 'sql_all_users_query' configuration option is required")
            return False

        if not self.sql_update_password_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_update_password_query' configuration option is required when read_only is false")
            return False

        if not self.sql_create_user_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_create_user_query' configuration option is required when read_only is false")
            return False

        if not self.sql_delete_user_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_delete_user_query' configuration option is required when read_only is false")
            return False

        if not self.sql_delete_group_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_delete_group_query' configuration option is required when read_only is false")
            return False

        if not self.sql_add_user_to_group_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_add_user_to_group_query' configuration option is required when read_only is false")
            return False

        if not self.sql_add_group_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_add_group_query' configuration option is required when read_only is false")
            return False

        if not self.sql_del_user_from_group_query and not self.read_only:
            self.log.debug("sqlflexibleauthstore: 'sql_del_user_from_group_query' configuration option is required when read_only is false")
            return False

        if not self.sql_group_membership_query:
            self.log.debug("sqlflexibleauthstore: 'sql_group_membership_query' configuration option is required")
            return False

        if not self.sql_get_groups_query:
            self.log.debug("sqlflexibleauthstore: 'sql_get_groups_query' configuration option is required")
            return False

        if not self.sql_username_field:
            self.log.debug("sqlflexibleauthstore: 'sql_username_field' configuration option is required")
            return False

        if not self.sql_groupname_field:
            self.log.debug("sqlflexibleauthstore: 'sql_groupname_field' configuration option is required")
            return False

        if not self.sql_password_field:
            self.log.debug("sqlflexibleauthstore: 'sql_password_field' configuration option is required")
            return False
        return True

    # IPasswordStore methods
    def get_users(self):
        """
        Returns an iterable of the known usernames.
        """

        if not self.check_prereqs():
            raise StopIteration

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_all_users_query+" ORDER BY $username_field$",{'username_field':self.sql_username_field,'password_field':self.sql_password_field})
        self.log.debug("sqlflexibleauthstore: get_users: %s" % (query,))

        cursor.execute(query)
        desc=[i[0] for i in cursor.description]
        for row in cursor:
            self.log.debug('sqlflexibleauthstore: get_users: row %s'%str(row))
            dictrow=dict(zip(desc,row))
            yield dictrow[self.sql_username_field]

    def has_user(self, user):
        """
        Returns whether the user account exists.
        """

        if not self.check_prereqs():
            return False

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_all_users_query+" WHERE $username_field$='$username$'",{'username_field':self.sql_username_field,'password_field':self.sql_password_field,'username':user})
        self.log.debug("sqlflexibleauthstore: has_user: %s" % (query,))
        cursor.execute(query)

        for row in cursor:
            return True
        return False

    def set_password(self, user, password, create_user=True):
        """
        Sets the password for the user. This should create the user account
        if it doesn't already exist.

        Returns True if a new account was created, False if an existing account
        was updated.
        """

        if not self.check_prereqs():
            return False

        hash = self.hash_method.generate_hash(user,password)
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_update_password_query,{'username_field':self.sql_username_field,'password_field':self.sql_password_field,'username':user,'password':hash})
        self.log.debug("sqlflexibleauthstore: set_password: %s" % (query,))
        cursor.execute(query)

        if cursor.rowcount > 0:
            self.log.debug('sqlflexibleauthstore: set_password: an existing user was updated')
            db.commit()
            if create_user:
                '''only return False when a user was updated, and create_user is true, because a user was not created'''
                return False
            else:
                '''the user was succesfully updated and no user should be created'''
                return True
        elif not create_user:
            self.log.debug('sqlflexibleauthstore: set_password: user doesnt exist, and none should be created')
            '''no existing user was updated, an none should be created either'''
            return False
        query=self.create_query(self.sql_create_user_query,{'username_field':self.sql_username_field,'password_field':self.sql_password_field,'username':user,'password':hash})
        self.log.debug("sqlflexibleauthstore: set_password: %s" % (query,))
        cursor.execute(query)

        db.commit()
        return True

    def __getattribute__(self, name):
        if name == 'set_password':
            self.log.debug('%s requested, and sql_read_only is %s'%(name,self.sql_read_only))
            if self.sql_read_only:
                raise AttributeError
        return super(SQLFlexibleAuthStore, self).__getattribute__(name)

    def check_password(self, user, password):
        """
        Checks if the password is valid for the user.

        Returns True if the correct user and password are specfied. Returns
        False if the incorrect password was specified. Returns None if the
        user doesn't exist in this password store.

        Note: Returing `False` is an active rejection of the login attempt.
        Return None to let the auth fall through to the next store in the
        chain.
        """

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if not self.check_prereqs():
            return None

        query=self.create_query(self.sql_all_users_query+" WHERE %(username_field)s='%(username)s'",{'password_field':self.sql_password_field,'username_field':self.sql_username_field,'username':user})
        self.log.debug("sqlflexibleauthstore: check_password: %s" % (query,))
        cursor.execute(query)

        desc=[i[0] for i in cursor.description]
        for row in cursor:
            self.log.debug("sqlflexibleauthstore: check_password: retrieved hash from the database")
            dictrow=dict(zip(desc,row))
            hash=dictrow[self.sql_password_field]
            return self.hash_method.check_hash(user,password, hash)
        return None

    def delete_user(self, user):
        """
        Deletes the user account.

        Returns True if the account existed and was deleted, False otherwise.
        """

        if self.sql_read_only:
            return False

        if not self.check_prereqs():
            return False

        if not self.has_user(user):
            return False

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_delete_user_query,{'username_field':self.sql_username_field,'username':user})
        self.log.debug("sqlflexibleauthstore: delete_user: %s" % (query,))
        cursor.execute(query)

        db.commit()
        del_user_attribute(self.env,username=user)
        return True

    #IAccountChangeListener methods

    def user_created(self, user, password):
        """
        Create a New user
        """

        if not self.check_prereqs():
            return False

        if self.has_user(user):
            return False

        hash = self.hash_method.generate_hash(user,password)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        res=self.set_password(user,password,create_user=True)
        self.log.debug("sqlflexibleauthstore: user_created: %s, %s" % (user,res))
        return res

    def user_password_changed(self, user, password):
        """Password changed
        """
        self.log.debug("sqlflexibleauthstore: user_password_changed")
        return self.set_password(user,password,create_user=True)

    def user_deleted(self, user):
        """User deleted
        """
        self.log.debug("sqlflexibleauthstore: user_deleted")
        return self.delete_user(user)
#
#    def user_password_reset(self, user, email, password):
#        """User password reset
#        """
#        self.log.info("sqlflexibleauthstore: user_password_reset")

#    def user_email_verification_requested(self, user, token):
#        """User verification requested
#        """
#        self.log.error("sqlflexibleauthstore: user_email_verification_requested: not implemented yet")
#        raise NotImplementedError

    # IPermissionGroupProvider methods

    def get_permission_groups(self, username):
        """
        Returns a list of names of the groups that the user with the specified
        name is a member of.
        """

        if not self.check_prereqs():
            return []
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_group_membership_query,{'username_field':self.sql_username_field,'username':username,'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: get_permission_groups: %s" % (query,))
        cursor.execute(query)
        groups=[]
        desc=[i[0] for i in cursor.description]
        for row in cursor:
            self.log.debug("sqlflexibleauthstore: get_permission_groups: retrieved groupname from the database")
            dictrow=dict(zip(desc,row))
            groups.append(dictrow[self.sql_groupname_field])
        return groups

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        """
        Returns changed stream for `admin_users.html` template to change how
        account deletion is described if SQL table is read-only.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.
        """
        if self.sql_read_only and filename == 'admin_users.html':
            stream |= Transformer(".//input[@name='remove']").attr('value', 'Remove session and permissions data for selected accounts')
        return stream

    # IAdminPanelProvider

    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('accounts', 'Accounts', 'groups', 'Groups')

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('TRAC_ADMIN')
        if cat == 'accounts' and page == 'groups':
            return self._do_group(req)

    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    #group methods
    def has_group(self,groupname):
        """
        Returns True if groupname exists.
        """

        if not self.check_prereqs():
            return False

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_get_groups_query+" WHERE $groupname_field$='$groupname$'",{'groupname':groupname,'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: has_group: %s" % (query,))

        cursor.execute(query)
        for row in cursor:
            return True
        return False

    def get_groups(self):
        """
        Returns an iterable of the known groupnames.
        """

        if not self.check_prereqs():
            raise StopIteration

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_get_groups_query+" ORDER BY $groupname_field$",{'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: get_groups: %s" % (query,))

        cursor.execute(query)
        desc=[i[0] for i in cursor.description]
        for row in cursor:
            dictrow=dict(zip(desc,row))
            yield dictrow[self.sql_groupname_field]

    def group_get_members(self,groupname):
        """
        Returns an iterable of all the members of a group.
        """

        if not self.check_prereqs():
            raise StopIteration

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_group_get_members_query+" ORDER BY $username_field$",{'groupname':groupname,'username_field':self.sql_username_field,'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: group_get_members: %s" % (query,))

        cursor.execute(query)
        desc=[i[0] for i in cursor.description]
        for row in cursor:
            dictrow=dict(zip(desc,row))
            yield dictrow[self.sql_username_field]

    def add_user_to_group(self,username,groupname):
        """
        Returns True if a user was succesfully added to a group.
        """

        if not self.check_prereqs():
            raise StopIteration

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_add_user_to_group_query,{'username':username,'groupname':groupname,'username_field':self.sql_username_field,'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: add_user_to_group: %s" % (query,))

        cursor.execute(query)
        if cursor.rowcount > 0:
            db.commit()
            return True
        return False

    def add_group(self,groupname):
        """
        Returns True if a group was added.
        """

        if not self.check_prereqs():
            raise StopIteration

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_add_group_query,{'groupname':groupname,'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: add_group: %s" % (query,))

        cursor.execute(query)
        if cursor.rowcount > 0:
            db.commit()
            return True
        return False

    def del_user_from_group(self,username,groupname):
        """
        Returns True if the user was successfully removed from a group.
        """

        if not self.check_prereqs():
            raise StopIteration

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        query=self.create_query(self.sql_del_user_from_group_query,{'username':username,'groupname':groupname,'username_field':self.sql_username_field,'groupname_field':self.sql_groupname_field})
        self.log.debug("sqlflexibleauthstore: del_user_from_group: %s" % (query,))

        cursor.execute(query)
        db.commit()
        return True

    def _do_group(self, req):
        """Provide a list of groups, a current group name and a list
        of users in the current group.
        """
        # process forms/commands
        message=''
        args={}
        if req.method == 'POST':
            group = req.args.get('group')
            user = req.args.get('user')
            if req.args.get('add'):
                if group and not self.has_group(group):
                    self.add_group(group)
                    message+=u'added group %s\n'%group
                if user and not group in self.get_permission_groups(user):
                    self.add_user_to_group(user,group)
                    message+=u'added %s to %s' % (user, group)
                args['message'] = message
            elif req.args.get('remove') and req.args.get('group'):
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                for user in sel:
                    self.del_user_from_group(user,group)
                    args['message'] = u'removed %s from %s' % (sel, req.args.get('group'))
        # lists and other info
        all_groups = sorted(self.get_groups())
        args['groups'] = all_groups
        if req.args.get('group') and self.has_group(req.args.get('group')):
            group_name=req.args.get('group')
        elif len(all_groups) > 0:
            group_name=all_groups[0]
        else:
            group_name = None
        if group_name:
            args['group'] = group_name
            args['members'] = sorted(self.group_get_members(group_name))
            args['listing_enabled'] = True
        args['selection_enabled'] = len(all_groups)>0
        return 'sqlflexibleauthstore_group_editor.html', args
