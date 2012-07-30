# -*- coding: utf-8 -*-

import re
from StringIO import StringIO
import codecs
import csv
from util import *
from time import time
from datetime import tzinfo, timedelta, datetime
from usermanual import *
from manager import WorkLogManager
from trac.log import logger_factory
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler, IRequestFilter
from trac.util.datefmt import format_date, format_time
from trac.util import Markup
from trac.ticket import Ticket
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href
from trac.wiki.formatter import wiki_to_html
from trac.util.text import CRLF

class WorkLogPage(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler, ITemplateProvider)

    def __init__(self):
        pass

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['WORK_LOG', ('WORK_VIEW', ['WORK_LOG']), ('WORK_ADMIN', ['WORK_VIEW'])]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'worklog'

    def get_navigation_items(self, req):
        url = req.href.worklog()
        if req.perm.has_permission("WORK_VIEW"):
            yield 'mainnav', "worklog", \
                  Markup('<a href="%s">%s</a>' % \
                         (url , "Work Log"))

    # Internal Methods
    def worklog_csv(self, req, log):
      #req.send_header('Content-Type', 'text/plain')
      req.send_header('Content-Type', 'text/csv;charset=utf-8')
      req.send_header('Content-Disposition', 'filename=worklog.csv')
      
      # Headers
      fields = ['user',
                'name',
                'starttime',
                'endtime',
                'ticket',
                'summary',
                'comment']
      sep=','

      content = StringIO()
      writer = csv.writer(content, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
      writer.writerow([unicode(c).encode('utf-8') for c in fields])

      # Rows
      for row in log:
        values=[]
        for field in fields:
          values.append(unicode(row[field]).encode('utf-8'))
        writer.writerow(values)

      req.send_header('Content-Length', content.len)
      req.write(content.getvalue())
    
    # IRequestHandler methods
    def match_request(self, req):
        if re.search('^/worklog', req.path_info):
            return True
        return None

    def process_request(self, req):
        req.perm.require('WORK_VIEW')
        
        messages = []

        def addMessage(s):
            messages.extend([s]);

        # General protection (not strictly needed if Trac behaves itself)
        if not re.search('/worklog', req.path_info):
            return None
        
        add_stylesheet(req, "worklog/worklogplugin.css")

        # Specific pages:
        match = re.search('/worklog/users/(.*)', req.path_info)
        if match:
          mgr = WorkLogManager(self.env, self.config, match.group(1))
          if req.args.has_key('format') and req.args['format'] == 'csv':
            self.worklog_csv(req, mgr.get_work_log('user'))
            return None
          
          data = {"worklog": mgr.get_work_log('user'),
                  "ticket_href": req.href.ticket(),
                  "usermanual_href":req.href.wiki(user_manual_wiki_title),
                  "usermanual_title":user_manual_title
                  }
          return 'worklog_user.html', data, None

        match = re.search('/worklog/stop/([0-9]+)', req.path_info)
        if match:
          ticket = match.group(1)
          data = {'worklog_href': req.href.worklog(),
                  'ticket_href':  req.href.ticket(ticket),
                  'ticket':       ticket,
                  'action':       'stop',
                  'label':        'Stop Work'}
          xhr = req.get_header('X-Requested-With') == 'XMLHttpRequest'
          if xhr:
              data['xhr'] = True
          return 'worklog_stop.html', data, None
        
        mgr = WorkLogManager(self.env, self.config, req.authname)
        if req.args.has_key('format') and req.args['format'] == 'csv':
            self.worklog_csv(req, mgr.get_work_log())
            return None
        
        # Not any specific page, so process POST actions here.
        if req.method == 'POST':
            if req.args.has_key('startwork') and req.args.has_key('ticket'):
                if not mgr.start_work(req.args['ticket']):
                    addMessage(mgr.get_explanation())
                else:
                    addMessage('You are now working on ticket #%s.' % (req.args['ticket'],))
                
                req.redirect(req.args['source_url'])
                return None
                
            elif req.args.has_key('stopwork'):
                stoptime = None
                if req.args.has_key('stoptime') and req.args['stoptime']:
                    stoptime = int(req.args['stoptime'])

                comment = ''
                if req.args.has_key('comment'):
                    comment = req.args['comment']

                if not mgr.stop_work(stoptime, comment):
                    addMessage(mgr.get_explanation())
                else:
                    addMessage('You have stopped working.')
                
                req.redirect(req.args['source_url'])
                return None
        
        # no POST, so they're just wanting a list of the worklog entries
        data = {"messages": messages,
                "worklog": mgr.get_work_log('summary'),
                "worklog_href": req.href.worklog(),
                "ticket_href": req.href.ticket(),
                "usermanual_href": req.href.wiki(user_manual_wiki_title),
                "usermanual_title": user_manual_title
                }
        return 'worklog.html', data, None
        
        
    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('worklog', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
