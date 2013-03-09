# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Malcolm Studd <mestudd@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.builder import tag
from genshi.filters.transform import StreamBuffer, Transformer
from genshi.template.markup import MarkupTemplate

from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket import Version
from trac.util.datefmt import to_timestamp
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import INavigationContributor
from trac.wiki.formatter import wiki_to_oneliner


class MilestoneVersion(Component):
    """Add a 'Version' attribute to milestones.
    """

    implements(INavigationContributor, IRequestFilter, ITemplateStreamFilter)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'versions'

    def get_navigation_items(self, req):
        return []


    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        action = req.args.get('action', 'view')
        if req.path_info.startswith('/milestone') \
            and req.method == 'POST' \
            and action == 'edit' or action == 'delete':

            old_name = req.args.get('id')
            new_name = req.args.get('name')
            db = self.env.get_db_cnx()

            if old_name and old_name != new_name:
                self._delete_milestone_version(db, old_name)
            if new_name:
                self._delete_milestone_version(db, new_name)
                version_id = req.args.get('version')
                if version_id and action == 'edit':
                    self._insert_milestone_version(db, new_name, version_id)

            db.commit() # is called when milestone save succeeds

        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        # Allow setting version for milestone
        if filename == 'milestone_edit.html':
            filter = Transformer('//fieldset[1]')
            return stream | filter.before(self._version_edit(data))

        # Display version for milestone
        elif filename == 'milestone_view.html':
            milestone = data.get('milestone').name
            filter = Transformer('//div[@class="info"]/p[@class="date"]')
            return stream | filter.append(self._version_display(req, milestone))
        elif filename == 'roadmap.html':
            return self._milestone_versions(stream, req)

        return stream

    # internal methods

    def _delete_milestone_version(self, db, milestone):
        cursor = db.cursor()
        cursor.execute("DELETE FROM milestone_version WHERE milestone=%s", (milestone,))

    def _insert_milestone_version(self, db, milestone, version):
        cursor = db.cursor()
        cursor.execute("INSERT INTO milestone_version "
                       "(milestone, version) VALUES (%s, %s)",
                       (milestone, version))

    def _milestone_versions(self, stream, req):
        buffer = StreamBuffer()

        def apply_version():
            return self._version_display(req, buffer.events[1][1])

        filter = Transformer('//li[@class="milestone"]/div/h2/a/em').copy(buffer).end() \
            .select('//li[@class="milestone"]//p[@class="date"]').append(apply_version)
        return stream | filter

    def _version_display(self, req, milestone):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT version FROM milestone_version WHERE milestone=%s", (milestone,))
        row = cursor.fetchone()

        if row:
            return tag.span(
                "; ",
                wiki_to_oneliner("For version:'%s'" % (row[0],), self.env, req=req),
                class_="date")
        else:
            return []

    def _version_edit(self, data):
        milestone = data.get('milestone').name
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT version FROM milestone_version WHERE milestone=%s", (milestone,))
        row = cursor.fetchone()
        value = row and row[0]

        cursor.execute("SELECT name FROM version WHERE time IS NULL OR time = 0 OR time>%s "
                       "OR name = %s ORDER BY name",
                       (to_timestamp(None), value))

        return tag.div(
            tag.label(
                'Version:',
                tag.br(),
                tag.select(
                    tag.option(),
                    [tag.option(row[0], selected=(value == row[0] or None)) for row in cursor],
                    name="version")),
            class_="field")

