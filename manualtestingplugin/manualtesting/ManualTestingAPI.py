# ManualTesting.ManualTestingAPI

import time
from trac.core import *
from manualtesting.DBUtils import *

class ManualTestingAPI:
    def __init__(self, component):
        self.env = component.env
        self.log = component.log
        self.dbUtils = DBUtils(self)

    # Main request processing function
    def renderUI(self, req, cursor):
        # Get request mode
        suite_id, plan_id = self.parseRequest(req, cursor)
        modes = self.getModes(req, suite_id, plan_id)
        # Perform actions
        template = self.performAction(req, cursor, modes, suite_id, plan_id)
        return template, None

    def parseRequest(self, req, cursor):
        suite_id = None
        plan_id = None

        # Populate active suite
        if req.args.has_key('suite'):
            suite_id = int(req.args.get('suite') or 0)

        # Populate active plan
        if req.args.has_key('plan'):
            plan_id = int(req.args.get('plan') or 0)

        self.log.debug('suite_id: %s' % suite_id)
        self.log.debug('plan_id: %s' % plan_id)
        return suite_id, plan_id

    def getModes(self, req, suite_id, plan_id):
        # Get action
        component = req.args.get('component')
        action = req.args.get('manualtesting_action')
        preview = req.args.has_key('preview');
        submit = req.args.has_key('submit');
        self.log.debug('component: %s' % component)
        self.log.debug('action: %s' % action)

        if component == 'admin':
            req.hdf['discussion.href'] = req.href.admin('discussion')
        elif component == 'wiki':
            req.hdf['discussion.href'] = req.href(req.path_info)
        else:
            req.hdf['manualtesting.href'] = req.href.testing()

        req.hdf['discussion.component'] = component

        # Determine mode
        if plan_id:
            pass
        elif suite_id:
            if action == 'add':
                return ['plan-add-form']
            elif action == 'plan-add':
                return ['plan-add-submit', 'suite-view']
            elif action == 'delete':
                return ['suite-delete', 'suite-view']
            else:
                return ['suite-view']
        else:
            return ['main']

    def performAction(self, req, cursor, modes, suite_id, plan_id):
        for mode in modes:
            self.log.debug('doing %s mode action' % (mode,))
            if mode == 'main':
                # Display the main page (a listing of available suites.)
                suites = self.dbUtils.get_suites(cursor)
                req.hdf['manualtesting.suites'] = suites
                return 'suites.cs'

            elif mode == 'plan-add-form':
                suite = self.dbUtils.get_suite(cursor, suite_id)
                req.hdf['manualtesting.suite'] = suite
                # Get form values.
                new_title = req.args.get('title')
                new_description = req.args.get('description')
                new_priority = req.args.get('priority')
                # Display pupulated form (if data is available)
                if new_title:
                    req.hdf['manualtesting.title'] = wiki_to_oneliner(new_title, self.env)
                if new_priority:
                    req.hdf['manualtesting.priority'] = wiki_to_oneliner(new_priority, self.env)
                if new_description:
                    req.hdf['manualtesting.description'] = wiki_to_html(new_description, self.env, req)
                # Return template
                return 'plan-add.cs'

            elif mode == 'plan-add-submit':
                # Get form values.
                new_user = req.args.get('user')
                new_title = req.args.get('title')
                new_priority = req.args.get('priority')
                new_description = req.args.get('description')
                new_time = int( time.time() )
                # Add plan.
                self.log.debug(new_description)
                self.dbUtils.add_plan(cursor,suite_id,new_user,new_title,new_priority,new_description,new_time)

            elif mode == 'suite-view':
                # Display the plans in a suite.
                suite = self.dbUtils.get_suite(cursor, suite_id)
                plans = self.dbUtils.get_plans(req, cursor, suite_id)
                req.hdf['manualtesting.suite'] = suite
                req.hdf['manualtesting.plans'] = plans
                return 'suite.cs'