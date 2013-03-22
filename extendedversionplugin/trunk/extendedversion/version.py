# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Malcolm Studd <mestudd@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from datetime import date
from pkg_resources import parse_version

from genshi.builder import tag
from trac import __version__ as trac_version
from trac.attachment import AttachmentModule, ILegacyAttachmentPolicyDelegate
from trac.config import BoolOption, ExtensionOption, Option
from trac.core import *
from trac.mimeview.api import Context
from trac.perm import IPermissionRequestor
from trac.resource import IResourceManager, Resource, ResourceNotFound
from trac.ticket import Milestone, Version
from trac.ticket.query import QueryModule
from trac.ticket.roadmap import (
    ITicketGroupStatsProvider, apply_ticket_permissions,
    get_tickets_for_milestone, get_ticket_stats
)
from trac.util.datefmt import get_datetime_format_hint, parse_date
from trac.util.translation import _
from trac.web.chrome import (
    Chrome, INavigationContributor, IRequestHandler, ITemplateProvider,
    add_ctxtnav, add_notice, add_script, add_stylesheet, add_warning
)
from trac.wiki import IWikiSyntaxProvider


def milestone_stats_data(env, req, stat, name, grouped_by='component',
                         group=None):
    has_query = env[QueryModule] is not None

    def query_href(extra_args):
        if not has_query:
            return None
        args = {'milestone': name, grouped_by: group, 'group': 'status'}
        args.update(extra_args)
        return req.href.query(args)

    return {'stats': stat,
            'stats_href': query_href(stat.qry_args),
            'interval_hrefs': [query_href(interval['qry_args'])
                               for interval in stat.intervals]}


def version_interval_hrefs(env, req, stat, milestones):
    has_query = env[QueryModule] is not None

    def query_href(extra_args):
        if not has_query:
            return None
        args = {'milestone': milestones, 'group': 'milestone'}
        args.update(extra_args)
        return req.href.query(args)

    return [query_href(interval['qry_args']) for interval in stat.intervals]


# TODO: rename this to VersionModule, but beware that on upgrade, if the user
# hasn't used a wilcard to specify the components to be enabled, they will
# need to modify the components section of trac.ini:
#   extendedversion.version.visibleversion = enabled ->
#   extendedversion.version.versionmodule = enabled

class VisibleVersion(Component):
    implements(ILegacyAttachmentPolicyDelegate, INavigationContributor,
               IPermissionRequestor, IRequestHandler, IResourceManager,
               ITemplateProvider, IWikiSyntaxProvider)

    navigation_item = Option('extended_version', 'navigation_item', 'roadmap',
        """The main navigation item to highlight when displaying versions.""")

    show_milestone_description = BoolOption('extended_version',
        'show_milestone_description', False,
        """whether to display milestone descriptions on version page.""")

    version_stats_provider = ExtensionOption('extended_version', 'version_stats_provider',
        ITicketGroupStatsProvider, 'DefaultTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`,
           which is used to collect statistics on all version tickets.""")

    milestone_stats_provider = ExtensionOption('extended_version',
        'milestone_stats_provider', ITicketGroupStatsProvider,
        'DefaultTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`,
           which is used to collect statistics on per milestone tickets in
           the version view.""")

    # ILegacyAttachmentPolicyDelegate methods

    def check_attachment_permission(self, action, username, resource, perm):
        if resource.parent.realm != 'version':
            return

        if action == 'ATTACHMENT_CREATE':
            action = 'VERSION_MODIFY'
        elif action == 'ATTACHMENT_VIEW':
            action = 'VERSION_VIEW'
        elif action == 'ATTACHMENT_DELETE':
            action = 'VERSION_DELETE'

        decision = action in perm(resource.parent)
        if not decision:
            self.env.log.debug('ExtendedVersionTracPlugin denied %s '
                               'access to %s. User needs %s' %
                               (username, resource, action))
        return decision


    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'versions'

    def get_navigation_items(self, req):
        return []


    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['VERSION_CREATE', 'VERSION_DELETE', 'VERSION_MODIFY',
                   'VERSION_VIEW']
        return actions + [('VERSION_ADMIN', actions)]


    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/version[/^s]?(?:(.+))?', req.path_info)
        if match:
            if match.group(1):
                req.args['id'] = match.group(1)
            return True

    def process_request(self, req):
        version_id = req.args.get('id')
        req.perm('version', version_id).require('VERSION_VIEW')

        db = self.env.get_db_cnx()
        version = Version(self.env, version_id, db)
        action = req.args.get('action', 'view')

        if req.method == 'POST':
            if req.args.has_key('cancel'):
                if version.exists:
                    req.redirect(req.href.version(version.name))
                else:
                    req.redirect(req.href.versions())
            elif action == 'edit':
                return self._do_save(req, db, version)
            elif action == 'delete':
                self._do_delete(req, db, version)
        elif action in ('new', 'edit'):
            return self._render_editor(req, db, version)
        elif action == 'delete':
            return self._render_confirm(req, db, version)

        if not version.name:
            req.redirect(req.href.versions())

        add_stylesheet(req, 'common/css/roadmap.css')
        return self._render_view(req, db, version)


    # IResourceManager methods

    # TODO: not sure this is implemented right just yet,
    # and do we need to implement get_resource_url?

    def get_resource_realms(self):
        yield 'version'

    def get_resource_description(self, resource, format=None, context=None,
                                 **kwargs):
        desc = resource.id
        if format != 'compact':
            desc = _('Version %(name)s', name=resource.id)
        if context:
            return tag.a('Version %(name)s', name=resource.id,
                         href=context.href.version(resource.id))
        else:
            return desc

    def resource_exists(self, resource):
        try:
            Version(self.env, resource.id)
            return Version.exists
        except ResourceNotFound:
            return False


    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('extendedversion', resource_filename('extendedversion', 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('extendedversion', 'templates')]


    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('version', self._format_link)

    # Internal methods

    def _do_delete(self, req, db, version):
        name = version.name
        resource = Resource('version', version.name)
        req.perm(resource).require('VERSION_DELETE')

        cursor = db.cursor()
        cursor.execute("DELETE FROM milestone_version WHERE version=%s",
                       (version.name,))
        version.delete(db=db)
        db.commit()
        add_notice(req, _('The version "%(name)s" has been deleted.',
                          name=name))
        req.redirect(req.href.versions())

    def _do_save(self, req, db, version):
        resource = Resource('version', version.name)
        if version.exists:
            req.perm(resource).require('VERSION_MODIFY')
        else:
            req.perm(resource).require('VERSION_CREATE')

        old_name = version.name
        new_name = req.args.get('name')

        version.name = new_name
        version.description = req.args.get('description', '')

        time = req.args.get('time', '')

        # Instead of raising one single error, check all the constraints and
        # let the user fix them by going back to edit mode showing the warnings
        warnings = []

        def warn(msg):
            add_warning(req, msg)
            warnings.append(msg)

        # -- check the name
        if new_name:
            if new_name != old_name:
                # check that the version doesn't already exists
                # FIXME: the whole .exists business needs to be clarified
                #        (#4130) and should behave like a WikiPage does in
                #        this respect.
                try:
                    other_version = Version(self.env, new_name, db)
                    warn(_('Version "%(name)s" already exists, please '
                           'choose another name', name=new_name))
                except ResourceNotFound:
                    pass
        else:
            warn(_('You must provide a name for the version.'))

        # -- check completed date
        if 'time' in req.args:
            time = time and parse_date(time, req.tz) or None
        else:
            time = None
        version.time = time

        if warnings:
            return self._render_editor(req, db, version)

        # -- actually save changes
        if version.exists:
            if version.name != version._old_name:
                # Update tickets
                cursor = db.cursor()
                cursor.execute("UPDATE milestone_version SET version=%s WHERE version=%s",
                               (version.name, version._old_name))
            version.update(db)
        else:
            version.insert(db)
        db.commit()

        req.redirect(req.href.version(version.name))

    def _format_link(self, formatter, ns, name, label):
        name, query, fragment = formatter.split_link(name)
        return self._render_link(formatter.context, name, label,
                                 query + fragment)

    def _render_confirm(self, req, db, version):
        resource = Resource('version', version.name)
        req.perm(resource).require('VERSION_DELETE')

        data = {
            'version': version,
        }

        add_stylesheet(req, 'common/css/roadmap.css')
        return 'version_delete.html', data, None

    def _render_editor(self, req, db, version):
        resource = Resource('version', version.name)
        data = {
            'version': version,
            'resource': resource,
            'versions': [ver.name for ver in Version.select(self.env)],
            'datetime_hint': get_datetime_format_hint(),
            'version_groups': [],
        }

        if version.exists:
            req.perm(resource).require('VERSION_MODIFY')
            #versions = [m for m in Version.select(self.env, db=db)
            #              if m.name != version.name
            #              and 'VERSION_VIEW' in req.perm(m.resource)]
        else:
            req.perm(resource).require('VERSION_CREATE')

        if parse_version(trac_version) >= parse_version('1.0'):
            Chrome(self.env).add_jquery_ui(req)
        Chrome(self.env).add_wiki_toolbars(req)
        return 'version_edit.html', data, None

    def _render_link(self, context, name, label, extra=''):
        try:
            version = Version(self.env, name)
        except TracError:
            version = None
        # Note: the above should really not be needed, `Milestone.exists`
        # should simply be false if the milestone doesn't exist in the db
        # (related to #4130)
        href = context.href.version(name)
        if version and version.exists:
            resource = Resource('version', name)
            if 'VERSION_VIEW' in context.perm(resource):
                return tag.a(label, class_='version', href=href + extra)
        elif 'VERSION_CREATE' in context.perm('version', name):
            return tag.a(label, class_='missing version', href=href + extra,
                         rel='nofollow')
        return tag.a(label, class_='missing version')

    def _render_view(self, req, db, version):

        db = self.env.get_db_cnx()
        sql = "SELECT name FROM milestone " \
              "INNER JOIN milestone_version ON (name = milestone) " \
              "WHERE version = %s " \
              "ORDER BY due"
        cursor = db.cursor()
        cursor.execute(sql, (version.name,))

        milestones = []
        tickets = []
        milestone_stats = []

        for row in cursor:
            milestone = Milestone(self.env, row[0])
            milestones.append(milestone)

            mtickets = get_tickets_for_milestone(self.env, db, milestone.name,
                                                 'owner')
            mtickets = apply_ticket_permissions(self.env, req, mtickets)
            tickets += mtickets
            stat = get_ticket_stats(self.milestone_stats_provider, mtickets)
            milestone_stats.append(milestone_stats_data(self.env, req, stat, milestone.name))

        stats = get_ticket_stats(self.version_stats_provider, tickets)
        interval_hrefs = version_interval_hrefs(self.env, req, stats,
                                                [milestone.name for milestone in milestones])

        version.resource = Resource('version', version.name)
        context = Context.from_request(req, version.resource)

        version.is_released = version.time and version.time.date() < date.today()
        version.stats = stats
        version.interval_hrefs = interval_hrefs
        version.stats_href = [] # Not implemented yet, see th:#10349
        data = {
            'context': context,
            'version': version,
            'attachments': AttachmentModule(self.env).attachment_data(context),
            'milestones': milestones,
            'milestone_stats': milestone_stats,
            'show_milestone_description': self.show_milestone_description # Not implemented yet
        }

        add_stylesheet(req, 'extendedversion/css/version.css')
        add_script(req, 'common/js/folding.js')
        add_ctxtnav(req, _("Back to Versions"), req.href.versions())
        return 'version_view.html', data, None

