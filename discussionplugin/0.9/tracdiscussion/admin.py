from tracdiscussion.api import *
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
        submit = req.args.has_key('submit');
        cancel = req.args.has_key('cancel');

        # Determine mode
        if page == 'group':
            if action == 'post-add':
                mode = 'group-post-add'
            elif action == 'post-edit':
                if submit:
                    mode = 'group-post-edit'
                else:
                    mode = 'group-admin'
            elif action == 'delete':
                mode = 'group-delete'
            else:
                mode = 'group-admin'
        elif page == 'forum':
            if action == 'post-add':
                mode = 'forum-post-add'
            elif action == 'post-edit':
                if submit:
                    mode = 'forum-post-edit'
                else:
                    mode = 'forum-admin'
            elif action == 'delete':
                mode = 'forum-delete'
            else:
                mode = 'forum-admin'

        # Perform mode action
        if mode == 'group-admin':
            # Get selected group
            if path_info:
                req.hdf['discussion.group'] = get_group(cursor, self.env, req,
                  self.log, path_info)

            # Display group list
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
        elif mode == 'group-post-add':
            # Get form values
            name = req.args.get('name')
            description = req.args.get('description')

            # Add new group
            add_group(cursor, self.log, name, description)

            # Display group list
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            mode = 'group-admin'
        elif mode == 'group-post-edit':
            # Get form values
            group = req.args.get('group')
            name = req.args.get('name')
            description = req.args.get('description')

            # Add new group
            edit_group(cursor, self.log, group, name, description)

            # Display group list
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            mode = 'group-admin'
        elif mode == 'group-delete':
            # Get form values
            selection = req.args.get('selection')
            if isinstance(selection, (str, unicode)):
                selection = [selection]

            # Delete selected groups
            if selection:
                for group in selection:
                    delete_group(cursor, self.log, group)

            # Display group list
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            mode = 'group-admin'
        elif mode == 'forum-admin':
            # Get selected group
            if path_info:
                req.hdf['discussion.forum'] = get_forum(cursor, self.env, req,
                  self.log, path_info)

            # Display forum list
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
        elif mode == 'forum-post-add':
            # Get form values
            name = req.args.get('name')
            author = req.authname
            subject = req.args.get('subject')
            description = req.args.get('description')
            moderators = req.args.get('moderators')
            group = req.args.get('group')

            if not moderators:
                moderators = []
            if not isinstance(moderators, list):
                moderators = [moderators]

            # Add new forum
            add_forum(cursor, self.log, name, author, subject, description,
              moderators, group)

            # Display forum list
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            mode = 'forum-admin'
        elif mode == 'forum-post-edit':
            # Get form values
            forum = req.args.get('forum')
            name = req.args.get('name')
            subject = req.args.get('subject')
            description = req.args.get('description')
            moderators = req.args.get('moderators')
            group = req.args.get('group')

            if not moderators:
                moderators = []
            if not isinstance(moderators, list):
                moderators = [moderators]

            # Add new forum
            edit_forum(cursor, self.log, forum, name, subject, description, moderators, group)

            # Display forum list
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            mode = 'forum-admin'
        elif mode == 'forum-delete':
            # Get form values
            selection = req.args.get('selection')
            if isinstance(selection, (str, unicode)):
                selection = [selection]

            # Delete selected forums
            if selection:
                for forum in selection:
                    delete_forum(cursor, self.log, forum)

            # Display forum list
            req.hdf['discussion.forums'] = get_forums(cursor, self.env, req,
              self.log)
            req.hdf['discussion.groups'] = get_groups(cursor, self.env, req,
              self.log)
            mode = 'forum-admin'

        # Fill template values and return mode template
        req.hdf['discussion.href'] = self.env.href.admin(category, page)
        req.hdf['discussion.users'] = get_users(self.env, self.log)
        db.commit()
        return mode + '.cs', None
