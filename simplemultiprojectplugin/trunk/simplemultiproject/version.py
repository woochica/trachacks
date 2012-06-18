# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering
#

# smp
from simplemultiproject.model import *

#trac
from trac.attachment import AttachmentModule
from trac.config import ExtensionOption
from trac.core import *
from trac.util.text import to_unicode
from trac.ticket.model import Version, Ticket, TicketSystem
from trac.ticket.roadmap import apply_ticket_permissions, get_ticket_stats, ITicketGroupStatsProvider, DefaultTicketGroupStatsProvider
from trac.ticket.query import QueryModule
from trac.mimeview import Context
from trac.timeline.api import ITimelineEventProvider

from trac.util.translation import _, tag_
from trac.util.datefmt import parse_date, utc, to_utimestamp, \
                              get_datetime_format_hint, format_date, \
                              format_datetime, from_utimestamp

from trac.web.api import IRequestHandler, IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_link, add_notice, add_script, add_stylesheet, \
                            add_warning, Chrome, INavigationContributor

# genshi
from genshi.builder import tag
from genshi.filters.transform import Transformer

# python
from datetime import datetime, timedelta
from pkg_resources import resource_filename
from operator import itemgetter
import re

def get_tickets_for_any(env, db, any_name, any_value, field='component'):
    cursor = db.cursor()
    fields = TicketSystem(env).get_ticket_fields()
    if field in [f['name'] for f in fields if not f.get('custom')]:
        cursor.execute("SELECT id,status,%s FROM ticket WHERE %s='%s' ORDER BY %s" % (field, any_name, any_value, field))
    else:
        cursor.execute("SELECT id,status,value FROM ticket LEFT OUTER JOIN ticket_custom ON (id=ticket AND name=%s) WHERE %s='%s' ORDER BY value", (field, any_name, any_value))
    tickets = []
    for tkt_id, status, fieldval in cursor:
        tickets.append({'id': tkt_id, 'status': status, field: fieldval})
    return tickets

def any_stats_data(env, req, stat, any_name, any_value, grouped_by='component',
                         group=None):
    has_query = env[QueryModule] is not None
    def query_href(extra_args):
        if not has_query:
            return None
        args = {any_name: any_value, grouped_by: group, 'group': 'status'}
        args.update(extra_args)
        return req.href.query(args)
    return {'stats': stat,
            'stats_href': query_href(stat.qry_args),
            'interval_hrefs': [query_href(interval['qry_args'])
                               for interval in stat.intervals]}

class SmpVersionProject(Component):
    """Create Project dependent versions"""

    implements(IRequestHandler, IRequestFilter, ITemplateStreamFilter)
    
    stats_provider = ExtensionOption('roadmap', 'stats_provider',
                                     ITicketGroupStatsProvider,
                                     'DefaultTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`, 
        which is used to collect statistics on groups of tickets for display
        in the roadmap views.""")

    def __init__(self):
        self.__SmpModel = SmpModel(self.env)
        
    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/version(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['id'] = match.group(1)
            return True

    def process_request(self, req):
        version_id = req.args.get('id')
        version_project = req.args.get('project', '')

        db = self.env.get_db_cnx() # TODO: db can be removed
        action = req.args.get('action', 'view')
        try:
            version = Version(self.env, version_id, db)
        except:
            version = Version(self.env, None, db)
            version.name = version_id
            action = 'edit' # rather than 'new' so that it works for POST/save

        if req.method == 'POST':
            if req.args.has_key('cancel'):
                if version.exists:
                    req.redirect(req.href.version(version.name))
                else:
                    req.redirect(req.href.roadmap())
            elif action == 'edit':
                return self._do_save(req, db, version)
            elif action == 'delete':
                self._do_delete(req, version)
        elif action in ('new', 'edit'):
            return self._render_editor(req, db, version)
        elif action == 'delete':
            return self._render_confirm(req, db, version)

        if not version.name:
            req.redirect(req.href.roadmap())

        return self._render_view(req, db, version)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/roadmap'):
            hide            = smp_settings(req, 'roadmap', 'hide', None)
            filter_projects = smp_filter_settings(req, 'roadmap', 'projects')
            
            if hide:
                data['hide'] = hide
                
            if not hide or 'versions' not in hide:
                versions, version_stats = self._versions_and_stats(req, filter_projects)
                data['versions'] = versions
                data['version_stats'] = version_stats
            
            if hide and 'milestones' in hide:
                data['milestones'] = []
                data['milestone_stats'] = []
                
            return "roadmap_versions.html", data, content_type
            
        return template, data, content_type


    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        action = req.args.get('action', 'view')

        if filename == "version_edit.html":
            if action == 'new':
                filter = Transformer('//form[@id="edit"]/div[1]')
                return stream | filter.before(self.__new_project())
            elif action == 'edit':
                filter = Transformer('//form[@id="edit"]/div[1]')
                return stream | filter.before(self.__edit_project(data))

        return stream

    # Internal methods

    def __edit_project(self, data):
        version = data.get('version').name
        all_projects = self.__SmpModel.get_all_projects()
        id_project_version = self.__SmpModel.get_id_project_version(version)

        if id_project_version != None:
            id_project_selected = id_project_version[0]
        else:
            id_project_selected = None

        return tag.div(
                       tag.label(
                       'Project:',
                       tag.br(),
                       tag.select(
                       tag.option(),
                       [tag.option(row[1], selected=(id_project_selected == row[0] or None), value=row[0]) for row in sorted(all_projects, key=itemgetter(1))],
                       name="project")
                       ),
                       class_="field")

    def __new_project(self):
        all_projects = self.__SmpModel.get_all_projects()

        return tag.div(
                       tag.label(
                       'Project:',
                       tag.br(),
                       tag.select(
                       tag.option(),
                       [tag.option(row[1], value=row[0]) for row in sorted(all_projects, key=itemgetter(1))],
                       name="project")
                       ),
                       class_="field")
                       
    def _do_delete(self, req, version):
        req.perm.require('MILESTONE_DELETE')
        version_name = version.name
        version.delete()

        self.__SmpModel.delete_version_project(version_name)

        add_notice(req, _('The version "%(name)s" has been deleted.',
                          name=version_name))
        req.redirect(req.href.roadmap())

    def _do_save(self, req, db, version):
        version_name = req.args.get('name')
        version_project = req.args.get('project')
        old_version_project = self.__SmpModel.get_id_project_version(version.name)

        if version.exists:
            req.perm.require('MILESTONE_MODIFY')
        else:
            req.perm.require('MILESTONE_CREATE')

        old_name = version.name
        new_name = version_name
        
        version.description = req.args.get('description', '')

        if 'time' in req.args:
            time = req.args.get('time', '')
            version.time = time and parse_date(time, req.tz, 'datetime') or None
        else:
            version.time = None

        # Instead of raising one single error, check all the constraints and
        # let the user fix them by going back to edit mode showing the warnings
        warnings = []
        def warn(msg):
            add_warning(req, msg)
            warnings.append(msg)

        # -- check the name
        # If the name has changed, check that the version doesn't already
        # exist
        # FIXME: the whole .exists business needs to be clarified
        #        (#4130) and should behave like a WikiPage does in
        #        this respect.
        try:
            new_version = Version(self.env, new_name, db)
            if new_version.name == old_name:
                pass        # Creation or no name change
            elif new_version.name:
                warn(_('Version "%(name)s" already exists, please '
                       'choose another name.', name=new_version.name))
            else:
                warn(_('You must provide a name for the version.'))
        except:
            version.name = new_name

        if warnings:
            return self._render_editor(req, db, version)
        
        # -- actually save changes

        if version.exists:
            version.update()

            if old_name != version.name:
                self.__SmpModel.rename_version_project(old_name, version.name)
               
            if not version_project:
                self.__SmpModel.delete_version_project(version.name)
            elif not old_version_project:
                self.__SmpModel.insert_version_project(version.name, version_project)    
            else:
                self.__SmpModel.update_version_project(version.name, version_project)    
        else:
            version.insert()
            if version_project:
                self.__SmpModel.insert_version_project(version.name, version_project)    


        add_notice(req, _('Your changes have been saved.'))
        req.redirect(req.href.version(version.name))

    def _render_confirm(self, req, db, version):
        req.perm.require('MILESTONE_DELETE')

        version = [v for v in Version.select(self.env, db=db)
                      if v.name != version.name
                      and 'MILESTONE_VIEW' in req.perm]
        data = {
            'version': version
        }
        return 'version_delete.html', data, None

    def _render_editor(self, req, db, version):
        # Suggest a default due time of 18:00 in the user's timezone
        default_time = datetime.now(req.tz).replace(hour=18, minute=0, second=0,
                                                   microsecond=0)
        if default_time <= datetime.now(utc):
            default_time += timedelta(days=1)
        
        data = {
            'version': version,
            'datetime_hint': get_datetime_format_hint(),
            'default_time': default_time
        }

        if version.exists:
            req.perm.require('MILESTONE_MODIFY')
            versions = [v for v in Version.select(self.env, db=db)
                          if v.name != version.name
                          and 'MILESTONE_VIEW' in req.perm]
        else:
            req.perm.require('MILESTONE_CREATE')

        Chrome(self.env).add_wiki_toolbars(req)
        return 'version_edit.html', data, None

    def _render_view(self, req, db, version):
        version_groups = []
        available_groups = []
        component_group_available = False
        ticket_fields = TicketSystem(self.env).get_ticket_fields()

        # collect fields that can be used for grouping
        for field in ticket_fields:
            if field['type'] == 'select' and field['name'] != 'version' \
                    or field['name'] in ('owner', 'reporter'):
                available_groups.append({'name': field['name'],
                                         'label': field['label']})
                if field['name'] == 'component':
                    component_group_available = True

        # determine the field currently used for grouping
        by = None
        if component_group_available:
            by = 'component'
        elif available_groups:
            by = available_groups[0]['name']
        by = req.args.get('by', by)

        tickets = get_tickets_for_any(self.env, db, 'version', version.name, by)
        tickets = apply_ticket_permissions(self.env, req, tickets)
        stat = get_ticket_stats(self.stats_provider, tickets)

        context = Context.from_request(req)
        data = {
            'context': context,
            'version': version,
            'attachments': AttachmentModule(self.env).attachment_data(context),
            'available_groups': available_groups, 
            'grouped_by': by,
            'groups': version_groups
            }
        data.update(any_stats_data(self.env, req, stat, 'version', version.name))

        if by:
            groups = []
            for field in ticket_fields:
                if field['name'] == by:
                    if 'options' in field:
                        groups = field['options']
                        if field.get('optional'):
                            groups.insert(0, '')
                    else:
                        cursor = db.cursor()
                        cursor.execute("""
                            SELECT DISTINCT COALESCE(%s,'') FROM ticket
                            ORDER BY COALESCE(%s,'')
                            """ % (by, by))
                        groups = [row[0] for row in cursor]

            max_count = 0
            group_stats = []

            for group in groups:
                values = group and (group,) or (None, group)
                group_tickets = [t for t in tickets if t[by] in values]
                if not group_tickets:
                    continue

                gstat = get_ticket_stats(self.stats_provider, group_tickets)
                if gstat.count > max_count:
                    max_count = gstat.count

                group_stats.append(gstat) 

                gs_dict = {'name': group}
                gs_dict.update(any_stats_data(self.env, req, gstat,
                                                    'version', version.name, by, group))
                version_groups.append(gs_dict)

            for idx, gstat in enumerate(group_stats):
                gs_dict = version_groups[idx]
                percent = 1.0
                if max_count:
                    percent = float(gstat.count) / float(max_count) * 100
                gs_dict['percent_of_max_total'] = percent

        add_stylesheet(req, 'common/css/roadmap.css')
        add_script(req, 'common/js/folding.js')
        return 'version_view.html', data, None

    def _versions_and_stats(self, req, filter_projects):
        req.perm.require('MILESTONE_VIEW')
        db = self.env.get_db_cnx()
        
        versions = Version.select(self.env, db)
    
        filtered_versions = []
        stats = []
    
        for version in versions:
            project = self.__SmpModel.get_project_version(version.name)
            
            if not filter_projects or (project and project[0] in filter_projects):
                filtered_versions.append(version)
                tickets = get_tickets_for_any(self.env, db, 'version', version.name,
                                                    'owner')
                tickets = apply_ticket_permissions(self.env, req, tickets)
                stat = get_ticket_stats(self.stats_provider, tickets)
                stats.append(any_stats_data(self.env, req, stat,
                                                  'version', version.name))
    
        return filtered_versions, stats

