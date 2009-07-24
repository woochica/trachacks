"""
plugin fro Trac 0.11 to provide iCalendar ouput for ticket's queries
author : Xavier Pechoultes <x.pechoultres@clariprint.com>
Licence: GPL
"""

#import re

#from ical import iCal

import os
import sys
from trac.core import *
from trac.util.translation import _
from trac.web import IRequestFilter
from trac.web import IRequestHandler
from trac.web.chrome import add_link
from trac.ticket.query import QueryModule
from trac.mimeview.api import Mimeview, IContentConverter, Context
from trac.web.chrome import add_ctxtnav, add_link, add_script, add_stylesheet, INavigationContributor, Chrome

from cStringIO import StringIO
from trac.resource import Resource, get_resource_url

import datetime
import time

class iCalViewPlugin(QueryModule):
    implements(IRequestHandler, INavigationContributor, 
               IContentConverter)

    def match_request(self, req):
        return req.path_info == '/ical'

    def convert_content(self, req, mimetype, query, key):
        return self.export_ical(req, query)

    def get_supported_conversions(self):
        yield ('ical', _('iCalendar'), 'ics',
               'trac.ticket.Query', 'text/calendar', 8)

    def convert_content(self, req, mimetype, query, key):
        if key == 'ical':
            return self.export_ical(req, query)
    
    def get_active_navigation_item(self, req):
        return 'icalendar'

    def export_ical(self, req, query):        
        dtstart_key = self.config['icalendar'].get('dtstart','date_start')
        duration_key = self.config['icalendar'].get('duration','duration')
        input_date_format = self.config['icalendar'].get('input_date_format','duration')
        if dtstart_key not in query.cols:
            query.cols.append(dtstart_key)
        if duration_key not in query.cols:
            query.cols.append(duration_key)

        if 'description' not in query.cols:
            query.cols.append('description')
        if 'changetime' not in query.cols:
            query.cols.append('changetime')
        if 'time' not in query.cols:
            query.cols.append('time')
        query.max = sys.maxint
        results = query.execute(req)
        cols = query.get_columns()
        content = StringIO()
        content.write('BEGIN:VCALENDAR\r\n')
        content.write('VERSION:2.0\r\n')
        content.write('PRODID:2.0:-//Edgewall Software//NONSGML Trac 0.11//EN\r\n')
        content.write('METHOD:PUBLISH\r\n')
        content.write('X-WR-CALNAME: test\r\n')

        attr_map = {
                    "summary" : "SUMMARY",
                    "type" :  "CATEGORIES"
                   }

        for result in results:
            ticket = Resource('ticket', result['id'])
            if 'TICKET_VIEW' in req.perm(ticket):
                kind = "VEVENT"
                if result["date_start"] in ['--', '' ] :
                    kind = "VTODO"
                content.write("BEGIN:%s\r\n" % kind)
                content.write("UID:</cgi-bin/trac.cgi/ticket/%d@trac.clariprint.com\r\n" % result["id"])
                dtstart = result[dtstart_key]
                if not dtstart in [ '--', '' ] :
                    d = dtstart.split('.')
                    if len(d) == 3:
                        content.write("DTSTART;VALUE=DATE:%s%s%s\r\n" % (d[2],d[1],d[0]))
                        n_days = 1
                        if result[duration_key] != '--':
                            n_days = int(result[duration_key])
                        end_date = datetime.date(int(d[2]),int(d[1]),int(d[0]) + n_days)
                        content.write("DTEND;VALUE=DATE:%s\r\n" % end_date.strftime("%Y%m%d"))
                content.write("CREATED:%s\r\n" % result["time"].strftime("%Y%m%dT%H%M%S"))
                content.write("DTSTAMP:%s\r\n" % result["changetime"].strftime("%Y%m%dT%H%M%S"))
                protocol = "http"
                if "HTTPS" in os.getenv('SERVER_PROTOCOL') :
                    protocol = "https"
                content.write("URL:%s://%s%s\r\n" % (protocol,os.getenv('SERVER_NAME'),get_resource_url(self.env,ticket,req.href)))
                for key in attr_map:
                   if key in cols:
                       content.write("%s:%s\r\n" % (attr_map[key], unicode(result[key]).encode('utf-8')))
                content.write("END:%s\r\n" % kind)
        content.write('END:VCALENDAR\r\n')
        return content.getvalue(), 'text/calendar;charset=utf-8'

