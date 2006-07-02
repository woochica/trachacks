from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner
from webadmin.web_ui import IAdminPageProvider
import time

class DiscussionWebAdmin(Component):
    """
        The webadmin module implements discussion plugin administration
        via WebAdminPlugin.
    """
    implements(IAdminPageProvider)

    # IAdminPageProvider
    def get_admin_pages(self, req):
        if req.perm.has_permission('DISCUSSION_MODIFY'):
            yield ('discussion', 'Discussion System', 'group', 'Forum Groups')
            yield ('discussion', 'Discussion System', 'forum', 'Forums')

    def process_admin_request(self, req, category, page, path_info):
        # Check permission
        req.perm.assert_permission('DISCUSSION_MODIFY')

        # Get access to database
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # CSS styles
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'discussion/css/admin.css')

        # Get action
        action = req.args.get('discussion_action')

        # Determine mode
        if page == 'group':
            if action == 'post-add':
                mode = 'group-post-add'
            elif action == 'delete':
                mode = 'group-delete'
            else:
                mode = 'group-admin'
        elif page == 'forum':
            if action == 'post-add':
                mode = 'forum-post-add'
            elif action == 'delete':
                mode = 'forum-delete'
            elif action == 'change-group':
                mode = 'forum-change-group'
            else:
                mode = 'forum-admin'

        # Perform mode action
        if mode == 'group-admin':
            # Display group list
            req.hdf['discussion.groups'] = self._get_groups(cursor)
        elif mode == 'group-post-add':
            # Get form values
            name = req.args.get('name')
            description = req.args.get('description')

            # Add new group
            self._add_group(cursor, name, description)

            # Display group list
            req.hdf['discussion.groups'] = self._get_groups(cursor)
            mode = 'group-admin'
        elif mode == 'group-delete':
            # Get form values
            selection = req.args.get('selection')
            if isinstance(selection, (str, unicode)):
                selection = [selection]

            # Delete selected groups
            self._delete_groups(cursor, selection)

            # Display group list
            req.hdf['discussion.groups'] = self._get_groups(cursor)
            mode = 'group-admin'
        elif mode == 'forum-admin':
            # Display forum list
            req.hdf['discussion.forums'] = self._get_forums(cursor)
            req.hdf['discussion.groups'] = self._get_groups(cursor)
        elif mode == 'forum-post-add':
            # Get form values
            name = req.args.get('name')
            author = req.authname
            subject = req.args.get('subject')
            description = req.args.get('description')
            moderators = req.args.get('moderators')
            if moderators:
                moderators = moderators.split(' ')
            else:
                moderators = ''

            # Add new forum
            self._add_forum(cursor, name, author, subject, description, moderators)

            # Display forum list
            req.hdf['discussion.forums'] = self._get_forums(cursor)
            req.hdf['discussion.groups'] = self._get_groups(cursor)
            mode = 'forum-admin'
        elif mode == 'forum-delete':
            # Get form values
            selection = req.args.get('selection')
            if isinstance(selection, (str, unicode)):
                selection = [selection]

            # Delete selected forums
            self._delete_forums(cursor, selection)

            # Display forum list
            req.hdf['discussion.forums'] = self._get_forums(cursor)
            req.hdf['discussion.groups'] = self._get_groups(cursor)
            mode = 'forum-admin'
        elif mode == 'forum-change-group':
            # Get form values
            forum = req.args.get('forum')
            group = req.args.get('group')

            # Set new group
            self._set_group(cursor, forum, group)

            # Display forum list
            req.hdf['discussion.forums'] = self._get_forums(cursor)
            req.hdf['discussion.groups'] = self._get_groups(cursor)
            mode = 'forum-admin'

        # Fill template values and return mode template
        req.hdf['discussion.href'] = self.env.href.admin(category, page)
        req.hdf['discussion.users'] = self._get_users()
        db.commit()
        return mode + '.cs', None

    def _get_groups(self, cursor):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM forum_group"
        self.log.debug(sql)
        cursor.execute(sql)
        groups = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['name'] = wiki_to_oneliner(row['name'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            groups.append(row)
        return groups

    def _get_forums(self, cursor):
        columns = ('id', 'name', 'author', 'moderators', 'group', 'subject',
          'description')
        sql = "SELECT id, name, author, moderators, forum_group, subject," \
          " description FROM forum"
        self.log.debug(sql)
        cursor.execute(sql)
        forums = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['name'] = wiki_to_oneliner(row['name'], self.env)
            row['subject'] = wiki_to_oneliner(row['subject'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            row['moderators'] = wiki_to_oneliner(row['moderators'], self.env)
            forums.append(row)
        return forums

    def _get_users(self):
        users = []
        for user in self.env.get_known_users():
            users.append(user[0])
        return users

    def _add_group(self, cursor, name, description):
        sql = "INSERT INTO forum_group (name, description) VALUES ('%s', '%s')" \
          % (name, description)
        self.log.debug(sql)
        cursor.execute(sql)

    def _add_forum(self, cursor, name, author, subject, description, moderators):
        moderators = ' '.join(moderators)
        sql = "INSERT INTO forum (name, author, time, moderators, subject," \
          " description) VALUES ('%s', '%s', %s, '%s', '%s', '%s')" % (name,
          author, str(int(time.time())), moderators, subject, description)
        self.log.debug(sql)
        cursor.execute(sql)

    def _delete_groups(self, cursor, groups):
        if groups:
            groups = ', '.join(groups)
            sql = "DELETE FROM forum_group WHERE id IN (%s)" % (groups)
            self.log.debug(sql)
            cursor.execute(sql)
            sql = "UPDATE forum SET forum_group = NULL WHERE forum_group IN" \
              " (%s)" % (groups)
            cursor.execute(sql)

    def _delete_forums(self, cursor, forums):
        if forums:
            forums = ', '.join(forums)
            sql = "DELETE FROM message WHERE forum IN (%s)" % (forums)
            self.log.debug(sql)
            cursor.execute(sql)
            sql = "DELETE FROM topic WHERE forum IN (%s)" % (forums)
            self.log.debug(sql)
            cursor.execute(sql)
            sql = "DELETE FROM forum WHERE id IN (%s)" % (forums)
            self.log.debug(sql)
            cursor.execute(sql)

    def _set_group(self, cursor, forum, group):
        if not group:
            group = 'NULL'
        sql = "UPDATE forum SET forum_group = %s WHERE id = %s" % (group, forum)
        self.log.debug(sql)
        cursor.execute(sql)
