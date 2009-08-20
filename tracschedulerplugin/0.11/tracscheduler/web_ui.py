# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The Trac Scheduler Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

from trac.core import *
from trac.db import DatabaseManager
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.chrome import *
from trac.perm import IPermissionRequestor
from trac.web.api import RequestDone

from trac.ticket import Milestone, Ticket, TicketSystem, ITicketManipulator

from trac.admin import IAdminPanelProvider

from pkg_resources import resource_filename

import os
import time
from threading import Thread, Lock

from model import schema, schema_version, TracScheduler_List

__all__ = ['TracSchedulerModule', 'IScheduledTask']

class IScheduledTask(Interface):
    """
    Extension point interface for adding scheduled tasks to the scheduler module.
    """
    def process_scheduled_task(self, parent):
        """ process scheduled task
        """

class TaskWorker(Thread):
    def __init__(self, parent, task):
        Thread.__init__(self)
        self.parent = parent
        self.task = task

    def run(self):
        self.task(self.parent)

class Scheduler(Thread):
    def __init__(self, parent, poll_interval, worker_interval):
        Thread.__init__(self)
        self.parent = parent
        self.poll_interval = poll_interval
        self.worker_interval = worker_interval

    def run(self):
        while True:
            # check tasks
            for scheduled_task in self.parent.scheduled_tasks:
                task_worker = TaskWorker(self.parent, scheduled_task.process_scheduled_task)
                task_worker.setDaemon(True)
                task_worker.start()
                time.sleep(self.worker_interval)

            time.sleep(self.poll_interval)

class TracSchedulerModule(Component):

    scheduled_tasks = ExtensionPoint(IScheduledTask)

    implements(
               ITemplateProvider,
               IPermissionRequestor,
               )

    def __init__(self):
        self.db_lock = Lock()

        poll_interval = self.config.getint("tracscheduler", "poll_interval", 60)
        worker_interval = self.config.getint("tracscheduler", "worker_interval", 1)
        if poll_interval < 1:
            poll_interval = 1
        if worker_interval < 1:
            worker_interval = 1
        if poll_interval < worker_interval + 1:
            poll_interval = worker_interval + 1

        self.scheduler = Scheduler(self, poll_interval, worker_interval)
        self.scheduler.setDaemon(True)
        self.scheduler.start()

    def queryDb(self, sqlString, params = [], commit = False):
        """ public method for threaded tasks to access trac db
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        self.db_lock.acquire()
        try:
            cursor.execute(sqlString, params)
            if commit:
                db.commit()
            else:
                return cursor.fetchall()
        finally:
            self.db_lock.release()

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TS_VIEW', 'TS_ADMIN', ]
        return actions

    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ts', resource_filename(__name__, 'htdocs'))]


    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        self.env.log.info('get_admin_pages')

        if 'TS_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'ts_admin', 'TracScheduler Admin')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TS_ADMIN')

        data = {'subdata':[1], }
        req.hdf['data'] = data

        return 'ts_admin.html', data

    # internal methods

class TracSchedulerTest(Component):
    implements( IScheduledTask)
    def process_scheduled_task(self, parent):
        print "TracSchedulerTest"
        #sqlString = "SELECT id FROM ticket ORDER BY id LIMIT 2;"
        #rows = parent.queryDb(sqlString)
        #print rows

