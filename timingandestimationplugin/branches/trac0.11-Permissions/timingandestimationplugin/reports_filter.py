from trac.web.api import ITemplateStreamFilter
from trac.core import *
from genshi.core import *
from genshi.builder import tag
try: 
    set 
except NameError: 
    from sets import Set as set     # Python 2.3 fallback 

from genshi.filters.transform import Transformer
import re

from trac.ticket.report import ReportModule
from trac.util.datefmt import format_datetime, format_time
import csv
from trac.web.api import RequestDone

billing_report_regex = re.compile("\{(?P<reportid>\d*)\}")
def report_id_from_text(text):
    m = billing_report_regex.match(text)
    if m:
        return int(m.groupdict()["reportid"])

def get_billing_reports(comp):
    cur = comp.env.get_db_cnx().cursor()
    try:
        cur.execute("SELECT id FROM custom_report")
        return set([x[0] for x in cur.fetchall()])
    except Exception, e:
        # if we can't get the billing reports (e.g. the
        # TimingAndEstimationPlugin isn't installed), silently continue
        # without hiding anything.
        return set()

class RowFilter(object):
    """A genshi filter that operates on table rows, completely hiding any that
    are in the billing_reports table."""

    def __init__(self, comp):
        self.component = comp
        self.billing_reports = get_billing_reports(comp)
        self.component.log.debug('self.billing_reports= %r' % self.billing_reports)

    def __call__(self, row_stream):
        events = list(row_stream)
        report_url = Stream(events) \
                        .select('td[@class="report"]/a/@href').render()
        id = int(report_url.split('/')[-1])

        if not id in self.billing_reports:
            for kind,data,pos in Stream(events):
                yield kind,data,pos

class ReportsFilter(Component):
    """Remove all billing reports from the reports list."""
    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        if not filename == 'report_view.html':
            return stream
        self.log.debug("Applying Reports Filter to remove T&E reports")
        return stream | Transformer(
            '//table[@class="listing reports"]/tbody/tr'
            ).filter(RowFilter(self))

class ReportScreenFilter(Component):
    """Hides TandE reports even when you just go to the url"""
    implements(ITemplateStreamFilter)
    def __init__(self):
        self.billing_reports = get_billing_reports(self)
        self.log.debug('ReportScreenFilter: self.billing_reports= %r' % self.billing_reports)

    def filter_stream(self, req, method, filename, stream, data):
        if not filename == 'report_view.html':
            return stream
        reportid = [None]

        def idhelper(strm):
            header = strm[0][1]
            if not reportid[0]:
                self.log.debug("ReportScreenFilter: helper: %s %s %s"%(strm,header,report_id_from_text(header)))
                reportid[0] = report_id_from_text(header) 
            for kind, data, pos in strm:
                yield kind, data, pos       
                
        def permhelper(strm):
            id = reportid[0]
            self.log.debug("ReportScreenFilter: id:%s, in bill: %s   has perm:%s" % (id, id in self.billing_reports, req.perm.has_permission("TIME_VIEW")))
            if id and id in self.billing_reports and not req.perm.has_permission("TIME_VIEW"):
                self.log.debug("ReportScreenFilter: No time view, prevent render")
                msg = "YOU MUST HAVE TIME_VIEW PERMSSIONS TO VIEW THIS REPORT"
                for kind, data, pos in tag.span(msg).generate():
                    yield kind, data, pos
            else:
                for kind, data, pos in strm:
                    yield kind, data, pos

        self.log.debug("ReportScreenFilter: About to prevent rendering of billing reports without permissions")
        stream = stream | Transformer('//div[@id="content"]/h1/text()').filter(idhelper)
        stream = stream | Transformer('//div[@id="content"]').filter(permhelper)
        return stream

## ENFORCE PERMISSIONS ON report exports

billing_report_fname_regex = re.compile("report_(?P<reportid>\d*)")
def report_id_from_filename(text):
    if text:
        m = billing_report_fname_regex.match(text)
        if m:
            return int(m.groupdict()["reportid"])
    return -1;


def _send_csv(self, req, cols, rows, sep=',', mimetype='text/plain',
              filename=None):
    req.send_response(200)
    req.send_header('Content-Type', mimetype + ';charset=utf-8')
    if filename:
        req.send_header('Content-Disposition', 'filename=' + filename)
    req.end_headers()
    
    id = report_id_from_filename(filename)
    reports = get_billing_reports(self)
    if id in reports and not req.perm.has_permission("TIME_VIEW"):
        raise RequestDone
    
    def iso_time(t):
        return format_time(t, 'iso8601')

    def iso_datetime(dt):
        return format_datetime(dt, 'iso8601')

    col_conversions = {
        'time': iso_time,
        'datetime': iso_datetime,
        'changetime': iso_datetime,
        'date': iso_datetime,
        'created': iso_datetime,
        'modified': iso_datetime,
        }
    
    converters = [col_conversions.get(c.strip('_'), unicode) for c in cols]
    
    writer = csv.writer(req, delimiter=sep)
    writer.writerow([unicode(c).encode('utf-8') for c in cols])
    for row in rows:
        row = list(row)
        for i in xrange(len(row)):
            row[i] = converters[i](row[i]).encode('utf-8')
        writer.writerow(row)

    raise RequestDone

ReportModule._send_csv = _send_csv
