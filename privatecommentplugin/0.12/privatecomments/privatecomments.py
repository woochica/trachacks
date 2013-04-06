# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.config import Option
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionSystem, IPermissionRequestor
from trac.ticket.web_ui import TicketModule
from trac.util.translation import _
from trac.web.api import ITemplateStreamFilter, IRequestFilter

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from genshi.input import HTML


class PrivateComments(Component):
    implements(IEnvironmentSetupParticipant, IPermissionRequestor,
               IRequestFilter, ITemplateStreamFilter)

    private_comment_permission = Option(
        'privatecomments',
        'permission',
        default='PRIVATE_COMMENT_PERMISSION',
        doc='The name of the permission which allows to see private comments')

    css_class_checkbox = Option(
        'privatecomments',
        'css_class_checkbox',
        default='private_comment_checkbox',
        doc='The name of the css class for the label of the checkbox')

    css_class_private_comment_marker = Option(
        'privatecomments',
        'css_class_private_comment_marker',
        default='private_comment_marker',
        doc='The name of the css class for the \"this is a private comment\" -label')

    # IPermissionRequestor methods
    def get_permission_actions(self):
        group_actions = [self.private_comment_permission]
        return group_actions

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if not isinstance(handler, TicketModule) or req.method != 'POST':
            return handler

        ticket_id = req.args.get('id')
        if not ticket_id:
            return handler

        if 'edited_comment' in req.args:
            editing = True
        elif 'comment' in req.args and req.args['comment']:
            editing = False
        else:
            return handler

        if 'cnum' in req.args:
            comment_id = req.args['cnum']
        elif 'cnum_edit' in req.args:
            comment_id = req.args['cnum_edit']
        else:
            return handler

        if 'private_comment' in req.args and \
           req.args['private_comment'] == 'on':
            private = 1
        else:
            private = 0

        if editing:
            sql = """
                UPDATE private_comment SET private=%s
                WHERE ticket_id=%s AND comment_id=%s
                """
            params = (int(private), int(ticket_id), int(comment_id))
        else:
            sql = """
                INSERT INTO private_comment(ticket_id, comment_id, private)
                  values(%s, %s, %s)"""
            params = (int(ticket_id), int(comment_id), int(private))

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql, params)
        db.commit()

        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        db = self.env.get_db_cnx()
        if self.environment_needs_upgrade(db):
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM private_comment")
            return False
        except:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("""
                CREATE TABLE private_comment(ticket_id integer,
                  comment_id integer, private tinyint)
                """)
            db.commit()
        except:
            pass

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename not in ('ticket.html', 'ticket.rss'):
            return stream

        ticket_id = req.args.get('id')
        if not ticket_id:
            return stream

        # determine the username of the current user
        user = req.authname

        # determine if the user has the permission to see private comments
        perms = PermissionSystem(self.env)
        has_private_permission = self.private_comment_permission in perms.get_user_permissions(user)

        # Remove private comments from Ticket Page
        if filename == 'ticket.html':
            buf = StreamBuffer()

            def check_comments():
                delimiter = '<div xmlns="http://www.w3.org/1999/xhtml" class="change" id="trac-change-'

                comment_stream = str(buf)
                # split the comment_stream to get single comments
                comments_raw = comment_stream.split(delimiter)
                comment_stream = ''

                for comment in comments_raw:
                    if comment is None or len(comment) < 1:
                        continue

                    # determine comment id
                    find = comment.find('">')
                    if find == -1:
                        continue
                    comment_id = comment[:find]

                    # concat the delimiter and the comment again
                    comment_code = delimiter + comment

                    # if the user has the permission to see the comment
                    # the comment_code will be appended to the comment_stream
                    comment_private = self._is_comment_private(ticket_id, comment_id)

                    if comment_private:
                        comment_code = comment_code.replace(
                            '<span class="threading">',
                            '<span class="threading"> <span class="%s">this comment is private</span>'
                            % str(self.css_class_private_comment_marker)
                        )

                    if has_private_permission or not comment_private:
                        comment_stream += comment_code

                return HTML(comment_stream)

            # filter all comments
            stream |= Transformer('//div[@class="change" and @id]') \
                .copy(buf).replace(check_comments)

            # if the user has the private comment permission the checkboxes to change the private value will be added
            if has_private_permission:
                input = tag.label(_("Private Comment:"),
                                  tag.input(type='checkbox',
                                            name='private_comment'))
                stream |= Transformer('//h2[@id="trac-add-comment"]').after(input)
                # Trac 1.0 and later:
                # stream |= Transformer('//div[@id="trac-add-comment"]//fieldset').prepend(input)

        # Remove private comments from ticket RSS feed
        if filename == 'ticket.rss':
            comments = self._get_all_private_comments(ticket_id)

            self.log.debug("Private Comments for Ticket %d: %s" % (ticket_id, comments))

            for comment_id in comments:
                stream |= Transformer('//item[%d]' % comment_id).remove()

        return stream

    # internal methods

    def _is_comment_private(self, ticket_id, comment_id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute("""
            SELECT private FROM private_comment
            WHERE ticket_id=%s AND comment_id=%s
            """, (int(ticket_id), int(comment_id.split('-')[0])))
        try:
            private = cursor.fetchone()[0]
        except:
            private = 0

        return private == 1

    def _get_all_private_comments(self, ticket_id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute("""
            SELECT comment_id FROM private_comment
            WHERE ticket_id=%s AND private=1
            """, int(ticket_id))

        comments = []
        for comment_id in cursor:
            comments += [comment_id]

        return comments
