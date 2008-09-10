from trac.web.api import ITemplateStreamFilter
from trac.core import *
from genshi.core import *
from genshi.builder import tag
from sets import Set as set
from genshi.filters.transform import Transformer

class RowFilter(object):
    """A genshi filter that operates on table rows, completely hiding any that
    are in the billing_reports table."""

    def __init__(self, comp):
        self.component = comp
        cur = comp.env.get_db_cnx().cursor()
        try:
            cur.execute("SELECT id FROM custom_report")
            self.billing_reports = set([x[0] for x in cur.fetchall()])
        except Exception, e:
            # if we can't get the billing reports (e.g. the
            # TimingAndEstimationPlugin isn't installed), silently continue
            # without hiding anything.
            self.billing_reports = set()
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
