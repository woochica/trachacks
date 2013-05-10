# Copyright (C) 2006 Sam Bloomquist <spooninator@hotmail.com>
# Copyright (C) 2006-2008 Daan van Etten <daan@stuq.nl>
# All rights reserved.

# This software may at some point consist of voluntary contributions made by
# many individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Sam Bloomquist <spooninator@hotmail.com>
# Author: Daan van Etten <daan@stuq.nl>

import time
import sys

from trac import __version__ as trac_version
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.ticket import ITicketChangeListener
from trac.util import Markup, format_date
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_script, add_stylesheet
)
from trac.web.main import IRequestHandler

import dbhelper


class BurndownComponent(Component):
    implements(IEnvironmentSetupParticipant, INavigationContributor,
               IRequestHandler, ITemplateProvider, IPermissionRequestor,
               ITicketChangeListener)

    tracversion = trac_version[:4]

    ### IEnvironmentSetupParticipant methods

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        if not db:
            db = self.env.get_db_cnx()

        needsUpgrade = True

        # See if the burndown table exists, if not, we need an upgrade
        if dbhelper.table_exists(db, "burndown"):
            needsUpgrade = False
            if dbhelper.table_field_exists(db, "burndown", "week"):
                needsUpgrade = True

        if dbhelper.table_field_exists(db, "milestone", "started"):
            needsUpgrade = False

        return needsUpgrade

    def upgrade_environment(self, db):
        db = self.env.get_db_cnx()

        needsCreate = True
        needsUpgrade_milestone = True
        needsUpgrade_burndown = False

        if dbhelper.table_exists(db, "burndown"):
            needsCreate = False
            if dbhelper.table_field_exists(db, "burndown", "week"):
                needsUpgrade_burndown = True

        if dbhelper.table_field_exists(db, "milestone", "started"):
            needsUpgrade_milestone = False

        if needsCreate:
            print >> sys.stderr, 'Attempting to create the burndown table'
            dbhelper.create_burndown_table(db, self.env)

        if needsUpgrade_milestone:
            print >> sys.stderr, 'Attempting to modify the milestone table'
            dbhelper.upgrade_milestone_table(db, self.env)

        if needsUpgrade_burndown:
            print >> sys.stderr, 'Attempting to modify the burndown table'
            dbhelper.upgrade_burndown_table(db, self.env)

        db.commit()

    ### ITicketChangeListener methods

    def ticket_created(self, ticket):
        self.log.debug('burndown plugin - ticket_created')
        self.update_burndown_data()

    def ticket_changed(self, ticket, comment, author, old_values):
        self.log.debug('burndown plugin - ticket_changed')
        self.update_burndown_data()

    def ticket_deleted(self, ticket):
        self.log.debug('burndown plugin - ticket_modified')
        self.update_burndown_data()

    ### INavigationContributor methods

    def get_active_navigation_item(self, req):
        return "burndown"

    def get_navigation_items(self, req):
        if req.perm.has_permission("BURNDOWN_VIEW"):
            if self.tracversion == "0.10":
                yield 'mainnav', 'burndown', Markup(
                    '<a href="%s">Burndown</a>') % req.href.burndown()
            else:
                yield 'mainnav', 'burndown', Markup(
                    '<a href="%s">Burndown</a>' % req.href.burndown())

    ### IPermissionRequestor methods

    def get_permission_actions(self):
        return ["BURNDOWN_VIEW", "BURNDOWN_ADMIN"]

    ### IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/burndown'

    def process_request(self, req):
        req.perm.assert_permission('BURNDOWN_VIEW')

        db = self.env.get_db_cnx()

        milestones = dbhelper.get_milestones(db)
        components = dbhelper.get_components(db)

        selected_milestone = None
        if len(milestones) > 0:
            selected_milestone = dbhelper.get_current_milestone(
                db, req.args.get('selected_milestone', ''))

        selected_component = req.args.get('selected_component',
                                          'All Components')

        empty_db_for_testing = req.args.get('empty_db_for_testing', 'false')
        if empty_db_for_testing == "true":
            req.perm.assert_permission('TRAC_ADMIN')
            dbhelper.empty_db_for_testing(db)

        # expose display data to the templates
        data = {}
        data['milestones'] = req.hdf['milestones'] = milestones
        data['components'] = req.hdf['components'] = components
        data['selected_milestone'] = req.hdf[
            'selected_milestone'] = selected_milestone
        data['selected_component'] = req.hdf[
            'selected_component'] = selected_component
        data['draw_graph'] = req.hdf['draw_graph'] = False
        data['start'] = req.hdf['start'] = False

        if req.perm.has_permission("BURNDOWN_ADMIN"):
            data['start'] = req.hdf['start'] = True

        if 'start' in req.args:
            self.start_milestone(db, selected_milestone['name'])

        data['draw_graph'] = req.hdf['draw_graph'] = True
        self.update_burndown_data()

        data['burndown_data'] = req.hdf['burndown_data'] = \
            self.get_burndown_data(db, selected_milestone, components,
                                   selected_component)

        add_stylesheet(req, 'hw/css/burndown.css')

        self.update_burndown_data()

        if self.tracversion == "0.10":
            add_script(req, 'hw/js/line.js')
            add_script(req, 'hw/js/wz_jsgraphics.js')
            return 'burndown.cs', None
        else:
            data['library'] = ''
            if data['library'] == 'flot':
                add_script(req, 'hw/js/jquery.flot.js')
            else:
                add_script(req, 'hw/js/line.js')
                add_script(req, 'hw/js/wz_jsgraphics.js')

            return 'burndown.html', data, None

    def get_burndown_data(self, db, selected_milestone, components,
                          selected_component):
        cursor = db.cursor()

        if not selected_milestone:
            raise TracError(
                "No milestones defined, please create at least one milestone.")

        # this will be a dictionary of lists of tuples --
        # e.g. component_data = {'componentName':[(id, hours_remaining), ...
        component_data = {}
        for comp in components:
            if selected_component == 'All Components' or \
                    comp['name'] == selected_component:
                self.log.debug("comp = %s", comp['name'])
                self.log.debug("selected_component = %s", selected_component)
                cursor.execute("""
                    SELECT id, hours_remaining
                    FROM burndown
                    WHERE milestone_name = %s AND component_name = %s
                    ORDER BY id""", (selected_milestone['name'], comp['name']))
                component_data[comp['name']] = cursor.fetchall()
                self.log.debug(component_data[comp['name']])

        if len(component_data) > 0 and component_data[component_data.keys()[0]]:
            burndown_length = len(component_data[component_data.keys()[0]])
        else:
            burndown_length = 0
        burndown_data = []
        if selected_component == 'All Components':
            for time_unit in range(0, burndown_length):
                sumHours = 0
                for comp in components:
                    self.log.debug('component: %s', [comp['name']])
                    self.log.debug('time_unit: %s', [time_unit])
                    if (component_data[comp['name']] and len(
                            component_data[comp['name']]) > time_unit):
                        self.log.debug(
                            'hours: %s',
                            component_data[comp['name']][time_unit][1])
                        sumHours += component_data[comp['name']][time_unit][1]

                burndown_data.append((time_unit + 1, sumHours))

        else:
            for time_unit in range(0, len(component_data[selected_component])):
                burndown_data.append((time_unit + 1,
                                      component_data[selected_component][
                                          time_unit][1]))

        return burndown_data

    def start_milestone(self, db, milestone):
        start_date = dbhelper.get_startdate_for_milestone(db, milestone)

        if start_date is not None:
            raise TracError("Milestone %s was already started." % milestone)

        dbhelper.set_startdate_for_milestone(db, milestone, int(time.time()))

    ### ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename

        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename

        return [('hw', resource_filename(__name__, 'htdocs'))]

    #------------------------------------------------------------------------
    # update_burndown_data
    #  - add up the hours remaining for the open tickets for each open
    #    milestone and put the sums into the burndown table
    #------------------------------------------------------------------------
    def update_burndown_data(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # today's date
        today = format_date(int(time.time()))

        milestones = dbhelper.get_milestones(db)
        components = dbhelper.get_components(db)

        for mile in milestones:
            if mile['started'] and not mile['completed']:
                for comp in components:
                    cursor.execute("""
                        SELECT est.value AS estimate, ts.value AS spent
                        FROM ticket t
                        LEFT OUTER JOIN ticket_custom est
                          ON (t.id = est.ticket AND est.name = 'estimatedhours')
                        LEFT OUTER JOIN ticket_custom ts
                          ON (t.id = ts.ticket AND ts.name = 'totalhours')
                        WHERE t.component = %s AND t.milestone = %s
                          AND status IN ('new', 'assigned', 'reopened',
                            'accepted')""", (comp['name'], mile['name']))

                    rows = cursor.fetchall()
                    hours = 0
                    if rows:
                        for estimate, spent in rows:
                            if not estimate:
                                estimate = 0
                            if not spent:
                                spent = 0

                            if (float(estimate) - float(spent)) > 0:
                                hours += float(estimate) - float(spent)

                    cursor.execute("""
                        SELECT id FROM burndown
                        WHERE date = %s AND milestone_name = %s
                        AND component_name = %s
                        """, (today, mile['name'], comp['name']))

                    row = cursor.fetchone()

                    try:
                        if row:
                            cursor.execute("""
                                UPDATE burndown SET hours_remaining = %s
                                WHERE date = %s AND milestone_name = %s
                                AND component_name = %s
                                """, (hours, today, mile['name'], comp['name']))
                        else:
                            cursor.execute("""
                                INSERT INTO burndown(component_name,
                                  milestone_name, date, hours_remaining)
                                VALUES(%s,%s,%s,%s)
                                """, (comp['name'], mile['name'], today, hours))
                    except Exception, inst:
                        self.log.debug(type(inst))
                        self.log.debug(inst.args)
                        self.log.debug(inst)
                        cursor.connection.rollback()
                    else:
                        db.commit()
